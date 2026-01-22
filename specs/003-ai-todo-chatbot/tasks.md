# Implementation Tasks: AI-Powered Todo Chatbot (Phase 3)

**Branch**: `003-ai-todo-chatbot`
**Plan**: [plan.md](./plan.md)
**Generated**: 2026-01-04

## Task Overview

> **Architecture Update (2026-01-22)**: Implementation uses OpenAI ChatKit instead of custom SSE architecture. Tasks updated to reflect actual implementation.

| Phase | Tasks | Focus |
|-------|-------|-------|
| 1. Foundation | 1.1-1.4 | Dependencies, models, migrations |
| 2. Services | 2.1-2.2 | ChatKit session service |
| 3. Agent | 3.1-3.4 | FastMCP server, tools, auth |
| 4. API | 4.1-4.2 | MCP endpoint, ChatKit token API |
| 5. Frontend | 5.1-5.5 | ChatKit integration, workflow config |
| 6. Security | 6.0a-6.0c | Rate limiting, timeout, clear history |
| 7. Integration | 7.1-7.3 | Testing, observability, polish |

---

## Phase 1: Foundation

### Task 1.1: Add Backend Dependencies

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: None

**Objective**: Add OpenAI Agents SDK and SSE support to backend.

**Acceptance Criteria**:
- [x] `openai-agents>=0.0.10` added to pyproject.toml
- [x] `sse-starlette>=2.0.0` added to pyproject.toml
- [x] `OPENAI_API_KEY` added to settings.py
- [x] Dependencies install successfully with `uv sync`

**Files to Modify**:
- `backend/pyproject.toml`
- `backend/app/config/settings.py`
- `backend/.env.example` (create if not exists)

**Test Cases**:
```python
# Verify imports work
from agents import Agent, function_tool
from sse_starlette.sse import EventSourceResponse
```

---

### Task 1.2: Create Conversation Model

**Status**: `completed`
**Estimated Files**: 2
**Dependencies**: 1.1

**Objective**: Create SQLModel entity for conversations.

**Acceptance Criteria**:
- [x] Conversation model with id, user_id, created_at, last_activity_at
- [x] Model registered in models/__init__.py
- [x] Index on user_id for fast lookups

**Files to Create**:
- `backend/app/models/conversation.py`

**Files to Modify**:
- `backend/app/models/__init__.py`

**Implementation**:
```python
class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(max_length=64, index=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
```

---

### Task 1.3: Create Message Model

**Status**: `completed`
**Estimated Files**: 2
**Dependencies**: 1.2

**Objective**: Create SQLModel entity for messages with role enum.

**Acceptance Criteria**:
- [x] Message model with id, conversation_id, role, content, metadata, created_at
- [x] Role constrained to 'user', 'assistant', 'tool'
- [x] Foreign key to Conversation with CASCADE delete
- [x] Composite index on (conversation_id, created_at)
- [x] Model registered in models/__init__.py

**Files to Create**:
- `backend/app/models/message.py`

**Files to Modify**:
- `backend/app/models/__init__.py`

**Implementation**:
```python
class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class Message(SQLModel, table=True):
    __tablename__ = "message"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversation.id", nullable=False)
    role: MessageRole = Field(nullable=False)
    content: str = Field(nullable=False)
    metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

### Task 1.4: Create Database Migrations

**Status**: `completed`
**Estimated Files**: 2
**Dependencies**: 1.2, 1.3

**Objective**: Create Alembic migrations for Conversation and Message tables.

**Acceptance Criteria**:
- [x] Migration 003 creates conversation table with index
- [x] Migration 004 creates message table with FK and indexes
- [x] Migrations run successfully: `alembic upgrade head`
- [x] Rollback works: `alembic downgrade -1`

**Files to Create**:
- `backend/alembic/versions/003_create_conversation_table.py`
- `backend/alembic/versions/004_create_message_table.py`

**Test Cases**:
```bash
cd backend
alembic upgrade head
alembic downgrade -2
alembic upgrade head
```

---

## Phase 2: Services

### Task 2.1: Create Conversation Service

**Status**: `completed`
**Estimated Files**: 2
**Dependencies**: 1.4

**Objective**: Implement service for conversation and message CRUD operations.

**Acceptance Criteria**:
- [x] `get_or_create_conversation(user_id)` - returns existing or creates new
- [x] `get_recent_messages(conversation_id, limit=20)` - returns messages ordered by created_at
- [x] `create_message(conversation_id, role, content, metadata)` - persists message
- [x] `update_conversation_activity(conversation_id)` - updates last_activity_at
- [x] All queries scoped by user_id where applicable

**Files to Create**:
- `backend/app/services/conversation_service.py`

**Files to Modify**:
- `backend/app/services/__init__.py`

**Test Cases**:
```python
async def test_get_or_create_conversation():
    # First call creates
    conv1 = await service.get_or_create_conversation(user_id)
    assert conv1 is not None

    # Second call returns same
    conv2 = await service.get_or_create_conversation(user_id)
    assert conv1.id == conv2.id

