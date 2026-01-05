# Research: AI-Powered Todo Chatbot (Phase 3)

**Branch**: `003-ai-todo-chatbot`
**Date**: 2026-01-04
**Status**: Complete

## Executive Summary

This research document consolidates findings on implementing a stateless AI-powered chatbot using OpenAI Agents SDK, MCP tools, and RAG patterns for the Todo application.

---

## 1. Agent vs Tool Responsibility Boundaries

### Decision: Clear Separation with Type-Safe Context Propagation

**Agent Responsibilities:**
- Natural language understanding of user intent
- Deciding which tool(s) to call based on intent
- Formatting responses conversationally
- Handling ambiguity with clarifying questions
- Presenting results in user-friendly format

**Tool Responsibilities:**
- Single, atomic operations (add_task, complete_task, etc.)
- Input validation and business rule enforcement
- Database mutations through service layer
- Returning structured results (not formatted text)
- User isolation via context-injected user_id

### Rationale
- Clean separation enables independent testing of agent logic vs tool operations
- Type-safe context (`UserContext`) ensures user_id propagation without trusting client input
- Tools return raw results; agent decides presentation

---

## 2. RAG Context Sources and Retrieval Depth

### Decision: Dual-Source Context with Fixed Retrieval Limits

| Context Source | Retrieval Depth | Purpose |
|---------------|-----------------|---------|
| Conversation History | Last 20 messages | Maintain dialogue continuity |
| User Tasks | Up to 20 active tasks | Ground responses in actual data |

### Context Assembly Strategy

```
System Prompt (Static)
↓
Task Context (Dynamic) - "Current active tasks: #1: buy groceries [medium]..."
↓
Conversation History (Chronological) - Last 20 user/assistant messages
↓
Current User Message
```

### Rationale
- 20 messages ≈ 2K tokens, leaving room for tool calls and responses
- Task context as system message ensures agent always "sees" current state
- Chronological order preserves conversational flow
- Fixed limits prevent context window overflow

### Alternatives Considered
- **Semantic search for relevant messages**: Rejected for MVP - adds complexity without clear benefit for task-focused conversations
- **Unlimited history**: Rejected - context window limits and latency concerns
- **Task summaries vs full list**: Rejected - full list enables precise references ("task #3")

---

## 3. Stateless Conversation Reconstruction Strategy

### Decision: Database-Backed Session with Per-Request Reconstruction

**Flow:**
1. Request arrives with JWT + thread_id
2. Validate JWT → extract user_id
3. Query Conversation by (user_id) - get or create
4. Query Messages by (conversation_id, limit=20, order=created_at DESC)
5. Query Tasks by (user_id, completed=false, limit=20)
6. Construct context payload
7. Execute agent with reconstructed context
8. Persist new messages (user + assistant + tool)
9. Return response

### Database Queries (Optimized)

```sql
-- Get conversation for user (creates if not exists via UPSERT)
SELECT * FROM conversations WHERE user_id = $1;

-- Get recent messages (composite index: user_id, conversation_id, created_at)
SELECT * FROM messages
WHERE conversation_id = $1
ORDER BY created_at DESC
LIMIT 20;

-- Get active tasks for context
SELECT * FROM tasks
WHERE user_id = $1 AND completed = false
ORDER BY created_at DESC
LIMIT 20;
```

### Rationale
- No server-side session state = horizontal scalability
- Database as source of truth = crash recovery
- Single conversation per user (MVP) simplifies reconstruction
- Indexes on (user_id, created_at) ensure sub-100ms queries

---

## 4. MCP Tool Granularity and Naming

### Decision: 5 Atomic Tools with Verb-Noun Naming

| Tool | Purpose | Parameters |
|------|---------|------------|
| `add_task` | Create new task | title (req), description (opt) |
| `list_tasks` | Query tasks | status (all/pending/completed), search (opt) |
| `update_task` | Modify task | task_id (req), title (opt), description (opt) |
| `complete_task` | Mark as done | task_id (req) |
| `delete_task` | Remove task | task_id (req) |

### Naming Convention
- **Pattern**: `verb_noun` (action-oriented)
- **Consistency**: All tools follow same pattern
- **Discoverability**: Names describe capability to LLM

### Tool Response Format

```python
# Success
"add_task: success - created task #42 'buy groceries'"

# Error
"complete_task: error - task #999 not found"
```

### Rationale
- Single responsibility per tool = predictable behavior
- Separate `complete_task` vs `update_task` = clear intent signaling to agent
- `list_tasks` with filters vs separate `list_pending`/`list_completed` = fewer tools, more flexible
- Consistent response format enables agent pattern matching

### Alternatives Considered
- **Combined CRUD tool**: Rejected - ambiguous intent, harder for LLM to choose correctly
- **Task ID in URL**: Rejected - tools don't have URLs, use parameters
- **Bulk operations**: Rejected - out of scope for MVP

---

## 5. Error Handling vs Clarification Behavior

### Decision: Tool Errors → Agent Interpretation → User Clarification

**Error Classification:**

| Error Type | Handler | Response Format |
|------------|---------|-----------------|
| Authentication | FastAPI middleware | HTTP 401, redirect to signin |
| Authorization | Tool execution | "error - task not found" (no 403 leak) |
| Validation | Tool execution | "error - [field] invalid: [reason]" |
| Not Found | Tool execution | "error - task #X not found" |
| System | FastAPI exception handler | HTTP 503, friendly error message |

### Tool Error Pattern

