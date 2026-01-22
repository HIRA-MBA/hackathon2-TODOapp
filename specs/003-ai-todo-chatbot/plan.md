# Implementation Plan: AI-Powered Todo Chatbot (Phase 3)

**Branch**: `003-ai-todo-chatbot` | **Date**: 2026-01-04 | **Updated**: 2026-01-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-ai-todo-chatbot/spec.md`

## Summary

Implement an AI-powered chatbot that enables natural language task management through conversation. Users can create, query, update, complete, and delete tasks via chat messages. The system uses **OpenAI ChatKit** for the frontend widget and conversation management, with a **FastMCP HTTP server** exposing task operations as MCP tools that ChatKit's workflow can invoke.

> **Architecture Note (2026-01-22)**: Implementation pivoted from custom SSE/Agent architecture to OpenAI ChatKit for faster delivery and built-in conversation management.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: FastAPI, FastMCP, SQLModel
**Frontend**: OpenAI ChatKit (`@openai/chatkit-react`)
**Storage**: Neon PostgreSQL (existing) - ChatKit session tokens table added
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server / Windows dev
**Project Type**: Web (frontend + backend monorepo)
**Performance Goals**: <5s task creation, <3s query response (per SC-001, SC-002)
**Constraints**: Stateless per request, MCP tools scoped by user authentication
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
| AI Orchestration | OpenAI | OpenAI ChatKit + Platform Workflow | ✅ |
| AI Tools | MCP | FastMCP HTTP Server | ✅ |
| Frontend Chat | - | OpenAI ChatKit React Widget | ✅ |
| Frontend Framework | Next.js | Next.js 15.x | ✅ |
| Auth | Better Auth JWT | Reuse Phase 2 + MCP token auth | ✅ |

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
│   │   └── chatkit.py       # [NEW] ChatKit session token endpoint
│   ├── services/
│   │   ├── task_service.py           # [existing] Task CRUD operations
│   │   └── chatkit_session_service.py # [NEW] ChatKit session token management
│   ├── models/
│   │   ├── task.py              # [existing] Task entity
│   │   └── chatkit_session.py   # [NEW] ChatKit session token entity
│   ├── mcp/
│   │   └── server.py        # [NEW] FastMCP server with task tools
│   ├── agent/
│   │   └── context.py       # [NEW] UserContext dataclass
│   ├── middleware/
│   │   └── rate_limit.py    # [NEW] Rate limiting middleware
│   ├── dependencies/
│   │   ├── auth.py          # [existing] JWT validation
│   │   └── database.py      # [existing] DB session
│   ├── config/
│   │   └── settings.py      # [modify] Add MCP and ChatKit settings
│   └── main.py              # [modify] Mount MCP server at /mcp
├── alembic/versions/
│   ├── 001_create_task_table.py              # [existing]
│   ├── 002_change_user_id_to_string.py       # [existing]
│   └── 2622ddabaf3c_add_chatkit_session_table.py # [NEW]
└── tests/
    └── test_mcp_tools.py    # [NEW] MCP tools tests

frontend/
├── src/
│   ├── app/
│   │   ├── (protected)/
│   │   │   ├── dashboard/   # [existing] Task management UI
│   │   │   └── chat/        # [NEW] Chat page with ChatKit widget
│   │   │       └── page.tsx # [NEW] ChatKit container
│   │   └── api/
│   │       └── chatkit/
│   │           └── session/
│   │               └── route.ts # [NEW] ChatKit session creation endpoint
│   ├── components/
│   │   ├── chat/
│   │   │   └── chatkit-container.tsx # [NEW] ChatKit widget wrapper
│   │   └── navbar.tsx       # [modify] Add chat link
│   └── lib/
│       └── auth.ts          # [existing] Better Auth client
└── package.json             # [modify] Add @openai/chatkit-react
```

**Structure Decision**: Uses OpenAI ChatKit for the chat UI instead of custom components. ChatKit manages conversation history internally while our FastMCP server provides task operations as external tools.

## Data Model

