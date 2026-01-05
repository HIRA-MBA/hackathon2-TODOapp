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
| 6. Integration | 6.1-6.2 | E2E testing, polish |

---

## Phase 1: Foundation

### Task 1.1: Add Backend Dependencies

**Status**: `pending`
**Estimated Files**: 1
**Dependencies**: None

**Objective**: Add OpenAI Agents SDK and SSE support to backend.

**Acceptance Criteria**:
- [ ] `openai-agents>=0.0.10` added to pyproject.toml
- [ ] `sse-starlette>=2.0.0` added to pyproject.toml
- [ ] `OPENAI_API_KEY` added to settings.py
- [ ] Dependencies install successfully with `uv sync`

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

**Status**: `pending`
**Estimated Files**: 2
**Dependencies**: 1.1

**Objective**: Create SQLModel entity for conversations.

**Acceptance Criteria**:
- [ ] Conversation model with id, user_id, created_at, last_activity_at
- [ ] Model registered in models/__init__.py
- [ ] Index on user_id for fast lookups

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

**Status**: `pending`
**Estimated Files**: 2
**Dependencies**: 1.2

**Objective**: Create SQLModel entity for messages with role enum.

**Acceptance Criteria**:
- [ ] Message model with id, conversation_id, role, content, metadata, created_at
- [ ] Role constrained to 'user', 'assistant', 'tool'
- [ ] Foreign key to Conversation with CASCADE delete
- [ ] Composite index on (conversation_id, created_at)
- [ ] Model registered in models/__init__.py

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

**Status**: `pending`
**Estimated Files**: 2
**Dependencies**: 1.2, 1.3

**Objective**: Create Alembic migrations for Conversation and Message tables.

**Acceptance Criteria**:
- [ ] Migration 003 creates conversation table with index
- [ ] Migration 004 creates message table with FK and indexes
- [ ] Migrations run successfully: `alembic upgrade head`
- [ ] Rollback works: `alembic downgrade -1`

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

**Status**: `pending`
**Estimated Files**: 2
**Dependencies**: 1.4

**Objective**: Implement service for conversation and message CRUD operations.

**Acceptance Criteria**:
- [ ] `get_or_create_conversation(user_id)` - returns existing or creates new
- [ ] `get_recent_messages(conversation_id, limit=20)` - returns messages ordered by created_at
- [ ] `create_message(conversation_id, role, content, metadata)` - persists message
- [ ] `update_conversation_activity(conversation_id)` - updates last_activity_at
- [ ] All queries scoped by user_id where applicable

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

**Status**: `pending`
**Estimated Files**: 1
**Dependencies**: 1.3

**Objective**: Define Pydantic schemas for chat request/response.

**Acceptance Criteria**:
- [ ] `ChatRequest` with message (required)
- [ ] `ChatResponse` with response, tool_executions, conversation_id
- [ ] `ToolExecution` with tool, status, result
- [ ] `ChatStreamEvent` for SSE events

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

---

## Phase 3: Agent Layer

### Task 3.1: Create User Context

**Status**: `pending`
**Estimated Files**: 1
**Dependencies**: 2.1

**Objective**: Define UserContext dataclass for agent tool injection.

**Acceptance Criteria**:
- [ ] `UserContext` dataclass with user_id, email, db session
- [ ] Immutable (frozen=True)
- [ ] Type hints for all fields

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

**Status**: `pending`
**Estimated Files**: 1
**Dependencies**: 3.1, existing TaskService

**Objective**: Create 5 MCP tools wrapping TaskService operations.

**Acceptance Criteria**:
- [ ] `add_task(ctx, title, description?)` - creates task, returns success/error string
- [ ] `list_tasks(ctx, status?, search?)` - returns formatted task list
- [ ] `update_task(ctx, task_id, title?, description?)` - updates task
- [ ] `complete_task(ctx, task_id)` - marks task complete
- [ ] `delete_task(ctx, task_id)` - removes task
- [ ] All tools use TaskService (no direct DB access)
- [ ] All tools return standardized response strings
- [ ] Tools handle UUID parsing errors gracefully

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

**Status**: `pending`
**Estimated Files**: 1
**Dependencies**: None

**Objective**: Define system prompt template for the todo agent.

**Acceptance Criteria**:
- [ ] `SYSTEM_PROMPT_TEMPLATE` with {task_context} placeholder
- [ ] `format_task_context(tasks)` - formats task list for prompt
- [ ] `build_system_prompt(tasks)` - returns complete prompt

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

**Status**: `pending`
**Estimated Files**: 1
**Dependencies**: 3.2, 3.3

**Objective**: Set up OpenAI Agent with tools and configuration.

**Acceptance Criteria**:
- [ ] Agent configured with gpt-4o-mini model
- [ ] All 5 tools registered
- [ ] UserContext generic type parameter set
- [ ] Agent name and instructions configured

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

**Status**: `pending`
**Estimated Files**: 1
**Dependencies**: 3.4, 2.1