async def test_message_ordering():
    # Messages returned newest last (chronological)
    messages = await service.get_recent_messages(conv_id, limit=5)
    assert messages[0].created_at < messages[-1].created_at
```

---

### Task 2.2: Create Chat Schemas

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 1.3

**Objective**: Define Pydantic schemas for chat request/response.

**Acceptance Criteria**:
- [x] `ChatRequest` with message (required)
- [x] `ChatResponse` with response, tool_executions, conversation_id
- [x] `ToolExecution` with tool, status, result
- [x] `ChatStreamEvent` for SSE events

**Files to Create**:
- `backend/app/schemas/chat.py`

**Implementation**:
```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)

class ToolExecution(BaseModel):
    tool: str
    status: str  # "success" | "error"
    result: str

class ChatResponse(BaseModel):
    response: str
    tool_executions: list[ToolExecution]
    conversation_id: str

class ChatStreamEvent(BaseModel):
    type: str  # "thinking" | "tool_call" | "tool_result" | "response" | "done"
    content: str | None = None
    tool: str | None = None
    status: str | None = None
    result: str | None = None
    conversation_id: str | None = None
```

**Test Cases**:
```python
async def test_message_length_validation():
    long_message = "x" * 2001
    response = await client.post("/api/chat", json={"message": long_message}, headers=auth_headers)
    assert response.status_code == 422
    assert "2000" in response.json()["detail"][0]["msg"]

async def test_empty_message_rejected():
    response = await client.post("/api/chat", json={"message": ""}, headers=auth_headers)
    assert response.status_code == 422
```

---

## Phase 3: Agent Layer

### Task 3.1: Create User Context

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 2.1

**Objective**: Define UserContext dataclass for agent tool injection.

**Acceptance Criteria**:
- [x] `UserContext` dataclass with user_id, email, db session
- [x] Immutable (frozen=True)
- [x] Type hints for all fields

**Files to Create**:
- `backend/app/agent/context.py`

**Implementation**:
```python
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

@dataclass(frozen=True)
class UserContext:
    user_id: str
    email: str | None
    db: AsyncSession
```

---

### Task 3.2: Implement MCP Tools

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 3.1, existing TaskService

**Objective**: Create 5 MCP tools wrapping TaskService operations.

**Acceptance Criteria**:
- [x] `add_task(ctx, title, description?)` - creates task, returns success/error string
- [x] `list_tasks(ctx, status?, search?)` - returns formatted task list
- [x] `update_task(ctx, task_id, title?, description?)` - updates task
- [x] `complete_task(ctx, task_id)` - marks task complete
- [x] `delete_task(ctx, task_id)` - removes task
- [x] All tools use TaskService (no direct DB access)
- [x] All tools return standardized response strings
- [x] Tools handle UUID parsing errors gracefully

**Files to Create**:
- `backend/app/tools/task_tools.py`

**Test Cases**:
```python
async def test_add_task_success():
    result = await add_task(ctx, "Buy groceries")
    assert "success" in result
    assert "Buy groceries" in result

async def test_complete_task_not_found():
    result = await complete_task(ctx, "invalid-uuid")
    assert "error" in result

async def test_list_tasks_empty():
    result = await list_tasks(ctx, status="all")
    assert "No tasks found" in result or "0 tasks" in result
```

---

### Task 3.3: Create System Prompts

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: None

**Objective**: Define system prompt template for the todo agent.

**Acceptance Criteria**:
- [x] `SYSTEM_PROMPT_TEMPLATE` with {task_context} placeholder
- [x] `format_task_context(tasks)` - formats task list for prompt
- [x] `build_system_prompt(tasks)` - returns complete prompt

**Files to Create**:
- `backend/app/agent/prompts.py`

**Implementation**:
```python
SYSTEM_PROMPT_TEMPLATE = """You are a helpful task management assistant...

CURRENT USER TASKS:
{task_context}

CAPABILITIES:
- Add new tasks...
"""

