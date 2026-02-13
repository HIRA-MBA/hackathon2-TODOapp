"""Chat service for AI chatbot orchestration.

Per spec FR-001: Single chat endpoint for natural language messages.
Per spec FR-002: Load existing conversation from database.
Per spec FR-003: Retrieve relevant tasks and messages for context.
Per spec FR-004: Execute appropriate task operations based on intent.
Per spec FR-005: Persist all assistant responses.
Per spec FR-010: Stateless request handling.
Per spec FR-024: Structured logs with unique request IDs.
Per spec FR-025: Key metrics including latency, AI response time, tool calls.
Per spec FR-027: 30-second timeout for AI service requests.
"""

import asyncio
import logging
import time
import uuid
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from agents import Runner

from app.agent.context import UserContext
from app.agent.prompts import build_system_prompt
from app.agent.todo_agent import todo_agent
from app.models.message import MessageRole
from app.services.conversation_service import ConversationService
from app.services.task_service import TaskService
from app.schemas.chat import ChatStreamEvent, ToolExecution

logger = logging.getLogger(__name__)

# Timeout configuration per FR-027
AI_SERVICE_TIMEOUT_SECONDS = 30


class ChatService:
    """Service for processing chat messages with AI agent.

    Per research Decision 3: Stateless per-request with database-backed
    session reconstruction.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversation_service = ConversationService(db)
        self.task_service = TaskService(db)

    async def process_message(
        self,
        user_id: str,
        email: str | None,
        message: str,
    ) -> AsyncGenerator[ChatStreamEvent, None]:
        """Process a chat message and yield streaming events.

        Per spec FR-001 through FR-005: This method handles the complete
        chat flow from message receipt to response generation.

        Args:
            user_id: Authenticated user's ID from JWT.
            email: User's email from JWT (for logging).
            message: The user's chat message.

        Yields:
            ChatStreamEvent objects for SSE streaming.
        """
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()
        tool_call_count = 0

        logger.info(
            "chat_processing_started",
            extra={
                "request_id": request_id,
                "user_id": user_id,
            },
        )

        try:
            # 1. Get or create conversation
            yield ChatStreamEvent(
                type="thinking", content="Understanding your request..."
            )

            conversation = await self.conversation_service.get_or_create_conversation(
                user_id
            )
            conversation_id = str(conversation.id)
            logger.info(
                "conversation_loaded",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                },
            )

            # 2. Load context (recent messages and tasks)
            recent_messages = await self.conversation_service.get_recent_messages(
                conversation.id, limit=20
            )
            tasks = await self.task_service.list_tasks(user_id)
            # Limit to 20 tasks for context
            tasks = tasks[:20]

            logger.info(
                "context_assembled",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "message_count": len(recent_messages),
                    "task_count": len(tasks),
                },
            )

            # 3. Persist user message
            await self.conversation_service.create_message(
                conversation.id,
                MessageRole.USER,
                message,
            )

            # 4. Build system prompt with task context
            system_prompt = build_system_prompt(tasks)

            # 5. Build conversation history as context string
            history_text = ""
            for msg in recent_messages:
                role_label = (
                    msg.role.upper()
                    if isinstance(msg.role, str)
                    else msg.role.value.upper()
                )
                if role_label in ("USER", "ASSISTANT"):
                    history_text += f"{role_label}: {msg.content}\n"

            # 6. Create user context for tools
            ctx = UserContext(user_id=user_id, email=email, db=self.db)

            # 7. Run the agent
            tool_executions: list[ToolExecution] = []
            response_content = ""
            ai_start_time = time.perf_counter()

            # Build full input with task context and history
            input_parts = []

            # Add task context
            input_parts.append(f"CONTEXT:\n{system_prompt}")

            # Add conversation history if available
            if history_text:
                input_parts.append(f"\nPREVIOUS CONVERSATION:\n{history_text}")

            # Add current message
            input_parts.append(f"\nUSER REQUEST: {message}")

            full_input = "\n".join(input_parts)

            try:
                # Use the agent with streaming and timeout per FR-027
                async with asyncio.timeout(AI_SERVICE_TIMEOUT_SECONDS):
                    result = await Runner.run(
                        starting_agent=todo_agent,
                        input=full_input,
                        context=ctx,
                    )

                # Calculate AI response time
                ai_latency_ms = (time.perf_counter() - ai_start_time) * 1000

                # Process the result
                response_content = result.final_output or ""

                # Extract tool calls from the run
                for item in result.new_items:
                    if hasattr(item, "tool_name") and hasattr(item, "output"):
                        tool_name = item.tool_name
                        tool_output = str(item.output) if item.output else ""

                        # Determine status from output
                        status = (
                            "success" if "success" in tool_output.lower() else "error"
                        )
                        if "info" in tool_output.lower():
                            status = "success"

                        tool_call_count += 1

                        logger.info(
                            "tool_executed",
                            extra={
                                "request_id": request_id,
                                "user_id": user_id,
                                "tool": tool_name,
                                "status": status,
                            },
                        )

                        yield ChatStreamEvent(
                            type="tool_call",
                            tool=tool_name,
                            status="executing",
                        )

                        yield ChatStreamEvent(
                            type="tool_result",
                            tool=tool_name,
                            status=status,
                            result=tool_output,
                        )

                        tool_executions.append(
                            ToolExecution(
                                tool=tool_name,
                                status=status,
                                result=tool_output,
                            )
                        )

                        # Persist tool result as message
                        await self.conversation_service.create_message(
                            conversation.id,
                            MessageRole.TOOL,
                            tool_output,
                            metadata={"tool": tool_name, "status": status},
                        )

            except asyncio.TimeoutError:
                # Per FR-027: 30-second timeout with no automatic retry
                ai_latency_ms = (time.perf_counter() - ai_start_time) * 1000
                logger.warning(
                    "ai_service_timeout",
                    extra={
                        "request_id": request_id,
                        "user_id": user_id,
                        "timeout_seconds": AI_SERVICE_TIMEOUT_SECONDS,
                        "ai_latency_ms": round(ai_latency_ms, 2),
                    },
                )
                response_content = (
                    "I'm sorry, the request took too long to process. "
                    "Please try again with a simpler request."
                )
                yield ChatStreamEvent(
                    type="error",
                    content="Request timed out. Please try again.",
                )

            except Exception as agent_error:
                ai_latency_ms = (time.perf_counter() - ai_start_time) * 1000
                logger.error(
                    "agent_error",
                    extra={
                        "request_id": request_id,
                        "user_id": user_id,
                        "error": str(agent_error),
                        "ai_latency_ms": round(ai_latency_ms, 2),
                    },
                    exc_info=True,
                )
                response_content = "I'm sorry, I encountered an error processing your request. Please try again."
                yield ChatStreamEvent(
                    type="error",
                    content=str(agent_error),
                )

            # 8. Yield the response
            if response_content:
                yield ChatStreamEvent(
                    type="response",
                    content=response_content,
                )

                # Persist assistant response
                await self.conversation_service.create_message(
                    conversation.id,
                    MessageRole.ASSISTANT,
                    response_content,
                )

            # 9. Update conversation activity
            await self.conversation_service.update_conversation_activity(
                conversation.id
            )

            # 10. Signal completion
            yield ChatStreamEvent(
                type="done",
                conversation_id=conversation_id,
            )

            # Calculate total latency
            total_latency_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "chat_processing_completed",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "latency_ms": round(total_latency_ms, 2),
                    "ai_latency_ms": round(ai_latency_ms, 2)
                    if "ai_latency_ms" in dir()
                    else None,
                    "tool_calls": tool_call_count,
                },
            )

        except Exception as e:
            total_latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "chat_processing_failed",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "error": str(e),
                    "latency_ms": round(total_latency_ms, 2),
                },
                exc_info=True,
            )
            yield ChatStreamEvent(
                type="error",
                content=f"An error occurred: {str(e)}",
            )

    async def get_conversation_history(
        self, user_id: str, limit: int = 50
    ) -> tuple[str | None, list[dict]]:
        """Get the user's conversation history.

        Args:
            user_id: Authenticated user's ID.
            limit: Maximum messages to retrieve.

        Returns:
            Tuple of (conversation_id, list of message dicts).
        """
        conversation = await self.conversation_service.get_or_create_conversation(
            user_id
        )
        messages = await self.conversation_service.get_recent_messages(
            conversation.id, limit=limit
        )

        return str(conversation.id), [
            {
                "id": str(msg.id),
                "role": msg.role if isinstance(msg.role, str) else msg.role.value,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ]

    async def clear_history(self, user_id: str) -> int:
        """Clear the user's conversation history.

        Per spec FR-029: System MUST provide a "Clear history" function that
        deletes all messages from the user's conversation while preserving
        the conversation container.

        Args:
            user_id: Authenticated user's ID.

        Returns:
            Number of messages deleted.
        """
        conversation = await self.conversation_service.get_or_create_conversation(
            user_id
        )
        deleted_count = await self.conversation_service.clear_messages(conversation.id)

        logger.info(
            "conversation_history_cleared",
            extra={
                "user_id": user_id,
                "conversation_id": str(conversation.id),
                "messages_deleted": deleted_count,
            },
        )

        return deleted_count
