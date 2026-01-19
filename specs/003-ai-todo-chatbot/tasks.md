# Implementation Tasks: AI-Powered Todo Chatbot (Phase 3)

**Branch**: `003-ai-todo-chatbot`
**Plan**: [plan.md](./plan.md)
**Generated**: 2026-01-04

## Task Overview

| Phase | Tasks | Focus |
|-------|-------|-------|
| 1. Foundation | 1.1-1.3 | Dependencies, models, migrations |
| 2. Services | 2.1-2.2 | Conversation and chat services |
| 3. Agent | 3.1-3.3 | MCP tools, agent config, prompts |
| 4. API | 4.1-4.2 | Chat endpoint with SSE |
| 5. Frontend | 5.1-5.4 | Chat UI components |
| 6. Integration | 6.1-6.3 | E2E testing, observability, polish |

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

## Phase 5: Frontend

### Task 5.1: Create Chat API Client

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 4.2

**Objective**: Create TypeScript client for chat API with SSE support.

**Acceptance Criteria**:
- [x] `sendChatMessage(message)` - sends message, returns SSE stream
- [x] Parses SSE events into typed objects
- [x] Handles connection errors
- [x] Uses existing auth token from session

**Files to Create**:
- `frontend/src/lib/chat-api.ts`

**Implementation**:
```typescript
export interface ChatEvent {
  type: 'thinking' | 'tool_call' | 'tool_result' | 'response' | 'done';
  content?: string;
  tool?: string;
  status?: string;
  result?: string;
  conversation_id?: string;
}

export async function* sendChatMessage(message: string): AsyncGenerator<ChatEvent> {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });

  const reader = response.body!.getReader();
  // Parse SSE stream...
}
```

---

### Task 5.2: Create Chat Hook

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 5.1

**Objective**: Create React hook for chat state management.

**Acceptance Criteria**:
- [x] `useChat()` hook returns messages, sendMessage, isLoading, error
- [x] Manages message history state
- [x] Handles streaming updates
- [x] Auto-scrolls on new messages

**Files to Create**:
- `frontend/src/hooks/use-chat.ts`

**Implementation**:
```typescript
export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (content: string) => {
    setIsLoading(true);
    setMessages(prev => [...prev, { role: 'user', content }]);

    try {
      for await (const event of sendChatMessage(content)) {
        // Handle streaming events...
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, sendMessage, isLoading, error };
}
```

---

### Task 5.3: Create Chat Components

**Status**: `completed`
**Estimated Files**: 5
**Dependencies**: 5.2

**Objective**: Build chat UI components.

**Acceptance Criteria**:
- [x] `ChatContainer` - main wrapper with scroll area
- [x] `MessageList` - renders message history
- [x] `MessageItem` - individual message bubble (user/assistant/tool)
- [x] `ChatInput` - text input with send button
- [x] `ToolResult` - displays tool execution results inline
- [x] Responsive design with Tailwind CSS
- [x] Loading states during streaming

**Files to Create**:
- `frontend/src/components/chat/chat-container.tsx`
- `frontend/src/components/chat/message-list.tsx`
- `frontend/src/components/chat/message-item.tsx`
- `frontend/src/components/chat/chat-input.tsx`
- `frontend/src/components/chat/tool-result.tsx`

---

### Task 5.4: Create Chat Page

**Status**: `completed`
**Estimated Files**: 2
**Dependencies**: 5.3

**Objective**: Create the /chat page and add navigation.

**Acceptance Criteria**:
- [x] `/chat` page with ChatContainer
- [x] Protected route (requires auth)
- [x] Loads existing conversation history on mount
- [x] Chat link added to navbar
- [x] Page title set appropriately

**Files to Create**:
- `frontend/src/app/(protected)/chat/page.tsx`

**Files to Modify**:
- `frontend/src/components/navbar.tsx`

---

### Task 5.5: Create Chat API Proxy Route

**Status**: `completed`
**Estimated Files**: 1
**Dependencies**: 5.1

**Objective**: Create Next.js API route to proxy chat requests to backend.

**Acceptance Criteria**:
- [x] `POST /api/chat` proxies to backend with auth header
- [x] Streams SSE response back to client
- [x] Handles backend errors gracefully

**Files to Create**:
- `frontend/src/app/api/chat/route.ts`