```python
# Tools return errors as strings, not exceptions
async def complete_task(ctx, task_id: int) -> str:
    task = await get_task(task_id, ctx.user_id)
    if not task:
        return "complete_task: error - task not found or access denied"
    if task.completed:
        return "complete_task: info - task already completed"
    # ... success
    return "complete_task: success - marked task #X as done"
```

### Agent Clarification Triggers

The agent will ask for clarification when:
1. **Ambiguous task reference**: "delete the task" → "Which task? #1 groceries or #2 laundry?"
2. **Missing required field**: "add task" → "What should the task title be?"
3. **Destructive action**: "delete all tasks" → "Are you sure? This will remove X tasks."
4. **Multiple matches**: "complete groceries" → "I found 2 tasks with 'groceries'. Which one?"

### Rationale
- Errors as strings let agent provide contextual help
- No HTTP exceptions for business logic = better UX
- Clarification reduces incorrect operations
- Never expose whether a task exists for other users (security)

---

## 6. Auth Propagation (JWT Reuse from Phase 2)

### Decision: Same JWT, Same Secret, Dependency Injection Chain

**JWT Flow:**
```
Frontend (Better Auth) → JWT → Backend → Validate → UserContext → Tools
```

**Implementation:**

```python
# FastAPI dependency chain
async def get_current_user(authorization: str = Header(...)) -> dict:
    token = authorization.replace("Bearer ", "")
    payload = jwt.decode(token, BETTER_AUTH_SECRET, algorithms=["HS256"])
    return {"user_id": payload["sub"], "email": payload.get("email")}

async def create_user_context(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserContext:
    return UserContext(user_id=user["user_id"], email=user["email"], db=db)
```

### JWT Claims Used
- `sub`: User ID (UUID from Better Auth)
- `email`: User email (for logging/display)
- `exp`: Expiration (30 days, per Phase 2 clarification)

### Rationale
- Single source of truth for auth (Better Auth)
- Shared secret enables backend verification
- Dependency injection = testable, type-safe
- No user table in backend (per Phase 2 decision)

---

## 7. OpenAI Agents SDK Integration

### Decision: Use `@function_tool` Decorator with Custom Context

**Agent Configuration:**

```python
from agents import Agent, function_tool, RunContextWrapper

@dataclass
class UserContext:
    user_id: str
    email: str
    db: AsyncSession

@function_tool
async def add_task(
    ctx: RunContextWrapper[UserContext],
    title: str,
    description: str | None = None
) -> str:
    """Add a new task for the user."""
    # ctx.context.user_id is guaranteed to be authenticated user
    ...

agent = Agent[UserContext](
    name="TodoAssistant",
    instructions="...",
    tools=[add_task, list_tasks, update_task, complete_task, delete_task],
    model="gpt-4o-mini"  # Cost-optimized for task management
)
```

### Model Selection
- **gpt-4o-mini**: Default for MVP (cost-effective, sufficient for task ops)
- **gpt-4o**: Available for complex disambiguation scenarios

### Rationale
- Type-safe context propagation via generics
- Decorator pattern matches FastAPI style
- Model flexibility via configuration

---

## 8. Frontend Integration (ChatKit)

### Decision: OpenAI ChatKit with Custom Backend

**Architecture:**
```
Next.js Frontend
    ↓ (JWT in header)
FastAPI /api/chat (SSE stream)
    ↓ (UserContext)
OpenAI Agent (with MCP tools)
    ↓ (tool calls)
Task Service Layer
    ↓
PostgreSQL
```

### ChatKit Configuration

```typescript
// Frontend: Simple ChatKit integration
<ChatKit
  endpoint="/api/chat/stream"
  headers={{ Authorization: `Bearer ${jwt}` }}
/>
```

### Rationale
- ChatKit handles UI/UX complexity
- SSE streaming for real-time responses
- Same auth header pattern as Phase 2 API calls

---

## 9. Observability Implementation

### Decision: Structured Logging with Request IDs

**Log Format:**
```json
{
  "timestamp": "2026-01-04T12:00:00Z",
  "request_id": "uuid",
  "user_id": "uuid",
  "event": "tool_call",
  "tool": "add_task",
  "status": "success",
  "latency_ms": 45
}
```

**Metrics Captured:**
- Request latency (total, AI service, DB)
- Tool call counts by type
- Error rates by category
- Active sessions

### Rationale
- Request IDs enable distributed tracing
- Structured logs = queryable in production
- Metrics inform optimization decisions

---

## 10. Technology Stack Confirmation

| Component | Technology | Version | Notes |
|-----------|------------|---------|-------|
| Backend Runtime | Python | 3.13+ | Per constitution |
| Backend Framework | FastAPI | Latest | Per constitution |
| ORM | SQLModel | Latest | Per constitution |
| Database | Neon PostgreSQL | Managed | Per constitution |
| AI Orchestration | OpenAI Agents SDK | Latest | Official SDK |
| AI Model | GPT-4o-mini | - | Cost-optimized |
| Frontend | Next.js + ChatKit | 16+ | Per constitution |
| Auth | Better Auth (JWT) | - | Reuse Phase 2 |

---

## Sources

### OpenAI Agents SDK & MCP
- OpenAI Agents SDK Documentation
- Model Context Protocol (MCP) Specification
- MCP Python SDK

### RAG & Conversation Patterns
- Building Context-Aware RAG with FastAPI
- RAG Chatbot with Conversational Memory

### FastAPI & Integration
- FastAPI OAuth2 with JWT
- FastAPI Dependencies with Yield
- OpenAI ChatKit Integration Guide
