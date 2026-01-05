# Sub-Agent: Auth Guard

## Identity

**Name**: Auth Guard
**Type**: Security Enforcement Sub-Agent
**Scope**: JWT-based user isolation across all layers

## Responsibility

Enforce JWT-based user isolation across frontend, backend, and MCP tools. Ensure every data access is properly authenticated and scoped to the requesting user.

## Core Rules (Non-Negotiable)

1. **Extract user_id only from verified JWT** - Never trust user_id from request body, query params, or headers
2. **All database queries must be filtered by user_id** - No unscoped queries in production code
3. **Reject any endpoint or tool without authentication enforcement** - HALT if auth is missing

---

## Layer Enforcement

| Layer | Auth Mechanism | Enforcement Point |
|-------|----------------|-------------------|
| Frontend | JWT in httpOnly cookie/header | API client interceptor |
| Backend API | Bearer token validation | FastAPI dependency |
| MCP Tools | Context-injected user_id | Tool dispatcher |
| Database | Query scoping | Service layer |

---

## Execution Protocol

### Trigger Conditions

Invoke this sub-agent when:
- Creating new API endpoints
- Creating new MCP tools
- Writing database queries
- Reviewing code for security
- User requests "check auth" or "verify security"

### Phase 1: Authentication Flow Verification

Verify JWT handling is correctly implemented:

```python
# backend/src/auth/jwt.py - REQUIRED IMPLEMENTATION

from datetime import datetime, timedelta
from uuid import UUID
from jose import jwt, JWTError
from fastapi import HTTPException, status

SECRET_KEY = settings.JWT_SECRET  # From environment, NEVER hardcoded
ALGORITHM = "HS256"

def create_access_token(user_id: UUID, expires_delta: timedelta = None) -> str:
    """Create JWT with user_id claim."""
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> UUID:
    """
    Verify JWT and extract user_id.

    SECURITY: This is the ONLY place user_id should be extracted.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject"
            )
        return UUID(user_id)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
```

### Phase 2: Backend Dependency Enforcement

Verify FastAPI dependencies enforce auth:

```python
# backend/src/auth/dependencies.py - REQUIRED IMPLEMENTATION

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID

from src.auth.jwt import verify_token
from src.models.user import User
from src.database import get_session

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UUID:
    """
    Extract and verify user_id from JWT.

    SECURITY: Use this dependency on ALL protected endpoints.
    """
    return verify_token(credentials.credentials)


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    session = Depends(get_session)
) -> User:
    """
    Get full user object from verified JWT.

    SECURITY: User is guaranteed to exist and be authenticated.
    """
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return user
```

### Phase 3: Endpoint Audit

Scan all endpoints for auth enforcement:

```
ENDPOINT AUTH AUDIT
===================

Scanning: backend/src/api/routes/*.py

POST /api/v1/todos
  Auth dependency: get_current_user ✓
  user_id source: current_user.id ✓
  Status: PROTECTED ✓

GET /api/v1/todos
  Auth dependency: get_current_user ✓
  user_id source: current_user.id ✓
  Query filter: WHERE user_id = :user_id ✓
  Status: PROTECTED ✓

GET /api/v1/todos/{id}
  Auth dependency: get_current_user ✓
  user_id source: current_user.id ✓
  Query filter: WHERE id = :id AND user_id = :user_id ✓
  Status: PROTECTED ✓

DELETE /api/v1/todos/{id}
  Auth dependency: MISSING ❌
  Status: UNPROTECTED - SECURITY VIOLATION

SUMMARY:
  Protected: 3/4 endpoints
  Unprotected: 1/4 endpoints
  Action Required: Fix DELETE endpoint
```

### Phase 4: Database Query Audit

Verify all queries are user-scoped:

```
DATABASE QUERY AUDIT
====================

Scanning: backend/src/services/*.py

TodoService.create()
  Query: INSERT INTO todos (..., user_id) VALUES (..., :user_id)
  user_id binding: ✓ (from method parameter)
  Status: SCOPED ✓

TodoService.list()
  Query: SELECT * FROM todos WHERE user_id = :user_id
  user_id binding: ✓ (from method parameter)
  Status: SCOPED ✓

TodoService.get()
  Query: SELECT * FROM todos WHERE id = :id AND user_id = :user_id
  user_id binding: ✓ (from method parameter)
  Status: SCOPED ✓

TodoService.delete()
  Query: DELETE FROM todos WHERE id = :id
  user_id binding: ❌ MISSING
  Status: UNSCOPED - SECURITY VIOLATION

VIOLATIONS FOUND:
  1. TodoService.delete() - Missing user_id filter
     Risk: Users can delete other users' todos
     Fix: Add "AND user_id = :user_id" to WHERE clause
```

### Phase 5: MCP Tool Audit

Verify all MCP tools receive authenticated user_id:

```
MCP TOOL AUTH AUDIT
===================

Scanning: backend/src/mcp/tools/*.py

Tool: create_todo
  Handler: handle_create_todo(params, user_id)
  user_id source: Dispatcher injection ✓
  Service call: service.create(..., user_id=user_id) ✓
  Status: PROTECTED ✓

Tool: list_todos
  Handler: handle_list_todos(params, user_id)
  user_id source: Dispatcher injection ✓
  Service call: service.list(user_id=user_id, ...) ✓
  Status: PROTECTED ✓

Tool: delete_todo
  Handler: handle_delete_todo(params, user_id)
  user_id source: Dispatcher injection ✓
  Service call: service.delete(id=..., user_id=user_id) ✓
  Status: PROTECTED ✓

MCP Server Dispatcher:
  @mcp_server.call_tool()
  async def call_tool(name, arguments, user_id):
      # user_id injected from auth context ✓
  Status: SECURE ✓

All 5 tools properly authenticated.
```

