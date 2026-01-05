# Implementation Plan: AI-Powered Todo Chatbot (Phase 3)

**Branch**: `003-ai-todo-chatbot` | **Date**: 2026-01-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-ai-todo-chatbot/spec.md`

## Summary

Implement an AI-powered chatbot that enables natural language task management through conversation. Users can create, query, update, complete, and delete tasks via chat messages. The system uses OpenAI Agents SDK for natural language understanding, MCP tools for task operations, and RAG patterns to ground responses in user data (tasks and conversation history).

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: FastAPI, OpenAI Agents SDK, SQLModel, SSE-Starlette
**Storage**: Neon PostgreSQL (existing) - add Conversation and Message tables
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server / Windows dev
**Project Type**: Web (frontend + backend monorepo)
**Performance Goals**: <5s task creation, <3s query response (per SC-001, SC-002)
**Constraints**: Stateless per request, 20 message context limit, 20 task context limit
**Scale/Scope**: 100 concurrent chat sessions (per SC-005)

## Constitution Check

*GATE: Must pass before implementation.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Only | ✅ PASS | This plan originates from spec.md |
| II. Clean Architecture | ✅ PASS | AI agents stateless, DB for state, service layer for tools |
| III. Accuracy | ✅ PASS | Acceptance criteria from spec will have tests |
| IV. Reproducibility | ⏳ DEFER | Containerization is Phase 4 scope |

**Technology Stack Compliance:**

| Component | Constitution | Implementation | Status |
|-----------|--------------|----------------|--------|
| Backend Runtime | Python 3.13+ | Python 3.13+ | ✅ |
| Backend Framework | FastAPI | FastAPI | ✅ |
| ORM | SQLModel | SQLModel | ✅ |
| Database | Neon PostgreSQL | Neon PostgreSQL | ✅ |
| AI Orchestration | OpenAI Agents SDK | OpenAI Agents SDK | ✅ |
| AI Tools | MCP SDK | function_tool decorator | ✅ |
| Frontend | Next.js 16+ | Next.js 15 | ✅ |
| Auth | Better Auth JWT | Reuse Phase 2 | ✅ |

## Project Structure

### Documentation (this feature)

```text
specs/003-ai-todo-chatbot/
├── spec.md              # Feature specification (DONE)
├── plan.md              # This file
├── research.md          # Technical research (DONE)
├── checklists/          # Validation checklists (DONE)
└── tasks.md             # Implementation tasks (TODO)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/routes/
│   │   ├── health.py        # [existing] Health check
│   │   ├── tasks.py         # [existing] Task CRUD REST API
│   │   └── chat.py          # [NEW] Chat endpoint with SSE streaming
│   ├── services/
│   │   ├── task_service.py      # [existing] Task CRUD operations
│   │   ├── conversation_service.py  # [NEW] Conversation/Message persistence
│   │   └── chat_service.py      # [NEW] Agent orchestration and context
│   ├── models/
│   │   ├── task.py          # [existing] Task entity
│   │   ├── conversation.py  # [NEW] Conversation entity
│   │   └── message.py       # [NEW] Message entity
│   ├── schemas/
│   │   ├── task.py          # [existing] Task DTOs
│   │   └── chat.py          # [NEW] Chat request/response DTOs
│   ├── tools/
│   │   └── task_tools.py    # [NEW] MCP tools for task operations
│   ├── agent/
│   │   ├── context.py       # [NEW] UserContext dataclass
│   │   ├── prompts.py       # [NEW] System prompts
│   │   └── todo_agent.py    # [NEW] Agent configuration
│   ├── dependencies/
│   │   ├── auth.py          # [existing] JWT validation
│   │   └── database.py      # [existing] DB session
│   ├── config/
│   │   └── settings.py      # [modify] Add OpenAI API key
│   └── main.py              # [modify] Register chat routes
├── alembic/versions/
│   ├── 001_create_task_table.py         # [existing]
│   ├── 002_change_user_id_to_string.py  # [existing]
│   ├── 003_create_conversation_table.py # [NEW]
│   └── 004_create_message_table.py      # [NEW]
└── tests/
    ├── test_chat_endpoint.py    # [NEW] Chat API tests
    ├── test_task_tools.py       # [NEW] MCP tools tests
    └── test_conversation_service.py  # [NEW] Service tests