def format_task_context(tasks: list[Task]) -> str:
    if not tasks:
        return "No tasks yet."
    lines = []
    for t in tasks:
        status = "✓" if t.completed else "○"
        lines.append(f"#{t.id} [{status}] {t.title}")
    return "\n".join(lines)
```

---

### Task 3.4: Configure Todo Agent

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 3.2, 3.3

**Objective**: Set up OpenAI Agent with tools and configuration.

**Acceptance Criteria**:
- [x] Agent configured with gpt-4o-mini model
- [x] All 5 tools registered
- [x] UserContext generic type parameter set
- [x] Agent name and instructions configured

**Files to Create**:
- `backend/app/agent/todo_agent.py`

**Implementation**:
```python
from agents import Agent
from app.agent.context import UserContext
from app.tools.task_tools import add_task, list_tasks, update_task, complete_task, delete_task

todo_agent = Agent[UserContext](
    name="TodoAssistant",
    instructions="You are a helpful task management assistant...",
    tools=[add_task, list_tasks, update_task, complete_task, delete_task],
    model="gpt-4o-mini",
)
```

---

## Phase 4: API Layer

### Task 4.1: Create Chat Service

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 3.4, 2.1

**Objective**: Implement chat orchestration service that coordinates context assembly and agent execution.

**Acceptance Criteria**:
- [x] `process_chat_message(user_id, message, db)` - main entry point
- [x] Assembles context (conversation, messages, tasks)
- [x] Runs agent with context
- [x] Persists all messages (user, tool, assistant)
- [x] Returns ChatResponse or streams events

**Files to Create**:
- `backend/app/services/chat_service.py`

**Implementation Outline**:
```python
async def process_chat_message(
    user_id: str,
    email: str | None,
    message: str,
    db: AsyncSession,
) -> AsyncGenerator[ChatStreamEvent, None]:
    # 1. Get/create conversation
    conv = await conversation_service.get_or_create_conversation(user_id, db)

    # 2. Load context
    recent_messages = await conversation_service.get_recent_messages(conv.id, db)
    tasks = await task_service.list_tasks(user_id, db)

    # 3. Build system prompt
    system_prompt = build_system_prompt(tasks)

    # 4. Persist user message
    await conversation_service.create_message(conv.id, "user", message, db)

    # 5. Create context and run agent
    ctx = UserContext(user_id=user_id, email=email, db=db)

    # 6. Stream response events
    async for event in run_agent_streaming(ctx, system_prompt, recent_messages, message):
        yield event

    # 7. Persist assistant response
    await conversation_service.create_message(conv.id, "assistant", response, db)
