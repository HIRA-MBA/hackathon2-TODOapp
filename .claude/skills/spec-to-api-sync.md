# Skill: Spec-to-API Sync

## Description

Generate FastAPI routes and Pydantic models directly from `specs/api/rest-endpoints.md`. Keeps code in sync with spec changes.

## Trigger

Invoke this skill when:
- Creating API endpoints from specs
- User asks to "generate API" or "sync API with spec"
- After API spec is created and before implementation
- When spec changes and code needs updating

## Core Rules (Non-Negotiable)

1. **Do not invent endpoints** - Only generate routes explicitly defined in the spec
2. **Exact match required** - Route paths, HTTP methods, and schemas MUST exactly match specs
3. **Sync on spec change only** - Update code only when specs change; never modify without spec update

---

## Execution Flow

### Phase 1: Load API Specification

1. **Locate spec file**:
   - Primary: `specs/api/rest-endpoints.md`
   - Fallback: `specs/<feature>/contracts/api.md`
   - If not found: HALT with error

2. **Parse endpoint definitions**:

   ```markdown
   ## POST /api/v1/todos

   **Description**: Create a new todo item
   **Auth**: Required (JWT)

   ### Request Body
   | Field | Type | Required | Constraints |
   |-------|------|----------|-------------|
   | title | string | yes | 1-200 chars |

   ### Response 201
   | Field | Type | Description |
   |-------|------|-------------|
   | id | uuid | Created todo ID |
   ```

3. **Build endpoint registry** (YAML format)

### Phase 2: Generate Pydantic Models

Create schema file at `backend/src/schemas/<resource>.py`:

```python
"""
Auto-generated from: specs/api/rest-endpoints.md
DO NOT EDIT MANUALLY - Run spec-to-api-sync skill to regenerate
"""
from pydantic import BaseModel, Field
from uuid import UUID

class TodoCreate(BaseModel):
    """Request body for POST /api/v1/todos"""
    title: str = Field(..., min_length=1, max_length=200)

class TodoResponse(BaseModel):
    """Response body for POST /api/v1/todos (201)"""
    id: UUID
    title: str

    model_config = {"from_attributes": True}
```

**Type mapping**:
| Spec Type | Python Type |
|-----------|-------------|
| string | str |
| integer | int |
| uuid | UUID |
| datetime | datetime |
| array[T] | list[T] |
| email | EmailStr |

### Phase 3: Generate FastAPI Routes

Create router at `backend/src/api/routes/<resource>.py`:

```python
"""
Auto-generated from: specs/api/rest-endpoints.md
DO NOT EDIT MANUALLY
"""
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/api/v1/todos", tags=["todos"])

@router.post(
    "",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new todo item"
)
async def create_todo(
    data: TodoCreate,
    current_user: User = Depends(get_current_user),
    service: TodoService = Depends()
) -> TodoResponse:
    return await service.create(data, user_id=current_user.id)
```

### Phase 4: Register Routes

Update `backend/src/api/router.py`:

```python
from src.api.routes import todos

api_router = APIRouter()
api_router.include_router(todos.router)
```

### Phase 5: Diff Detection & Sync

Compare spec with existing code:

```
CHANGES DETECTED:

+ ADDED: DELETE /api/v1/todos/{id}
~ MODIFIED: POST /api/v1/todos (added 'due_date' field)
- REMOVED: PATCH /api/v1/todos/{id}/archive

Proceed with sync? [y/N]
```

**Safe sync rules**:
- ADDED: Generate new code
- MODIFIED: Update existing, preserve service logic
- REMOVED: Comment out with deprecation warning

### Phase 6: Validation

After generation:
1. Verify Pydantic models load
2. Verify routes register
3. Cross-reference spec coverage

---

## Output

After execution, produce:
1. Sync Summary (files created/updated)
2. Endpoints synced list
3. Validation status
4. Any warnings or manual actions
