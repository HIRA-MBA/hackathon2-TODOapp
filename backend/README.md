# Todo Backend API

FastAPI backend for the Full-Stack Todo Web Application.

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

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/tasks` - List all tasks (requires auth)
- `POST /api/tasks` - Create a task (requires auth)
- `GET /api/tasks/{id}` - Get a task (requires auth)
- `PUT /api/tasks/{id}` - Update a task (requires auth)
- `PATCH /api/tasks/{id}/toggle` - Toggle task completion (requires auth)
- `DELETE /api/tasks/{id}` - Delete a task (requires auth)
