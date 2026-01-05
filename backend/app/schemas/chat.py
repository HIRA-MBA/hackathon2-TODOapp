from pydantic import BaseModel, Field
from typing import Literal


class ChatRequest(BaseModel):
    """Request body for chat endpoint.

    Per spec edge case: Messages are truncated at 2000 characters.
    """

    message: str = Field(..., min_length=1, max_length=2000)


class ToolExecution(BaseModel):
    """Details of a tool execution during chat processing.

    Per spec FR-013: Return tool execution metadata including tool name,
    success/failure status, and result summary.
    """

    tool: str
    status: Literal["success", "error"]
    result: str


class ChatResponse(BaseModel):
    """Response body for non-streaming chat endpoint."""

    response: str
    tool_executions: list[ToolExecution]
    conversation_id: str


class ChatStreamEvent(BaseModel):
    """Server-Sent Event for streaming chat responses.

    Event types:
    - thinking: Agent is processing the request
    - tool_call: Agent is calling a tool
    - tool_result: Tool execution completed
    - response: Final assistant response
    - done: Stream complete
    - error: Error occurred
    """

    type: Literal["thinking", "tool_call", "tool_result", "response", "done", "error"]
    content: str | None = None
    tool: str | None = None
    status: str | None = None
    result: str | None = None
    conversation_id: str | None = None


class MessageResponse(BaseModel):
    """Response schema for a single message in conversation history."""

    id: str
    role: Literal["user", "assistant", "tool"]
    content: str
    created_at: str


class ConversationHistoryResponse(BaseModel):
    """Response body for conversation history endpoint."""

    conversation_id: str
    messages: list[MessageResponse]