**Objective**: Implement chat orchestration service that coordinates context assembly and agent execution.

**Acceptance Criteria**:
- [ ] `process_chat_message(user_id, message, db)` - main entry point
- [ ] Assembles context (conversation, messages, tasks)
- [ ] Runs agent with context
- [ ] Persists all messages (user, tool, assistant)
- [ ] Returns ChatResponse or streams events

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

**Status**: `pending`
**Estimated Files**: 2
**Dependencies**: 4.1

**Objective**: Implement POST /api/chat endpoint with SSE streaming.

**Acceptance Criteria**:
- [ ] `POST /api/chat` accepts ChatRequest body
- [ ] Requires JWT authentication (reuse CurrentUser dependency)
- [ ] Returns SSE stream with ChatStreamEvents
- [ ] Handles errors gracefully (persists user message, returns error event)
- [ ] Route registered in main.py

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

**Status**: `pending`
**Estimated Files**: 1
**Dependencies**: 4.2

**Objective**: Create TypeScript client for chat API with SSE support.

**Acceptance Criteria**:
- [ ] `sendChatMessage(message)` - sends message, returns SSE stream
- [ ] Parses SSE events into typed objects
- [ ] Handles connection errors
- [ ] Uses existing auth token from session

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

**Status**: `pending`
**Estimated Files**: 1
**Dependencies**: 5.1

**Objective**: Create React hook for chat state management.

**Acceptance Criteria**:
- [ ] `useChat()` hook returns messages, sendMessage, isLoading, error
- [ ] Manages message history state
- [ ] Handles streaming updates
- [ ] Auto-scrolls on new messages

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

**Status**: `pending`
**Estimated Files**: 5
**Dependencies**: 5.2

**Objective**: Build chat UI components.

**Acceptance Criteria**:
- [ ] `ChatContainer` - main wrapper with scroll area
- [ ] `MessageList` - renders message history
- [ ] `MessageItem` - individual message bubble (user/assistant/tool)
- [ ] `ChatInput` - text input with send button
- [ ] `ToolResult` - displays tool execution results inline
- [ ] Responsive design with Tailwind CSS
- [ ] Loading states during streaming

**Files to Create**:
- `frontend/src/components/chat/chat-container.tsx`
- `frontend/src/components/chat/message-list.tsx`
- `frontend/src/components/chat/message-item.tsx`
- `frontend/src/components/chat/chat-input.tsx`
- `frontend/src/components/chat/tool-result.tsx`

---

### Task 5.4: Create Chat Page

**Status**: `pending`
**Estimated Files**: 2
**Dependencies**: 5.3

**Objective**: Create the /chat page and add navigation.

**Acceptance Criteria**:
- [ ] `/chat` page with ChatContainer
- [ ] Protected route (requires auth)
- [ ] Loads existing conversation history on mount
- [ ] Chat link added to navbar
- [ ] Page title set appropriately

**Files to Create**:
- `frontend/src/app/(protected)/chat/page.tsx`

**Files to Modify**:
- `frontend/src/components/navbar.tsx`

---

### Task 5.5: Create Chat API Proxy Route

**Status**: `pending`
**Estimated Files**: 1
**Dependencies**: 5.1

**Objective**: Create Next.js API route to proxy chat requests to backend.

**Acceptance Criteria**:
- [ ] `POST /api/chat` proxies to backend with auth header
- [ ] Streams SSE response back to client
- [ ] Handles backend errors gracefully

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

**Status**: `pending`
**Estimated Files**: 2
**Dependencies**: 5.4

**Objective**: Write integration tests for chat flow.

**Acceptance Criteria**:
- [ ] Test: Create task via chat → verify task in DB
- [ ] Test: List tasks via chat → verify response matches DB
- [ ] Test: Complete task via chat → verify status change
- [ ] Test: Delete task via chat → verify removal
- [ ] Test: Conversation persistence across requests
- [ ] Test: Message history limits (20 messages)

**Files to Create**:
- `backend/tests/test_chat_integration.py`
- `backend/tests/test_conversation_service.py`

---

### Task 6.2: Error Handling & Logging

**Status**: `pending`
**Estimated Files**: 2
**Dependencies**: 6.1

**Objective**: Add structured logging and error handling.

**Acceptance Criteria**:
- [ ] Request ID generated for each chat request
- [ ] Structured logs with request_id, user_id, tool calls
- [ ] Graceful handling of OpenAI API errors
- [ ] User-friendly error messages in UI

**Files to Modify**:
- `backend/app/services/chat_service.py`
- `backend/app/api/routes/chat.py`

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
                           6.2 (logging)
```

## Estimated Effort

| Phase | Tasks | Est. Time |
|-------|-------|-----------|
| 1. Foundation | 4 | Core setup |
| 2. Services | 2 | Data layer |
| 3. Agent | 4 | AI integration |
| 4. API | 2 | Endpoint |
| 5. Frontend | 5 | UI |
| 6. Integration | 2 | Polish |
| **Total** | **19** | |
