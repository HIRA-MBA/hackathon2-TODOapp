# Todo Backend API

FastAPI backend for the Full-Stack Todo Web Application with event-driven architecture (Phase V).

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your Neon database URL and Better Auth secret.

4. Run migrations:
   ```bash
   uv run alembic upgrade head
   ```

5. Start the server:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

The API will be available at http://localhost:8000

### Running with Dapr (Phase V Event-Driven)

```bash
dapr run --app-id backend --app-port 8000 --dapr-http-port 3500 \
  --components-path ../dapr/components -- \
  uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Core Task CRUD
- `GET /api/tasks` - List all tasks (requires auth)
- `POST /api/tasks` - Create a task (requires auth)
- `GET /api/tasks/{id}` - Get a task (requires auth)
- `PUT /api/tasks/{id}` - Update a task (requires auth)
- `PATCH /api/tasks/{id}/toggle` - Toggle task completion (requires auth)
- `POST /api/tasks/{id}/complete` - Complete task, triggers recurring logic (requires auth)
- `DELETE /api/tasks/{id}` - Delete a task (requires auth)

### Recurrence (Phase V)
- `GET /api/tasks/{id}/recurrence` - Get recurrence pattern
- `PUT /api/tasks/{id}/recurrence` - Set/update recurrence pattern
- `DELETE /api/tasks/{id}/recurrence` - Remove recurrence
- `GET /api/tasks/{id}/instances` - List recurring task instances

### Notifications (Phase V)
- `GET /api/notifications/preferences` - Get notification preferences
- `PUT /api/notifications/preferences` - Update notification preferences
- `DELETE /api/notifications/preferences` - Reset to defaults

### System
- `GET /api/health` - Liveness probe
- `GET /api/health/ready` - Readiness probe (checks DB + Dapr)

## Architecture (Phase V)

### Event-Driven Components
- **Event Publisher** (`app/services/event_publisher.py`) - Publishes task events to Dapr pub/sub (Redpanda) with at-least-once delivery
- **Reminder Publisher** (`app/services/reminder_publisher.py`) - Schedules reminder events for tasks with due dates
- **Correlation Middleware** (`app/middleware/correlation.py`) - Propagates correlation IDs across distributed services
- **Structured Logging** (`app/main.py`) - JSON log format with correlation IDs for observability

### Event Topics
| Topic | Publisher | Consumers |
|-------|-----------|-----------|
| `task-events` | Backend | recurring-task, notification |
| `task-updates` | Backend | websocket (real-time sync) |
| `reminders` | Backend/Scheduler | notification |

### Database Models (Phase V additions)
- `RecurrencePattern` - Recurring task schedules (daily, weekly, monthly, yearly)
- `NotificationPreference` - Per-user notification settings with quiet hours
- `ProcessedEvent` - Idempotent event processing tracking