```

---

### Task 4.2: Create Chat Endpoint

**Status**: `completed`
**Estimated Files**: 2
**Dependencies**: 4.1

**Objective**: Implement POST /api/chat endpoint with SSE streaming.

**Acceptance Criteria**:
- [x] `POST /api/chat` accepts ChatRequest body
- [x] Requires JWT authentication (reuse CurrentUser dependency)
- [x] Returns SSE stream with ChatStreamEvents
- [x] Handles errors gracefully (persists user message, returns error event)
- [x] Route registered in main.py

**Files to Create**:
- `backend/app/api/routes/chat.py`

**Files to Modify**:
- `backend/app/main.py`

**Implementation**:
```python
@router.post("/chat")
async def chat(
    request: ChatRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    async def event_generator():
        async for event in chat_service.process_chat_message(
            user_id=user.user_id,
            email=user.email,
            message=request.message,
            db=db,
        ):
            yield {"data": event.model_dump_json()}

    return EventSourceResponse(event_generator())
```

**Test Cases**:
```python
async def test_chat_requires_auth():
    response = await client.post("/api/chat", json={"message": "hi"})
    assert response.status_code == 401

async def test_chat_creates_task():
    response = await client.post(
        "/api/chat",
        json={"message": "Add buy milk"},
        headers={"Authorization": f"Bearer {token}"}
    )
    # Verify task was created
    tasks = await task_service.list_tasks(user_id)
    assert any("milk" in t.title.lower() for t in tasks)
```

---

## Phase 5: Frontend (ChatKit Integration)

> **Architecture Update (2026-01-22)**: Frontend implementation uses OpenAI ChatKit widget instead of custom components. Tasks 5.1-5.3 are superseded by ChatKit integration.

### Task 5.1: Add ChatKit Dependency

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 4.2

**Objective**: Add OpenAI ChatKit React package.

**Acceptance Criteria**:
- [x] `@openai/chatkit-react` added to package.json
- [x] Package installs successfully

**Files to Modify**:
- `frontend/package.json`

---

### Task 5.2: Create ChatKit Session Endpoint

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 5.1

**Objective**: Create API route to generate ChatKit session client_secret.

**Acceptance Criteria**:
- [x] `POST /api/chatkit/session` creates ChatKit session via OpenAI API
- [x] Requires authenticated user session
- [x] Returns `client_secret` for ChatKit widget initialization
- [x] Handles OpenAI API errors gracefully

**Files to Create**:
- `frontend/src/app/api/chatkit/session/route.ts`

**Implementation**:
```typescript
export async function POST(request: NextRequest) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const response = await fetch("https://api.openai.com/v1/chatkit/sessions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${OPENAI_API_KEY}`,
      "OpenAI-Beta": "chatkit_beta=v1",
    },
    body: JSON.stringify({
      workflow: { id: WORKFLOW_ID },
      user: session.user.id,
    }),
  });

  const data = await response.json();
  return NextResponse.json({ client_secret: data.client_secret });
}
```

---

### Task 5.3: Create ChatKit Container Component

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 5.2

**Objective**: Create wrapper component for ChatKit widget.

**Acceptance Criteria**:
- [x] `ChatKitContainer` wraps `useChatKit` hook
- [x] Fetches client_secret from session endpoint
- [x] Displays error state if session creation fails
- [x] Handles ChatKit errors gracefully

**Files to Create**:
- `frontend/src/components/chat/chatkit-container.tsx`

**Implementation**:
```typescript
export function ChatKitContainer() {
  const getClientSecret = async () => {
    const response = await fetch("/api/chatkit/session", { method: "POST" });
    const data = await response.json();
    return data.client_secret;
  };

  const { ui } = useChatKit({
    getClientSecret,
    onError: (error) => console.error("ChatKit error:", error),
  });

  return <div className="h-full">{ui}</div>;
}
```

---

### Task 5.4: Create Chat Page

**Status**: `completed`
**Estimated Files**: 2
**Dependencies**: 5.3

**Objective**: Create the /chat page with ChatKit widget and add navigation.

**Acceptance Criteria**:
- [x] `/chat` page renders ChatKitContainer
- [x] Protected route (requires auth)
- [x] Chat link added to navbar
- [x] Responsive layout with full height

**Files to Create**:
- `frontend/src/app/(protected)/chat/page.tsx`

**Files to Modify**:
- `frontend/src/components/navbar.tsx`

---

### Task 5.5: Configure OpenAI Platform Workflow

**Status**: `completed`
**Estimated Files**: 0 (external configuration)
**Dependencies**: 3.2 (MCP tools)

**Objective**: Set up ChatKit workflow on OpenAI Platform with MCP server connection.

**Acceptance Criteria**:
- [x] Workflow created at platform.openai.com/agents
- [x] MCP server URL configured (https://your-backend.com/mcp)
- [x] System prompt configured for task management
- [x] All 5 task tools available to the workflow
- [x] Workflow ID added to environment variables

**Configuration**:
- Workflow ID: Set in `OPENAI_CHATKIT_WORKFLOW_ID` env var
- MCP Server: Backend `/mcp` endpoint URL
- Model: gpt-4o-mini

---

## Phase 6: Security & Reliability

### Task 6.0a: Implement Rate Limiting (FR-026)

**Status**: `completed`
**Estimated Files**: 2
**Dependencies**: 4.2

**Objective**: Enforce rate limiting of 20 requests per minute per authenticated user.

**Acceptance Criteria**:
- [x] Rate limit middleware tracks requests per user_id
- [x] Returns HTTP 429 with friendly "Please slow down" message when exceeded
- [x] Rate limit resets after 60 seconds
- [x] Applied to chat and MCP endpoints

**Files to Create**:
- `backend/app/middleware/rate_limit.py`

**Files to Modify**:
- `backend/app/main.py`

**Test Cases**:
```python
async def test_rate_limit_exceeded():
    # Send 21 requests in quick succession
    for i in range(21):
        response = await client.post("/api/chat", json={"message": "hi"}, headers=auth_headers)
    assert response.status_code == 429
    assert "slow down" in response.json()["detail"].lower()
