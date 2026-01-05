# Skill: MCP Tool Generator

## Description

Convert backend CRUD logic into stateless MCP tools compatible with OpenAI Agents SDK. All state persists to the database.

## Trigger

Invoke this skill when:
- Creating MCP tools for AI agents
- User asks to "generate MCP tools" or "create agent tools"
- After services are implemented and before AI integration
- When adding new CRUD operations to expose as tools

## Core Rules (Non-Negotiable)

1. **Parameter schema match** - Tool parameters MUST match database schema and specs exactly
2. **Stateless tools** - Tools MUST NOT maintain in-memory state between invocations
3. **Database persistence** - All state MUST be persisted to and retrieved from the database
4. **User scoping** - All operations MUST be scoped by `user_id` from the authenticated context

---

## Execution Flow

### Phase 1: Load Source Context

1. **Identify target resource**:
   - Scan `backend/src/services/` for available services
   - Resource examples: `todo`, `user`, `task`, `project`

2. **Load specification files**:
   - **REQUIRED**: `specs/<feature>/data-model.md` for entity schema
   - **OPTIONAL**: `specs/<feature>/spec.md` for acceptance criteria
   - **OPTIONAL**: `backend/src/models/<resource>.py` for SQLModel definitions

3. **Extract CRUD operations** from service layer:

   ```python
   class TodoService:
       async def create(self, data: TodoCreate, user_id: UUID) -> Todo
       async def get(self, id: UUID, user_id: UUID) -> Todo | None
       async def list(self, user_id: UUID, **filters) -> list[Todo]
       async def update(self, id: UUID, data: TodoUpdate, user_id: UUID) -> Todo
       async def delete(self, id: UUID, user_id: UUID) -> bool
   ```

### Phase 2: Build Tool Registry

```yaml
mcp_tools:
  - name: create_todo
    description: Create a new todo item for the current user
    operation: CREATE
    service_method: TodoService.create
    parameters:
      - name: title
        type: string
        required: true
        constraints: {min_length: 1, max_length: 200}
    auth: required
    stateless: true
```

### Phase 3: Generate MCP Tool Definitions

Create tool file at `backend/src/mcp/tools/<resource>.py`:

```python
"""
MCP Tools: Todo Resource
Auto-generated - DO NOT EDIT MANUALLY

Stateless: YES - All state persisted to database
User Scoping: YES - All queries filtered by user_id
"""
from pydantic import BaseModel, Field
from mcp.types import Tool, TextContent

class CreateTodoParams(BaseModel):
    """Parameters for create_todo tool."""
    title: str = Field(..., min_length=1, max_length=200)
    priority: int = Field(default=3, ge=1, le=5)

TOOLS: list[Tool] = [
    Tool(
        name="create_todo",
        description="Create a new todo item for the current user.",
        inputSchema=CreateTodoParams.model_json_schema()
    ),
]
```

### Phase 4: Generate Tool Handlers (Stateless)

```python
async def handle_create_todo(
    params: dict,
    user_id: UUID
) -> list[TextContent]:
    """
    STATELESS: Creates record in database, no in-memory state.
    USER SCOPED: Todo is associated with user_id.
    """
    validated = CreateTodoParams.model_validate(params)

    async with get_session() as session:
        service = TodoService(session)
        todo = await service.create(
            title=validated.title,
            priority=validated.priority,
            user_id=user_id  # REQUIRED: User scoping
        )
        await session.commit()

    return [TextContent(
        type="text",
        text=f"Created todo: {todo.id} - {todo.title}"
    )]
```

### Phase 5: Generate MCP Server Registration

Update `backend/src/mcp/server.py`:

```python
from mcp.server import Server
from src.mcp.tools.todo import TOOLS as TODO_TOOLS, dispatch_tool

mcp_server = Server("hackathon-todo-mcp")

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    return TODO_TOOLS

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict, user_id: UUID):
    return await dispatch_tool(name, arguments, user_id)

def get_openai_tools_schema() -> list[dict]:
    """Export for OpenAI Agents SDK."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        }
        for tool in TODO_TOOLS
    ]
```

### Phase 6: Statelessness Verification

Detect forbidden patterns:

```python
# ❌ FORBIDDEN
class TodoTools:
    cache = {}  # Class-level state

_todo_cache = {}  # Global state

# ✓ ALLOWED
async def handle_list_todos(params, user_id):
    todos = []  # Local, not persisted between calls
```

**Verification report**:
```
Tool: create_todo
- No class-level attributes: ✓
- No global state references: ✓
- Database commit on each call: ✓
- Session scoped to request: ✓
Status: STATELESS ✓
```

### Phase 7: User Scoping Verification

```
Tool: create_todo
- user_id parameter: ✓
- Database insert includes user_id: ✓
Status: SCOPED ✓

Tool: list_todos
- user_id parameter: ✓
- WHERE clause includes user_id: ✓
Status: SCOPED ✓
```

---

## Output

After execution, produce:
1. Generation Summary (files, tool count)
2. Tools generated list (name, operation)
3. Statelessness verification (PASSED/FAILED)
4. User scoping verification (PASSED/FAILED)
5. Schema alignment check
6. OpenAI Agents SDK integration snippet
