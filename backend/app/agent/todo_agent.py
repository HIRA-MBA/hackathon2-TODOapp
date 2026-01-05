"""Todo Agent configuration using OpenAI Agents SDK.

Per constitution: AI Orchestration uses OpenAI Agents SDK.
Per research Decision 7: Use @function_tool decorator with custom UserContext.
Per research Decision 10: Model selection - gpt-4o-mini for cost-optimization.
"""

from agents import Agent

from app.agent.context import UserContext
from app.tools.task_tools import (
    add_task,
    list_tasks,
    update_task,
    complete_task,
    delete_task,
)


# Base instructions for the agent (task context is added dynamically)
AGENT_INSTRUCTIONS = """You are a helpful task management assistant. You help users manage their todo list through natural conversation.

Your job is to understand what the user wants to do with their tasks and use the appropriate tools to help them. You have access to the user's current tasks in the system prompt.

Be conversational, concise, and helpful. When in doubt, ask for clarification rather than making assumptions."""


def create_todo_agent() -> Agent[UserContext]:
    """Create and configure the todo management agent.

    Per research Decision 7: Agent configured with UserContext generic type
    for type-safe context propagation.

    Returns:
        Configured Agent instance with all task management tools.
    """
    return Agent[UserContext](
        name="TodoAssistant",
        instructions=AGENT_INSTRUCTIONS,
        tools=[
            add_task,
            list_tasks,
            update_task,
            complete_task,
            delete_task,
        ],
        model="gpt-4o-mini",
    )


# Singleton agent instance
todo_agent = create_todo_agent()