> **Note**: Conversation and message persistence is handled by OpenAI ChatKit internally. We only store session tokens for MCP authentication.

### ChatKit Session Table

```sql
CREATE TABLE chatkit_session (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_chatkit_session_token ON chatkit_session(token);
CREATE INDEX idx_chatkit_session_user_id ON chatkit_session(user_id);
```

**Purpose**: Session tokens authenticate MCP tool calls from ChatKit. When ChatKit invokes our MCP server, we validate the session token to identify the user.

## API Contract

### Frontend: POST /api/chatkit/session

Creates a ChatKit session for the authenticated user.

**Request:** (no body required, uses session cookie)

**Response:**
```json
{
  "client_secret": "chatkit_session_xxx..."
}
```

### Backend: POST /api/chatkit/token

Creates a session token for MCP authentication.

**Request:** (JWT required in Authorization header)

**Response:**
```json
{
  "token": "mcp_session_xxx..."
}
```

### MCP Server: /mcp (Streamable HTTP)

FastMCP server mounted at `/mcp` endpoint. ChatKit's workflow calls this server when the AI needs to execute task operations.

**Authentication**:
- API Key via `Authorization: Bearer <MCP_API_KEY>` header
- User identification via `X-User-ID` header or `user_id` query param
- Fallback: `MCP_DEFAULT_USER_ID` environment variable (for testing)

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                         │
│  /chat page with ChatKit widget                            │
│  Calls /api/chatkit/session to get client_secret           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 OpenAI ChatKit                              │
│  - Manages conversation UI (messages, input, streaming)    │
│  - Persists conversation history internally                │
│  - Connects to OpenAI Platform Workflow                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              OpenAI Platform Workflow                       │
│  - Configured at platform.openai.com/agents                │
│  - Model: gpt-4o-mini                                      │
│  - MCP Server: https://your-backend.com/mcp                │
│  - Tools: add_task, list_tasks, update_task,               │
│           complete_task, delete_task                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              FastMCP HTTP Server (/mcp)                     │
│  - Mounted on FastAPI backend                              │
│  - AuthMiddleware extracts user_id from headers            │
│  - Tools call TaskService with user_id isolation           │
│  - Returns structured string results                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    TaskService                              │
│  - Existing Phase 2 service layer                          │
│  - All CRUD operations scoped by user_id                   │
│  - No direct database access by MCP tools                  │
└─────────────────────────────────────────────────────────────┘
```

**Key Architectural Decisions:**
1. **ChatKit manages conversations** - No custom conversation/message tables needed
2. **MCP over HTTP** - FastMCP server exposed at `/mcp` for workflow tool calls
3. **User auth via headers** - MCP server validates user via API key + X-User-ID header
4. **Stateless tools** - MCP tools receive user context per request, no server-side session state

## MCP Tools Specification

> **Implementation**: Tools are defined using FastMCP's `@mcp.tool` decorator in `backend/app/mcp/server.py`. User context is obtained from the request via AuthMiddleware.

### add_task
```python
@mcp.tool
async def add_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: str = "",
) -> str:
    """Add a new task to the todo list.

    Args:
        title: Task title (required)
        description: Task description
        priority: Priority level - high, medium, or low
        due_date: Due date in YYYY-MM-DD format

    Returns:
        "Created task: {title}" or "Error: {reason}"
    """
```

### list_tasks
```python
@mcp.tool
async def list_tasks(
    filter_status: str = "all",
    search: str = "",
) -> str:
    """List all tasks, optionally filtered.

    Args:
        filter_status: Filter by status - all, pending, or completed
        search: Search term to filter tasks by title

    Returns:
        Formatted task list with status indicators
    """
```

### update_task
```python
@mcp.tool
async def update_task(
    task_id: str,
    title: str = "",
    description: str = "",
    priority: str = "",
    due_date: str = "",
) -> str:
    """Update an existing task.

    Args:
        task_id: The ID of the task to update
        title: New title (leave empty to keep current)
        description: New description (leave empty to keep current)
        priority: New priority - high, medium, or low
        due_date: New due date in YYYY-MM-DD format

    Returns:
        "Updated: {title}" or "Error: {reason}"
    """
