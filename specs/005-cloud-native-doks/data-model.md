# Data Model: Advanced Cloud-Native Todo Chatbot (Phase V)

**Branch**: `005-cloud-native-doks` | **Date**: 2026-02-04
**Source**: [spec.md](./spec.md) Key Entities section

---

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────────┐
│      User       │       │   RecurrencePattern │
│─────────────────│       │─────────────────────│
│ id (PK)         │       │ id (PK)             │
│ email           │       │ frequency           │
│ name            │       │ interval            │
└────────┬────────┘       │ by_weekday          │
         │                │ by_monthday         │
         │ 1:N            │ end_date            │
         │                │ max_occurrences     │
         ▼                └──────────┬──────────┘
┌─────────────────┐                  │
│      Task       │◄─────────────────┘
│─────────────────│       0..1
│ id (PK)         │
│ user_id (FK)    │       ┌─────────────────────┐
│ title           │       │ NotificationPref    │
│ description     │       │─────────────────────│
│ status          │       │ id (PK)             │
│ due_date        │       │ user_id (FK)        │
│ reminder_offset │       │ email_enabled       │
│ recurrence_id   │──────►│ push_enabled        │
│ parent_task_id  │       │ quiet_hours_start   │
│ created_at      │       │ quiet_hours_end     │
│ updated_at      │       └─────────────────────┘
└─────────────────┘
         │
         │ generates
         ▼
┌─────────────────┐       ┌─────────────────────┐
│   TaskEvent     │       │   ReminderEvent     │
│─────────────────│       │─────────────────────│
│ id (PK)         │       │ id (PK)             │
│ type            │       │ task_id (FK)        │
│ task_id         │       │ user_id             │
│ user_id         │       │ scheduled_time      │
│ data            │       │ channels            │
│ correlation_id  │       │ status              │
│ timestamp       │       │ created_at          │
└─────────────────┘       └─────────────────────┘
```

---

## Entity Definitions

### Task (Extended from Phase IV)

**Purpose**: Core task entity with recurrence support added.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Unique task identifier |
| `user_id` | UUID | FK → User, NOT NULL | Owner of the task |
| `title` | VARCHAR(255) | NOT NULL | Task title |
| `description` | TEXT | NULLABLE | Detailed description |
| `status` | ENUM | NOT NULL, DEFAULT 'pending' | pending, completed, deleted |
| `due_date` | TIMESTAMP | NULLABLE | When task is due |
| `reminder_offset` | INTEGER | DEFAULT 30 | Minutes before due_date for reminder |
| `recurrence_id` | UUID | FK → RecurrencePattern, NULLABLE | Recurrence configuration |
| `parent_task_id` | UUID | FK → Task (self), NULLABLE | Original task if this is a recurring instance |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last modification timestamp |

**Indexes**:
- `idx_task_user_id` on `user_id`
- `idx_task_due_date` on `due_date` WHERE `status = 'pending'`
- `idx_task_parent` on `parent_task_id`

**SQLModel Definition**:
```python
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    DELETED = "deleted"

