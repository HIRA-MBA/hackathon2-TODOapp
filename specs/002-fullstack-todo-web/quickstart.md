# Quickstart: Phase II - Full-Stack Todo Web Application

**Branch**: `002-fullstack-todo-web`
**Date**: 2026-01-02

---

## Prerequisites

### Required Software
- **Node.js**: 18+ (for Next.js frontend)
- **Python**: 3.13+ (for FastAPI backend)
- **uv**: Python package manager
- **pnpm** or **npm**: Node package manager
- **Git**: Version control

### Required Accounts/Services
- **Neon**: Serverless PostgreSQL account (https://neon.tech)
- Generate `BETTER_AUTH_SECRET`: 32+ character random string

---

## Environment Setup

### 1. Clone and Navigate
```powershell
# Already in repository
cd D:\hackathone2
git checkout 002-fullstack-todo-web
```

### 2. Create Environment Files

**Backend (.env in /backend):**
```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://user:password@host:6432/database?sslmode=require
BETTER_AUTH_SECRET=your-32-character-secret-here
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

**Frontend (.env.local in /frontend):**
```bash
# frontend/.env.local
BETTER_AUTH_SECRET=your-32-character-secret-here  # Same as backend
BACKEND_URL=http://localhost:8000
DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require
NEXT_PUBLIC_APP_NAME=Todo App
```

### 3. Generate BETTER_AUTH_SECRET
```powershell
# PowerShell - Generate 32-byte hex secret
[System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

---

## Backend Setup

### 1. Initialize Backend
```powershell
cd backend
uv init
uv add fastapi uvicorn sqlmodel asyncpg pyjwt python-jose alembic python-dotenv
```

### 2. Run Database Migrations
```powershell
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Create task table"

# Apply migration
alembic upgrade head
```

### 3. Start Backend Server
```powershell
uv run uvicorn app.main:app --reload --port 8000
```

### 4. Verify Backend
```powershell
# Health check
curl http://localhost:8000/api/health
```

---

## Frontend Setup

### 1. Initialize Frontend
```powershell
cd frontend
npx create-next-app@latest . --typescript --tailwind --app --src-dir --import-alias "@/*"
```

### 2. Install Dependencies
```powershell
pnpm add better-auth jose
pnpm add -D @types/node
```

### 3. Start Frontend Server
```powershell
pnpm dev
```

### 4. Verify Frontend
Open http://localhost:3000 in browser

---

## Neon Database Setup

### 1. Create Neon Project
1. Go to https://console.neon.tech
2. Create new project
3. Copy connection string

### 2. Connection String Format
```
# For application (transaction pooling)
postgresql+asyncpg://user:password@host:6432/database?sslmode=require

# For migrations (session pooling)
postgresql://user:password@host:5432/database?sslmode=require
```

---

## Development Workflow

### Start Both Services
```powershell
# Terminal 1: Backend
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && pnpm dev
```

### URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Quick Verification Steps

### 1. Backend Health
```powershell
curl http://localhost:8000/api/health
# Expected: {"status":"healthy","database":"connected"}
```

### 2. Frontend Loads
- Open http://localhost:3000
- Should see signin page (redirected from protected route)

### 3. Auth Flow
- Navigate to http://localhost:3000/signup
- Create account
- Should redirect to dashboard

### 4. Task Operations
- Create a task
- Toggle completion
- View task list (newest first)
- Delete task

---

## Troubleshooting

### Database Connection Failed
- Verify Neon connection string
- Check port: 6432 for pooling, 5432 for direct
- Ensure `sslmode=require` is included

### JWT Verification Failed
- Ensure `BETTER_AUTH_SECRET` is identical in frontend and backend
- Check token is being passed in Authorization header

### CORS Errors
- Verify `CORS_ORIGINS` in backend .env includes frontend URL
- Check `allow_credentials=True` in FastAPI CORS config

### Frontend Can't Reach Backend
- Verify `BACKEND_URL` in frontend .env.local
- Check backend is running on port 8000
- Try API route proxy instead of direct fetch

---

## Project Structure After Setup

```
D:\hackathone2\
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config/
│   │   │   └── database.py      # SQLModel config
│   │   ├── models/
│   │   │   └── task.py          # Task model
│   │   ├── schemas/
│   │   │   └── task.py          # Pydantic schemas
│   │   ├── services/
│   │   │   └── task_service.py  # Business logic
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── tasks.py     # API endpoints
│   │   └── dependencies/
│   │       ├── database.py      # DB session
│   │       └── auth.py          # JWT verification
│   ├── alembic/                 # Migrations
│   ├── tests/
│   ├── .env
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   │   ├── signin/page.tsx
│   │   │   │   └── signup/page.tsx
│   │   │   ├── (protected)/
│   │   │   │   ├── layout.tsx
│   │   │   │   └── dashboard/page.tsx
│   │   │   ├── api/
│   │   │   │   ├── auth/[...auth]/route.ts
│   │   │   │   └── tasks/route.ts
│   │   │   ├── layout.tsx
│   │   │   └── middleware.ts
│   │   ├── components/
│   │   ├── lib/
│   │   │   ├── auth.client.ts
│   │   │   └── auth.server.ts
│   │   └── hooks/
│   ├── .env.local
│   ├── package.json
│   └── tsconfig.json
│
├── specs/
│   └── 002-fullstack-todo-web/
│       ├── spec.md
│       ├── plan.md
│       ├── research.md
│       ├── data-model.md
│       ├── quickstart.md
│       ├── contracts/
│       │   └── openapi.yaml
│       └── tasks.md (generated by /sp.tasks)
│
└── src/                         # Phase I CLI (unchanged)
```

---

## Next Steps

1. Run `/sp.tasks` to generate implementation tasks
2. Execute tasks in order via `/sp.implement`
3. Test each user story independently
4. Commit after each task completion
