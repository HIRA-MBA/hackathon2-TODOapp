# Data Model: Phase II - Full-Stack Todo Web Application

**Branch**: `002-fullstack-todo-web`
**Date**: 2026-01-02
**Source**: spec.md Key Entities section

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────┐
│                     BETTER AUTH                      │
│  (External - manages User entity)                    │
│  ┌─────────────────────────────────┐                │
│  │ User (managed by Better Auth)   │                │
│  │ ─────────────────────────────── │                │
│  │ id: UUID (PK)                   │                │
│  │ email: VARCHAR(255)             │                │
│  │ password_hash: VARCHAR(255)     │                │
│  │ created_at: TIMESTAMP           │                │
│  └─────────────────────────────────┘                │
└─────────────────────────────────────────────────────┘
                         │
                         │ user_id (referenced from JWT)
                         │ (no foreign key - external system)
                         ▼
┌─────────────────────────────────────────────────────┐
│                   BACKEND DATABASE                   │
│  (Neon PostgreSQL - backend owns)                   │
│  ┌─────────────────────────────────┐                │
│  │ Task                             │                │
│  │ ─────────────────────────────── │                │
│  │ id: UUID (PK)                   │                │
│  │ user_id: UUID (indexed)         │◄── From JWT    │
│  │ title: VARCHAR(200)             │                │
│  │ description: TEXT (nullable)    │                │
│  │ completed: BOOLEAN              │                │
│  │ created_at: TIMESTAMP           │                │
│  │ updated_at: TIMESTAMP           │                │
│  └─────────────────────────────────┘                │
└─────────────────────────────────────────────────────┘
```

---

## Entities

### Task (Backend-owned)

The primary entity managed by the FastAPI backend. Each task belongs to exactly one user (referenced by user_id from JWT claims).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique task identifier |
| `user_id` | UUID | NOT NULL, INDEXED | Owner's ID (from Better Auth JWT) |
| `title` | VARCHAR(200) | NOT NULL | Task title (max 200 chars) |
| `description` | TEXT | NULLABLE | Optional task description (max 2000 chars app-enforced) |
| `completed` | BOOLEAN | NOT NULL, DEFAULT false | Completion status |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Last modification timestamp |

### User (Better Auth-owned)

Managed entirely by Better Auth. The backend does NOT create a user table; it only references `user_id` from validated JWT tokens.

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Extracted from JWT `sub` claim |
| `email` | VARCHAR(255) | Available in JWT payload for display |

---

## Indexes

| Table | Index Name | Columns | Type | Purpose |
|-------|------------|---------|------|---------|
| task | `idx_task_user_id` | user_id | B-tree | Filter tasks by owner |
| task | `idx_task_user_created` | user_id, created_at DESC | B-tree | Ordered task listing |

---

## Validation Rules

### Task Title
- **Required**: Must be non-empty
- **Max Length**: 200 characters
- **Trim**: Leading/trailing whitespace stripped
- **Validation**: Reject whitespace-only strings

### Task Description
- **Optional**: Can be null or empty
- **Max Length**: 2000 characters (application-enforced)
- **Trim**: Leading/trailing whitespace stripped

### User ID
- **Source**: JWT `sub` claim only
- **Never**: Accepted from client input
- **Format**: UUID string from Better Auth

---

## State Transitions

### Task Completion
```
                    toggle()
    ┌──────────────────────────────────┐
    │                                  │
    ▼                                  │
┌─────────┐     toggle()      ┌────────────┐
│INCOMPLETE│ ─────────────────►│  COMPLETE  │
│completed │                   │ completed  │
│ = false  │◄───────────────── │  = true    │
└─────────┘     toggle()      └────────────┘
```

### Task Lifecycle
```
Created ──► Active ──► (Updated)* ──► Deleted
   │           │            │
   │           ▼            │
   │      Completed ────────┘
   │           │
   └───────────┴──────────────────► Deleted
```

---

## SQLModel Definition (Reference)

```python
from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class Task(SQLModel, table=True):
    __tablename__ = "task"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True, nullable=False)
    title: str = Field(max_length=200, nullable=False)
    description: str | None = Field(default=None)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## Database Schema (SQL)

```sql
-- Task table
CREATE TABLE task (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    completed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_task_user_id ON task(user_id);
CREATE INDEX idx_task_user_created ON task(user_id, created_at DESC);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_task_updated_at
    BEFORE UPDATE ON task
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Data Isolation Strategy

### Query Pattern (All Queries Must Include user_id)

```python
# List tasks - ALWAYS filter by user_id
async def get_user_tasks(session: AsyncSession, user_id: UUID) -> list[Task]:
    stmt = select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()

# Get single task - ALWAYS include user_id in WHERE
async def get_task(session: AsyncSession, task_id: UUID, user_id: UUID) -> Task | None:
    stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

# Update task - ALWAYS include user_id in WHERE
async def update_task(session: AsyncSession, task_id: UUID, user_id: UUID, **updates) -> Task | None:
    stmt = (
        update(Task)
        .where(Task.id == task_id, Task.user_id == user_id)
        .values(**updates, updated_at=datetime.utcnow())
        .returning(Task)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

# Delete task - ALWAYS include user_id in WHERE
async def delete_task(session: AsyncSession, task_id: UUID, user_id: UUID) -> bool:
    stmt = delete(Task).where(Task.id == task_id, Task.user_id == user_id)
    result = await session.execute(stmt)
    return result.rowcount > 0
```

### Security Invariants

1. **user_id source**: Only from validated JWT `sub` claim
2. **No unscoped queries**: All queries MUST include user_id filter
3. **Return 404 not 403**: Prevents user enumeration attacks
4. **No user_id in request body**: Never accept from client

---

## Pydantic Schemas (API Layer)

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

# Request schemas (input)
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)

class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)

# Response schemas (output)
class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    count: int
```

---

## Notes

- **No User Table**: Backend does not store user data; Better Auth manages users
- **UUID Format**: All IDs are UUIDs for security and scalability
- **Timezone**: All timestamps are TIMESTAMPTZ (timezone-aware)
- **Soft Delete**: Not implemented (hard delete per spec); can be added later
- **Ordering**: Tasks returned newest-first (created_at DESC) per spec clarification