```

---

### Task 6.0b: Implement AI Service Timeout (FR-027)

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 4.1

**Objective**: Apply 30-second timeout for AI service requests with no automatic retry.

**Acceptance Criteria**:
- [x] OpenAI API calls timeout after 30 seconds
- [x] Timeout returns user-friendly error message
- [x] No automatic retry - user must manually resend
- [x] User's message is preserved in conversation history

**Files to Modify**:
- `backend/app/mcp/server.py` (timeout on MCP tool calls)

**Implementation**:
```python
# Add timeout to httpx client or fetch calls
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(...)
```

---

### Task 6.0c: Implement Clear History Function (FR-029)

**Status**: `pending`
**Estimated Files**: 2
**Dependencies**: 5.4

**Objective**: Provide "Clear history" button that deletes all messages from user's conversation.

**Acceptance Criteria**:
- [ ] Clear history button visible in chat UI
- [ ] Clicking button shows confirmation dialog
- [ ] Confirmation deletes all messages via API
- [ ] ChatKit widget refreshes after clear

**Note**: ChatKit manages conversation history internally. Clear functionality may require:
1. Backend endpoint to clear ChatKit conversation (if API supports it), OR
2. Creating new ChatKit session (discards old conversation)

**Files to Modify**:
- `frontend/src/components/chat/chatkit-container.tsx`
- `frontend/src/app/api/chatkit/clear/route.ts` (if needed)

---

## Phase 7: Integration & Polish

### Task 7.1: MCP Tools Integration Testing

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 5.5

**Objective**: Write integration tests for MCP tools.

**Acceptance Criteria**:
- [x] Test: add_task creates task in DB for authenticated user
- [x] Test: list_tasks returns user's tasks accurately
- [x] Test: complete_task marks task as completed
- [x] Test: delete_task removes task from DB
- [x] Test: update_task modifies task properties
- [x] Test: Tools reject unauthenticated requests

**Files to Create**:
- `backend/tests/test_mcp_tools.py`

---

### Task 7.2: Error Handling & Logging

**Status**: `completed`
**Estimated Files**: 2
**Dependencies**: 7.1

**Objective**: Add structured logging and error handling for MCP server.

**Acceptance Criteria**:
- [x] MCP tool errors logged with user_id and tool name
- [x] Graceful handling of database errors
- [x] User-friendly error messages returned to ChatKit
- [x] Authentication failures logged with request details

**Files to Modify**:
- `backend/app/mcp/server.py`

---

### Task 7.3: Implement Observability Infrastructure

**Status**: `completed`
**Estimated Files**: 2
**Dependencies**: 6.0a

**Objective**: Add structured logging with request IDs and key metrics tracking per FR-024 and FR-025.

**Acceptance Criteria**:
- [x] Unique request_id generated for each MCP request
- [x] Structured logs include: user_id, tool_name, latency_ms, success/failure
- [x] Logs written to stdout for container aggregation
- [x] Rate limit events logged

**Files to Modify**:
- `backend/app/mcp/server.py`
- `backend/app/middleware/rate_limit.py`

---

## Dependency Graph

```
1.1 (deps) ─────┐
                ├─→ 1.2 (chatkit model) ─→ 1.4 (migrations)
                │                               │
                │                               ▼
                │                          2.1 (chatkit svc)
                │                               │
                └───────────────────────────────┤
                                                │
3.1 (context) ←─────────────────────────────────┤
        │                                       │
        ▼                                       │
3.2 (mcp tools) ──→ 3.4 (mcp server) ←─────────┘
        │                   │
        │                   ▼
        │              4.2 (backend token API)
        │                   │
        └───────────────────┤
                            ▼
                       5.2 (chatkit session endpoint)
                            │
                            ▼
                       5.3 (chatkit container)
                            │
                            ▼
                       5.4 (chat page) ←── 5.5 (workflow config)
                            │
                            ▼
                       6.0a (rate limiting)
                            │
                            ├─→ 6.0b (timeout)
                            │
                            ▼
                       6.0c (clear history)
                            │
                            ▼
                       7.1 (integration tests)
                            │
                            ▼
                       7.2 (error handling)
                            │
                            ▼
                       7.3 (observability)
```

## Estimated Effort

| Phase | Tasks | Status |
|-------|-------|--------|
| 1. Foundation | 4 | ✅ Complete |
| 2. Services | 2 | ✅ Complete |
| 3. Agent | 4 | ✅ Complete |
| 4. API | 2 | ✅ Complete |
| 5. Frontend | 5 | ✅ Complete |
| 6. Security | 3 | ⚠️ 6.0c pending |
| 7. Integration | 3 | ✅ Complete |
| **Total** | **23** | 22/23 complete |