frontend/
├── src/
│   ├── app/
│   │   ├── (protected)/
│   │   │   ├── dashboard/   # [existing] Task management UI
│   │   │   └── chat/        # [NEW] Chat page
│   │   │       └── page.tsx # [NEW] Chat interface
│   │   └── api/
│   │       └── chat/        # [NEW] Chat API route (proxy to backend)
│   │           └── route.ts # [NEW] SSE proxy
│   ├── components/
│   │   ├── chat/            # [NEW] Chat components
│   │   │   ├── chat-container.tsx   # [NEW] Main chat wrapper
│   │   │   ├── message-list.tsx     # [NEW] Message display
│   │   │   ├── message-item.tsx     # [NEW] Individual message
│   │   │   ├── chat-input.tsx       # [NEW] Input with send button
│   │   │   └── tool-result.tsx      # [NEW] Tool execution display
│   │   └── navbar.tsx       # [modify] Add chat link
│   ├── hooks/
│   │   └── use-chat.ts      # [NEW] Chat state management
│   └── lib/
│       └── chat-api.ts      # [NEW] Chat API client
└── package.json             # [no changes - use existing deps]
```

**Structure Decision**: Extends existing web application structure (Option 2 from template). New chat functionality added as parallel feature to existing task management, sharing auth and database infrastructure.

## Data Model

### Conversation Table

```sql
CREATE TABLE conversation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversation_user_id ON conversation(user_id);
```

### Message Table

```sql
CREATE TABLE message (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_message_conversation_created ON message(conversation_id, created_at);
```

## API Contract

### POST /api/chat

**Request:**
```json
{
  "message": "Add buy groceries to my list"
}
```

**Response (SSE Stream):**
```
data: {"type": "thinking", "content": "Understanding your request..."}

data: {"type": "tool_call", "tool": "add_task", "status": "executing"}

data: {"type": "tool_result", "tool": "add_task", "result": "success - created task 'buy groceries'"}

data: {"type": "response", "content": "I've added 'buy groceries' to your task list."}

data: {"type": "done", "conversation_id": "uuid"}
```

**Response (Non-streaming fallback):**
```json
{
  "response": "I've added 'buy groceries' to your task list.",
  "tool_executions": [
    {
      "tool": "add_task",
      "status": "success",
      "result": "created task 'buy groceries'"
    }
  ],
  "conversation_id": "uuid"
}
```

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Chat Endpoint                            │
│  POST /api/chat (JWT required)                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Context Assembly                            │
│  1. Get/create conversation for user                       │
│  2. Load last 20 messages                                  │
│  3. Load user's tasks (up to 20)                           │
│  4. Build system prompt with task context                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 OpenAI Agent                                │
│  Model: gpt-4o-mini                                        │
│  Tools: add_task, list_tasks, update_task,                 │
│         complete_task, delete_task                         │
│  Context: UserContext(user_id, email, db_session)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 MCP Tools Layer                             │
│  - Receives UserContext via RunContextWrapper              │
│  - Calls TaskService with user_id isolation                │
│  - Returns structured string results                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Message Persistence                         │
│  - Persist user message                                    │
│  - Persist tool results (role='tool')                      │
│  - Persist assistant response                              │
└─────────────────────────────────────────────────────────────┘
```

## MCP Tools Specification

### add_task
```python
@function_tool
async def add_task(
    ctx: RunContextWrapper[UserContext],
    title: str,
    description: str | None = None
) -> str:
    """Add a new task for the user.

    Args:
        title: The task title (required)
        description: Optional task description

    Returns:
        "add_task: success - created task 'title'" or
        "add_task: error - reason"
    """
```

### list_tasks
```python
@function_tool
async def list_tasks(
    ctx: RunContextWrapper[UserContext],
    status: str = "all",
    search: str | None = None
) -> str:
    """List user's tasks with optional filtering.

    Args:
        status: Filter by status - "all", "pending", or "completed"
        search: Optional search term for title matching

    Returns:
        Formatted task list or "No tasks found"
    """
```

### update_task
```python
@function_tool
async def update_task(
    ctx: RunContextWrapper[UserContext],
    task_id: str,
    title: str | None = None,
    description: str | None = None
) -> str:
    """Update an existing task's title or description.

    Args:
        task_id: The task UUID to update
        title: New title (optional)
        description: New description (optional)

    Returns:
        "update_task: success - updated task 'title'" or
        "update_task: error - task not found"
    """
```

### complete_task
```python
@function_tool
async def complete_task(
    ctx: RunContextWrapper[UserContext],
    task_id: str
) -> str:
    """Mark a task as completed.

    Args:
        task_id: The task UUID to complete

    Returns:
        "complete_task: success - marked 'title' as done" or
        "complete_task: error - task not found"
    """
```

### delete_task
```python
@function_tool
async def delete_task(
    ctx: RunContextWrapper[UserContext],
    task_id: str
) -> str:
    """Delete a task.

    Args:
        task_id: The task UUID to delete

    Returns:
        "delete_task: success - deleted task" or
        "delete_task: error - task not found"
    """
```

## System Prompt

```
You are a helpful task management assistant. You help users manage their todo list through natural conversation.

CURRENT USER TASKS:
{formatted_task_list}

CAPABILITIES:
- Add new tasks (ask for clarification if the request is ambiguous)
- List tasks (all, pending, or completed)
- Update task titles or descriptions
- Mark tasks as complete
- Delete tasks

GUIDELINES:
1. Always use the provided tools to modify tasks - never pretend to modify them
2. When referencing tasks, use their ID number for precision
3. If a user's request is ambiguous, ask for clarification
4. Confirm all modifications with a brief summary
5. If a task operation fails, explain the issue clearly
6. Be conversational but concise

RESPONSE FORMAT:
- Keep responses brief and helpful
- Include task details when relevant (ID, title, status)
- Use natural language, not technical jargon
```

## Complexity Tracking

> No constitution violations requiring justification.

| Component | Complexity | Justification |
|-----------|------------|---------------|
| SSE Streaming | Medium | Required for responsive UX per SC-001/SC-002 |
| Conversation Persistence | Low | Simple table design, single conversation per user |
| MCP Tools | Low | Thin wrappers around existing TaskService |
| Agent Config | Low | Standard OpenAI Agents SDK setup |

## Dependencies to Add

### Backend (pyproject.toml)

```toml
dependencies = [
    # ... existing deps ...
    "openai-agents>=0.0.10",       # OpenAI Agents SDK
    "sse-starlette>=2.0.0",        # SSE streaming support
]
```

### Environment Variables

```env
# Add to backend/.env
OPENAI_API_KEY=sk-...  # OpenAI API key for Agents SDK
```

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| AI Response Latency | SSE streaming provides progressive feedback |
| Context Window Overflow | Fixed 20 message + 20 task limits |
| Tool Execution Errors | Tools return error strings for agent interpretation |
| Auth Token Expiry | Existing JWT refresh mechanism from Phase 2 |

## Success Criteria Mapping

| Success Criteria | Implementation |
|-----------------|----------------|
| SC-001: <5s task creation | SSE streaming + gpt-4o-mini |
| SC-002: <3s query response | Indexed queries + context caching |
| SC-003: 95% grounded responses | RAG with task context in system prompt |
| SC-004: Conversation persistence | Database-backed messages |
| SC-005: 100 concurrent sessions | Stateless architecture |
| SC-006: All 5 operations accessible | 5 MCP tools implemented |
| SC-007: Tool metadata in responses | SSE events include tool results |
| SC-008: No cross-user data leakage | user_id from JWT, scoped queries |