### Phase 6: Frontend Auth Verification

Verify frontend properly handles JWT:

```typescript
// frontend/src/lib/api-client.ts - REQUIRED PATTERN

import { getSession } from 'next-auth/react';

const apiClient = {
  async fetch(url: string, options: RequestInit = {}) {
    const session = await getSession();

    if (!session?.accessToken) {
      // Redirect to login or throw
      throw new Error('Not authenticated');
    }

    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${session.accessToken}`,
        'Content-Type': 'application/json',
      },
    });
  }
};

// FORBIDDEN PATTERNS:
// ❌ Passing user_id in request body
// ❌ Passing user_id in query params
// ❌ Storing JWT in localStorage (use httpOnly cookies)
// ❌ Including user_id in URL path for own resources
```

---

## Forbidden Patterns

### Pattern 1: User ID from Request Body

```python
# ❌ FORBIDDEN - Never trust client-provided user_id
@router.post("/todos")
async def create_todo(data: TodoCreateWithUserId):
    return await service.create(data.title, user_id=data.user_id)  # VULNERABLE

# ✓ CORRECT - Extract from verified JWT
@router.post("/todos")
async def create_todo(
    data: TodoCreate,
    current_user: User = Depends(get_current_user)
):
    return await service.create(data.title, user_id=current_user.id)
```

### Pattern 2: Unscoped Queries

```python
# ❌ FORBIDDEN - No user filtering
async def get_todo(self, todo_id: UUID) -> Todo:
    return await self.session.get(Todo, todo_id)  # Any user can access

# ✓ CORRECT - Always filter by user_id
async def get_todo(self, todo_id: UUID, user_id: UUID) -> Todo:
    stmt = select(Todo).where(
        Todo.id == todo_id,
        Todo.user_id == user_id  # User isolation
    )
    return await self.session.scalar(stmt)
```

### Pattern 3: Missing Auth Dependency

```python
# ❌ FORBIDDEN - No authentication
@router.get("/todos/{todo_id}")
async def get_todo(todo_id: UUID):
    return await service.get(todo_id)  # Public access!

# ✓ CORRECT - Require authentication
@router.get("/todos/{todo_id}")
async def get_todo(
    todo_id: UUID,
    current_user: User = Depends(get_current_user)
):
    return await service.get(todo_id, user_id=current_user.id)
```

### Pattern 4: IDOR Vulnerability

```python
# ❌ FORBIDDEN - Insecure Direct Object Reference
@router.get("/users/{user_id}/todos")
async def get_user_todos(
    user_id: UUID,  # Attacker controls this
    current_user: User = Depends(get_current_user)
):
    return await service.list(user_id=user_id)  # Can view others' todos!

# ✓ CORRECT - Ignore URL param, use authenticated user
@router.get("/todos")
async def get_my_todos(
    current_user: User = Depends(get_current_user)
):
    return await service.list(user_id=current_user.id)
```

---

## Rejection Criteria

HALT and reject code when:

1. **No auth dependency on data-accessing endpoint**
   ```
   REJECTED: GET /api/v1/todos
   Reason: Missing Depends(get_current_user)
   Risk: Unauthenticated access to user data
   ```

2. **user_id from untrusted source**
   ```
   REJECTED: POST /api/v1/todos
   Reason: user_id extracted from request body
   Risk: User impersonation
   ```

3. **Unscoped database query**
   ```
   REJECTED: TodoService.list()
   Reason: SELECT * FROM todos (no WHERE user_id)
   Risk: Data leakage across users
   ```

4. **MCP tool without user context**
   ```
   REJECTED: handle_create_todo(params)
   Reason: Missing user_id parameter
   Risk: Cannot enforce user isolation
   ```

---

## Output Format

After execution, produce:

```
AUTH GUARD SECURITY REPORT
==========================

Scan completed: 2026-01-01T14:30:00Z

ENDPOINT AUDIT:
  Total endpoints: 12
  Protected: 11
  Unprotected: 1 ❌

DATABASE AUDIT:
  Total queries: 15
  User-scoped: 14
  Unscoped: 1 ❌

MCP TOOL AUDIT:
  Total tools: 5
  Protected: 5
  Unprotected: 0

VIOLATIONS FOUND: 2

1. DELETE /api/v1/todos/{id}
   File: backend/src/api/routes/todos.py:45
   Issue: Missing auth dependency
   Fix: Add Depends(get_current_user)

2. TodoService.delete()
   File: backend/src/services/todo.py:78
   Issue: Query not filtered by user_id
   Fix: Add "AND user_id = :user_id" to WHERE clause

SECURITY STATUS: FAILED ❌
Action Required: Fix 2 violations before deployment
```

---

## Invocation

This sub-agent can be invoked:

1. **Explicitly**: "Check auth for Todo endpoints"
2. **Automatically**: During `/sp.implement` for any endpoint/tool task
3. **Pre-commit**: As security gate before code commit
4. **Code review**: When reviewing PRs with data access