**Implementation**:
```typescript
export async function POST(request: Request) {
  const session = await auth.api.getSession({ headers: request.headers });
  if (!session) {
    return new Response('Unauthorized', { status: 401 });
  }

  const body = await request.json();
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

  const response = await fetch(`${backendUrl}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.token}`,
    },
    body: JSON.stringify(body),
  });

  return new Response(response.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
```

---

## Phase 6: Integration & Polish

### Task 6.1: Integration Testing

**Status**: `completed`
**Estimated Files**: 2
**Dependencies**: 5.4

**Objective**: Write integration tests for chat flow.

**Acceptance Criteria**:
- [x] Test: Create task via chat → verify task in DB
- [x] Test: List tasks via chat → verify response matches DB
- [x] Test: Complete task via chat → verify status change
- [x] Test: Delete task via chat → verify removal
- [x] Test: Conversation persistence across requests
- [x] Test: Message history limits (20 messages)

**Files to Create**:
- `backend/tests/test_chat_integration.py`
- `backend/tests/test_conversation_service.py`

---

### Task 6.2: Error Handling & Logging

**Status**: `completed`
**Estimated Files**: 2
**Dependencies**: 6.1

**Objective**: Add structured logging and error handling.

**Acceptance Criteria**:
- [x] Request ID generated for each chat request
- [x] Structured logs with request_id, user_id, tool calls
- [x] Graceful handling of OpenAI API errors
- [x] User-friendly error messages in UI

**Files to Modify**:
- `backend/app/services/chat_service.py`
- `backend/app/api/routes/chat.py`

---

### Task 6.3: Implement Observability Infrastructure

**Status**: `completed`
**Estimated Files**: 3
**Dependencies**: 4.2

**Objective**: Add structured logging with request IDs and key metrics tracking per FR-024 and FR-025.

**Acceptance Criteria**:
- [x] Unique request_id generated for each chat request (UUID)
- [x] Structured JSON logs include: request_id, user_id, timestamp, tool_calls, latency_ms
- [x] Metrics captured: request latency (p50/p95), AI service response time, tool call counts
- [x] Logs written to stdout in JSON format for container aggregation
- [x] Request ID passed through to agent context for tool-level logging

**Files to Create**:
- `backend/app/middleware/request_id.py`

**Files to Modify**:
- `backend/app/services/chat_service.py`
- `backend/app/api/routes/chat.py`
- `backend/app/main.py`

**Implementation**:
```python
# middleware/request_id.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

**Test Cases**:
```python
async def test_request_id_in_response_header():
    response = await client.post("/api/chat", json={"message": "hi"}, headers=auth_headers)
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 36  # UUID format

async def test_structured_log_format(caplog):
    await client.post("/api/chat", json={"message": "list tasks"}, headers=auth_headers)
    # Verify log contains required fields
    log_record = json.loads(caplog.records[-1].message)
    assert "request_id" in log_record
    assert "user_id" in log_record
    assert "latency_ms" in log_record
```

---

## Dependency Graph

```
1.1 (deps) ─────┐
                ├─→ 1.2 (conv model) ─→ 1.3 (msg model) ─→ 1.4 (migrations)
                │                                              │
                │                                              ▼
                │                                         2.1 (conv svc)
                │                                              │
                └─────────────────────────────────────────────┬┘
                                                              │
2.2 (schemas) ─────────────────────────────────────────┐      │
                                                       │      │
3.1 (context) ←────────────────────────────────────────┼──────┘
        │                                              │
        ▼                                              │
3.2 (tools) ──→ 3.4 (agent) ←── 3.3 (prompts)         │
                    │                                  │
                    ▼                                  │
               4.1 (chat svc) ←────────────────────────┘
                    │
                    ▼
               4.2 (chat endpoint)
                    │
                    ▼
               5.1 (chat api client)
                    │
                    ▼
               5.2 (chat hook)
                    │
                    ├──→ 5.3 (components)
                    │           │
                    ▼           ▼
               5.5 (proxy) ─→ 5.4 (page)
                                │
                                ▼
                           6.1 (integration tests)
                                │
                                ▼
                           6.2 (error handling)
                                │
                                ▼
                           6.3 (observability)
```

## Estimated Effort

| Phase | Tasks | Est. Time |
|-------|-------|-----------|
| 1. Foundation | 4 | Core setup |
| 2. Services | 2 | Data layer |
| 3. Agent | 4 | AI integration |
| 4. API | 2 | Endpoint |
| 5. Frontend | 5 | UI |
| 6. Integration | 3 | Polish |
| **Total** | **20** | |