class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    title: str = Field(max_length=255)
    description: str | None = None
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    due_date: datetime | None = None
    reminder_offset: int = Field(default=30)  # minutes
    recurrence_id: UUID | None = Field(default=None, foreign_key="recurrencepattern.id")
    parent_task_id: UUID | None = Field(default=None, foreign_key="task.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    recurrence: "RecurrencePattern" = Relationship(back_populates="tasks")
    parent_task: "Task" = Relationship(
        sa_relationship_kwargs={"remote_side": "Task.id"}
    )
```

---

### RecurrencePattern (NEW)

**Purpose**: Defines repeat schedule for recurring tasks (FR-013).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Unique pattern identifier |
| `frequency` | ENUM | NOT NULL | daily, weekly, monthly, custom |
| `interval` | INTEGER | NOT NULL, DEFAULT 1 | Every N frequency units |
| `by_weekday` | ARRAY[INTEGER] | NULLABLE | Days of week (0=Mon, 6=Sun) |
| `by_monthday` | INTEGER | NULLABLE | Day of month (1-31) |
| `end_date` | TIMESTAMP | NULLABLE | When recurrence stops |
| `max_occurrences` | INTEGER | NULLABLE | Max instances to create |
| `rrule_string` | VARCHAR(500) | NULLABLE | RFC 5545 RRULE for complex patterns |

**Validation Rules**:
- Either `end_date` OR `max_occurrences` MUST be set (not both, not neither)
- `interval` must be >= 1
- `by_weekday` values must be 0-6
- `by_monthday` must be 1-31

**SQLModel Definition**:
```python
from enum import Enum

class RecurrenceFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

class RecurrencePattern(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    frequency: RecurrenceFrequency
    interval: int = Field(default=1, ge=1)
    by_weekday: list[int] | None = Field(default=None, sa_column=Column(ARRAY(Integer)))
    by_monthday: int | None = Field(default=None, ge=1, le=31)
    end_date: datetime | None = None
    max_occurrences: int | None = Field(default=None, ge=1)
    rrule_string: str | None = Field(default=None, max_length=500)

    # Relationships
    tasks: list["Task"] = Relationship(back_populates="recurrence")

    @validator("end_date", "max_occurrences", pre=True, always=True)
    def validate_end_condition(cls, v, values):
        end_date = values.get("end_date")
        max_occ = values.get("max_occurrences")
        if end_date is None and max_occ is None:
            raise ValueError("Either end_date or max_occurrences must be set")
        if end_date is not None and max_occ is not None:
            raise ValueError("Cannot set both end_date and max_occurrences")
        return v
```

---

### TaskEvent (NEW - Event Sourcing)

**Purpose**: Represents domain events for task operations (FR-001 to FR-003).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Event identifier (idempotency key) |
| `type` | ENUM | NOT NULL | created, updated, deleted, completed |
| `task_id` | UUID | NOT NULL | Reference to affected task |
| `user_id` | UUID | NOT NULL | User who triggered the event |
| `data` | JSONB | NOT NULL | Task snapshot at event time |
| `correlation_id` | VARCHAR(100) | NOT NULL | Dapr trace correlation ID |
| `timestamp` | TIMESTAMP | NOT NULL, DEFAULT NOW() | When event occurred |

**Event Types**:
- `task.created` - New task created
- `task.updated` - Task fields modified
- `task.deleted` - Task removed
- `task.completed` - Task marked as done (triggers recurring logic)

**CloudEvents Envelope** (handled by Dapr):
```python
from pydantic import BaseModel

class TaskEventData(BaseModel):
    task_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    due_date: datetime | None
    user_id: UUID
    recurrence: dict | None  # Recurrence pattern if exists
    parent_task_id: UUID | None

class TaskEvent(BaseModel):
    # CloudEvents attributes (auto-populated by Dapr)
    specversion: str = "1.0"
    id: UUID  # Event ID
    source: str = "https://api.todo.example.com/tasks"
    type: str  # e.g., "com.todo.task.created"
    datacontenttype: str = "application/json"
    subject: str  # e.g., "tasks/{task_id}"
    time: datetime

    # Event payload
    data: TaskEventData
```

---

### ReminderEvent (NEW)

**Purpose**: Scheduled notification trigger (FR-016 to FR-019).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Reminder identifier |
| `task_id` | UUID | FK → Task, NOT NULL | Task being reminded |
| `user_id` | UUID | NOT NULL | User to notify |
| `scheduled_time` | TIMESTAMP | NOT NULL | When to send reminder |
| `channels` | ARRAY[VARCHAR] | NOT NULL | ['email', 'push'] |
| `status` | ENUM | NOT NULL, DEFAULT 'pending' | pending, sent, failed, cancelled |
| `created_at` | TIMESTAMP | NOT NULL | When reminder was scheduled |

**State Transitions**:
```
pending → sent (notification delivered)
pending → failed (delivery error, will retry)
pending → cancelled (task deleted/completed before reminder)
```

---

### NotificationPreference (NEW)

**Purpose**: User settings for notification delivery (FR-018).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Preference identifier |
| `user_id` | UUID | FK → User, UNIQUE, NOT NULL | User reference |
| `email_enabled` | BOOLEAN | NOT NULL, DEFAULT true | Email notifications |
| `push_enabled` | BOOLEAN | NOT NULL, DEFAULT true | Push notifications (simulated) |
| `quiet_hours_start` | TIME | NULLABLE | Start of quiet period |
| `quiet_hours_end` | TIME | NULLABLE | End of quiet period |
| `default_reminder_offset` | INTEGER | DEFAULT 30 | Default minutes before due |

---

### ProcessedEvent (NEW - Idempotency)

**Purpose**: Track processed events for deduplication (FR-015).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `event_id` | UUID | PK, NOT NULL | CloudEvents ID |
| `consumer_id` | VARCHAR(100) | PK, NOT NULL | Service that processed it |
| `processed_at` | TIMESTAMP | NOT NULL | When event was handled |

**Usage**: Before processing any event, check if `(event_id, consumer_id)` exists. If yes, skip processing.

```python
async def process_event_idempotently(event_id: UUID, consumer_id: str, handler: Callable):
    """Idempotent event processing pattern"""
    async with db.transaction():
        existing = await ProcessedEvent.get_or_none(
            event_id=event_id,
            consumer_id=consumer_id
        )
        if existing:
            logger.info(f"Event {event_id} already processed by {consumer_id}, skipping")
            return

        await handler()

        await ProcessedEvent.create(
            event_id=event_id,
            consumer_id=consumer_id,
            processed_at=datetime.utcnow()
        )
```

---

## Migration Strategy

### New Tables (Phase V)
1. `recurrence_pattern` - Create first (referenced by tasks)
2. `notification_preference` - Independent, can create in parallel
3. `processed_event` - Independent, can create in parallel

### Modified Tables
1. `task` - Add columns:
   - `recurrence_id` (FK, nullable)
   - `parent_task_id` (FK, nullable)
   - `reminder_offset` (integer, default 30)

### Migration Script
```sql
-- Phase V Migration: Event-Driven Extensions

-- 1. Create recurrence_pattern table
CREATE TABLE recurrence_pattern (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('daily', 'weekly', 'monthly', 'custom')),
    interval INTEGER NOT NULL DEFAULT 1 CHECK (interval >= 1),
    by_weekday INTEGER[],
    by_monthday INTEGER CHECK (by_monthday >= 1 AND by_monthday <= 31),
    end_date TIMESTAMP,
    max_occurrences INTEGER CHECK (max_occurrences >= 1),
    rrule_string VARCHAR(500),
    CONSTRAINT end_condition_check CHECK (
        (end_date IS NOT NULL AND max_occurrences IS NULL) OR
        (end_date IS NULL AND max_occurrences IS NOT NULL)
    )
);

-- 2. Add recurrence columns to task
ALTER TABLE task
    ADD COLUMN recurrence_id UUID REFERENCES recurrence_pattern(id),
    ADD COLUMN parent_task_id UUID REFERENCES task(id),
    ADD COLUMN reminder_offset INTEGER NOT NULL DEFAULT 30;

CREATE INDEX idx_task_parent ON task(parent_task_id) WHERE parent_task_id IS NOT NULL;

-- 3. Create notification_preference table
CREATE TABLE notification_preference (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES "user"(id),
    email_enabled BOOLEAN NOT NULL DEFAULT true,
    push_enabled BOOLEAN NOT NULL DEFAULT true,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    default_reminder_offset INTEGER NOT NULL DEFAULT 30
);

-- 4. Create processed_event table (idempotency)
CREATE TABLE processed_event (
    event_id UUID NOT NULL,
    consumer_id VARCHAR(100) NOT NULL,
    processed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (event_id, consumer_id)
);

CREATE INDEX idx_processed_event_time ON processed_event(processed_at);
```

---

## Topic Schema (Redpanda)

| Topic | Partitions | Retention | Producers | Consumers |
|-------|------------|-----------|-----------|-----------|
| `task-events` | 6 | 7 days | backend | recurring-task, notification, websocket |
| `reminders` | 3 | 1 day | notification | notification (scheduled delivery) |
| `task-updates` | 6 | 1 day | backend | websocket (real-time sync) |

**Partition Key Strategy**:
- `task-events`: Partition by `user_id` (ensures ordering per user)
- `reminders`: Partition by `user_id`
- `task-updates`: Partition by `user_id`