```

### complete_task
```python
@mcp.tool
async def complete_task(task_id: str) -> str:
    """Mark a task as completed.

    Args:
        task_id: The ID of the task to complete

    Returns:
        "Completed: {title}" or "Error: {reason}"
    """
```

### delete_task
```python
@mcp.tool
async def delete_task(task_id: str) -> str:
    """Delete a task permanently.

    Args:
        task_id: The ID of the task to delete

    Returns:
        "Deleted: {title}" or "Error: {reason}"
    """
```

## System Prompt

> **Note**: System prompt is configured in the OpenAI Platform Workflow at platform.openai.com/agents. The MCP server configuration includes the server URL and available tools.

```
You are a helpful task management assistant. You help users manage their todo list through natural conversation.

CAPABILITIES:
- Add new tasks with optional priority (high/medium/low) and due dates
- List tasks (all, pending, or completed)
- Update task titles, descriptions, priority, or due dates
- Mark tasks as complete
- Delete tasks

GUIDELINES:
1. Always use the provided tools to modify tasks - never pretend to modify them
2. When referencing tasks, use their ID for precision
3. If a user's request is ambiguous, ask for clarification
4. Confirm all modifications with a brief summary
5. If a task operation fails, explain the issue clearly
6. Be conversational but concise
7. Parse natural language dates like "tomorrow", "next Friday", "in 3 days"
```

## Complexity Tracking

> No constitution violations requiring justification.

| Component | Complexity | Justification |
|-----------|------------|---------------|
| ChatKit Integration | Low | Hosted widget, minimal frontend code |
| FastMCP Server | Medium | HTTP transport with auth middleware |
| MCP Tools | Low | Thin wrappers around existing TaskService |
| Session Token Auth | Medium | JWT signing and token validation |

## Dependencies to Add

### Backend (pyproject.toml)

```toml
dependencies = [
    # ... existing deps ...
    "fastmcp>=0.1.0",              # FastMCP server
    "PyJWT>=2.8.0",                # JWT for MCP auth
]
```

### Frontend (package.json)

```json
{
  "dependencies": {
    "@openai/chatkit-react": "^0.1.0"
  }
}
```

### Environment Variables

```env
# Backend
OPENAI_API_KEY=sk-...              # OpenAI API key
MCP_API_KEY=your-mcp-api-key       # API key for MCP auth
MCP_DEFAULT_USER_ID=               # Optional: default user for testing

# Frontend
OPENAI_API_KEY=sk-...              # For ChatKit session creation
OPENAI_CHATKIT_WORKFLOW_ID=wf-...  # ChatKit workflow ID from platform
```

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| AI Response Latency | ChatKit provides streaming by default |
| MCP Auth Complexity | Multiple auth methods: API key + header, JWT, default user fallback |
| Tool Execution Errors | Tools return error strings for agent interpretation |
| Auth Token Expiry | Session tokens have 24h expiry, frontend re-fetches as needed |
| ChatKit Service Outage | Graceful error display in UI with retry option |

## Success Criteria Mapping

| Success Criteria | Implementation | Measurement |
|-----------------|----------------|-------------|
| SC-001: <5s task creation | ChatKit streaming + gpt-4o-mini | Manual testing |
| SC-002: <3s query response | Indexed DB queries | Manual testing |
| SC-003: 95% grounded responses | MCP tools query real user data | Manual review of responses |
| SC-004: Conversation persistence | ChatKit manages internally | Browser refresh test |
| SC-005: 100 concurrent sessions | Stateless MCP server | Load testing (Phase 4) |
| SC-006: All 5 operations accessible | 5 MCP tools implemented | Integration tests |
| SC-007: Tool metadata in responses | ChatKit shows tool calls in UI | Visual verification |
| SC-008: No cross-user data leakage | user_id from auth, scoped queries | Security review |
