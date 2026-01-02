# Implementation Plan: Phase II - Full-Stack Todo Web Application

**Branch**: `002-fullstack-todo-web` | **Date**: 2026-01-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-fullstack-todo-web/spec.md`

---

## Summary

Evolve the Phase I in-memory console todo application into a secure, multi-user, full-stack web application. The system implements user authentication via Better Auth with JWT tokens, a Next.js frontend with App Router, a FastAPI backend with SQLModel ORM, and Neon Serverless PostgreSQL for persistence. Users can register, sign in, and manage their personal tasks with complete data isolation.

---

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5+ (frontend)
**Primary Dependencies**:
- Backend: FastAPI, SQLModel, asyncpg, PyJWT, Alembic
- Frontend: Next.js 16+, Better Auth, Tailwind CSS, jose

**Storage**: Neon Serverless PostgreSQL (transaction pooling on port 6432)
**Testing**: pytest-asyncio (backend), Jest/React Testing Library (frontend)
**Target Platform**: Web (desktop browsers, responsive)
**Project Type**: Web application (monorepo: /frontend + /backend)
**Performance Goals**:
- Task list loads <2s for 100 tasks
- CRUD operations <1s
- 100 concurrent users

**Constraints**:
- JWT token expiration: 30 days
- Title max: 200 characters
- Description max: 2000 characters
- No user table in backend (Better Auth owns users)

**Scale/Scope**: 8 user stories, 31 functional requirements, 10 success criteria

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Planning Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Spec-Driven Only** | ✅ PASS | All code will be generated from this spec via Claude Code |
| **II. Clean Architecture** | ✅ PASS | Frontend (Next.js) ↔ Backend API (FastAPI) ↔ Database (Neon) - separated |
| **III. Accuracy** | ✅ PASS | 8 user stories with 28 acceptance scenarios defined |
| **IV. Reproducibility** | ⚠️ DEFER | Dockerfiles/Helm not in Phase II scope; to be added in Phase III |

### Technology Standards Alignment

| Layer | Required | Planned | Status |
|-------|----------|---------|--------|
| Backend Runtime | Python 3.13+ | Python 3.13+ | ✅ |
| Backend Framework | FastAPI | FastAPI | ✅ |
| ORM | SQLModel | SQLModel | ✅ |
| Database | Neon PostgreSQL | Neon PostgreSQL | ✅ |
| Frontend | Next.js 16+ | Next.js 16+ | ✅ |
| Styling | Tailwind CSS | Tailwind CSS | ✅ |
| Authentication | Better Auth | Better Auth | ✅ |

### Post-Design Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Spec-Driven Only** | ✅ PASS | research.md, data-model.md, contracts created from spec |
| **II. Clean Architecture** | ✅ PASS | Clear API contracts, no direct DB from frontend |
| **III. Accuracy** | ✅ PASS | OpenAPI contract matches all FR requirements |
| **IV. Reproducibility** | ⚠️ DEFER | Container setup deferred to Phase III |

---

## Project Structure

### Documentation (this feature)

```text
specs/002-fullstack-todo-web/
├── plan.md              # This file
├── research.md          # Phase 0 output - technical decisions
├── data-model.md        # Phase 1 output - entity definitions
├── quickstart.md        # Phase 1 output - setup guide
├── contracts/           # Phase 1 output - API contracts
│   └── openapi.yaml     # REST API specification
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (from /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry
│   ├── config/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLModel async engine config
│   │   └── settings.py            # Environment variables
│   ├── models/
│   │   ├── __init__.py
│   │   └── task.py                # Task SQLModel
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── task.py                # Pydantic request/response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   └── task_service.py        # Business logic layer
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── tasks.py           # Task CRUD endpoints
│   │       └── health.py          # Health check endpoint
│   └── dependencies/
│       ├── __init__.py
│       ├── database.py            # Session dependency injection
│       └── auth.py                # JWT verification dependency
├── alembic/
│   ├── versions/                  # Migration files
│   ├── env.py
│   └── script.py.mako
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_tasks.py
│   └── test_auth.py
├── .env.example
├── pyproject.toml
└── alembic.ini

frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/                # Unprotected auth routes
│   │   │   ├── layout.tsx
│   │   │   ├── signin/
│   │   │   │   └── page.tsx
│   │   │   └── signup/
│   │   │       └── page.tsx
│   │   ├── (protected)/           # Protected app routes
│   │   │   ├── layout.tsx         # Auth check + navbar
│   │   │   └── dashboard/
│   │   │       └── page.tsx       # Task list view
│   │   ├── api/
│   │   │   ├── auth/
│   │   │   │   └── [...auth]/
│   │   │   │       └── route.ts   # Better Auth handler
│   │   │   └── tasks/
│   │   │       ├── route.ts       # List/Create proxy
│   │   │       └── [id]/
│   │   │           └── route.ts   # Get/Update/Delete proxy
│   │   ├── layout.tsx             # Root layout
│   │   ├── page.tsx               # Redirect to dashboard
│   │   ├── globals.css            # Tailwind imports
│   │   └── middleware.ts          # Edge auth middleware
│   ├── components/
│   │   ├── ui/                    # Reusable UI components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   └── card.tsx
│   │   ├── auth/
│   │   │   ├── signin-form.tsx
│   │   │   └── signup-form.tsx
│   │   └── tasks/
│   │       ├── task-list.tsx
│   │       ├── task-item.tsx
│   │       ├── task-form.tsx
│   │       └── task-edit-dialog.tsx
│   ├── lib/
│   │   ├── auth.client.ts         # Better Auth client setup
│   │   ├── auth.server.ts         # Server-side session utils
│   │   ├── api.client.ts          # API fetch utilities
│   │   └── types.ts               # TypeScript interfaces
│   └── hooks/
│       ├── use-tasks.ts           # Task data fetching hook
│       └── use-auth.ts            # Auth state hook
├── .env.local.example
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── next.config.js
```

**Structure Decision**: Web application with monorepo structure. Frontend and backend are separate deployable units with API contracts as the integration boundary. This follows the constitution's Clean Architecture principle.

---

## Implementation Phases

### Phase 1: Backend Foundation

**Goal**: Establish FastAPI project with database connectivity and health check

| Step | Description | Dependencies | Validation |
|------|-------------|--------------|------------|
| 1.1 | Initialize backend with uv, create project structure | None | `uv run python -c "import fastapi"` |
| 1.2 | Configure SQLModel async engine for Neon | 1.1 | Engine creates without error |
| 1.3 | Create Task model in SQLModel | 1.2 | Model imports correctly |
| 1.4 | Set up Alembic for migrations | 1.2, 1.3 | `alembic upgrade head` succeeds |
| 1.5 | Create database session dependency | 1.2 | Session yields correctly |
| 1.6 | Implement health check endpoint | 1.1, 1.5 | `GET /api/health` returns 200 |

**Checkpoint**: Backend starts, connects to Neon, health check passes

---

### Phase 2: Backend Authentication

**Goal**: Implement JWT verification middleware for protected endpoints

| Step | Description | Dependencies | Validation |
|------|-------------|--------------|------------|
| 2.1 | Create auth dependency for JWT verification | 1.1 | Dependency loads |
| 2.2 | Implement token extraction (Bearer header + cookie) | 2.1 | Extracts token correctly |
| 2.3 | Implement JWT signature verification with BETTER_AUTH_SECRET | 2.2 | Verifies valid tokens |
| 2.4 | Extract user_id from JWT payload (sub claim) | 2.3 | Returns UUID |
| 2.5 | Handle auth errors (401 for invalid/missing) | 2.1-2.4 | Returns 401 appropriately |
| 2.6 | Configure CORS for frontend | 1.1 | Preflight requests succeed |

**Checkpoint**: Protected endpoints reject invalid tokens, accept valid ones

---

### Phase 3: Backend Task API

**Goal**: Implement all task CRUD endpoints with user isolation

| Step | Description | Dependencies | Validation |
|------|-------------|--------------|------------|
| 3.1 | Create Pydantic schemas (TaskCreate, TaskUpdate, TaskResponse) | 1.3 | Schemas validate correctly |
| 3.2 | Implement TaskService with user-scoped queries | 1.3, 1.5, 2.4 | Service methods work |
| 3.3 | Implement GET /api/tasks (list, ordered by created_at DESC) | 3.1, 3.2 | Returns user's tasks only |
| 3.4 | Implement POST /api/tasks (create) | 3.1, 3.2 | Creates task for user |
| 3.5 | Implement GET /api/tasks/{id} (get single) | 3.1, 3.2 | Returns 404 for other users' tasks |
| 3.6 | Implement PUT /api/tasks/{id} (update) | 3.1, 3.2 | Updates only user's tasks |
| 3.7 | Implement PATCH /api/tasks/{id}/toggle | 3.1, 3.2 | Toggles completion status |
| 3.8 | Implement DELETE /api/tasks/{id} | 3.1, 3.2 | Deletes only user's tasks |

**Checkpoint**: All 6 API endpoints work with user isolation, OpenAPI docs accessible

---

### Phase 4: Frontend Foundation

**Goal**: Set up Next.js with Tailwind and routing structure

| Step | Description | Dependencies | Validation |
|------|-------------|--------------|------------|
| 4.1 | Initialize Next.js with TypeScript, Tailwind, App Router | None | `pnpm dev` starts |
| 4.2 | Create route group structure: (auth), (protected) | 4.1 | Routes accessible |
| 4.3 | Set up environment variables (.env.local) | 4.1 | Variables load correctly |
| 4.4 | Create lib/types.ts with Task interface | 4.1 | Types available |
| 4.5 | Create base UI components (button, input, card) | 4.1 | Components render |

**Checkpoint**: Frontend runs, routing works, Tailwind styles apply

---

### Phase 5: Frontend Authentication

**Goal**: Implement Better Auth integration with protected routes

| Step | Description | Dependencies | Validation |
|------|-------------|--------------|------------|
| 5.1 | Install and configure Better Auth | 4.1 | Library installed |
| 5.2 | Create API route handler /api/auth/[...auth] | 5.1 | Route handles requests |
| 5.3 | Create auth.client.ts with signIn, signUp, signOut | 5.1 | Functions exported |
| 5.4 | Create auth.server.ts with getSession | 5.1 | Session retrieval works |
| 5.5 | Implement middleware.ts for edge auth check | 5.4 | Redirects unauthenticated |
| 5.6 | Create signin page with form | 5.3 | Form submits |
| 5.7 | Create signup page with form | 5.3 | Registration works |
| 5.8 | Implement (protected)/layout.tsx with session check | 5.4 | Layout protects routes |

**Checkpoint**: Users can sign up, sign in, access protected routes; unauthenticated users redirected

---

### Phase 6: Frontend Task Management

**Goal**: Implement task UI with all CRUD operations

| Step | Description | Dependencies | Validation |
|------|-------------|--------------|------------|
| 6.1 | Create API route proxies for /api/tasks | 5.5 | Proxies forward requests |
| 6.2 | Create api.client.ts with fetch utilities | 6.1 | API calls work |
| 6.3 | Create useTasks hook for data fetching | 6.2 | Hook returns tasks |
| 6.4 | Implement TaskList component | 6.3, 4.5 | List renders tasks |
| 6.5 | Implement TaskItem with checkbox toggle | 6.4 | Toggle works |
| 6.6 | Style completed tasks (strikethrough/muted) | 6.5 | Visual distinction shows |
| 6.7 | Implement TaskForm for creating tasks | 6.2 | Form creates tasks |
| 6.8 | Implement edit functionality (dialog/inline) | 6.4 | Edit saves changes |
| 6.9 | Implement delete with confirmation | 6.4 | Delete removes task |
| 6.10 | Add loading states and error handling | 6.3-6.9 | States display correctly |
| 6.11 | Implement dashboard page with all components | 6.4-6.10 | Dashboard functional |

**Checkpoint**: Full task CRUD working, all user stories testable

---

### Phase 7: Polish and Validation

**Goal**: Edge cases, error handling, and acceptance testing

| Step | Description | Dependencies | Validation |
|------|-------------|--------------|------------|
| 7.1 | Handle session expiration (redirect to signin) | 6.11 | User sees "Session expired" |
| 7.2 | Handle backend unavailable (friendly error) | 6.11 | Error message displays |
| 7.3 | Implement form validation (title required, max lengths) | 6.7, 6.8 | Validation errors show |
| 7.4 | Add sign out functionality with navbar button | 5.8 | Sign out works |
| 7.5 | Implement empty state for no tasks | 6.4 | Message displays |
| 7.6 | Manual acceptance testing (all 28 scenarios) | 7.1-7.5 | All scenarios pass |
| 7.7 | Cross-user isolation testing | 7.6 | No data leakage |

**Checkpoint**: All acceptance criteria met, feature complete

---

## Complexity Tracking

> No constitution violations requiring justification.

| Item | Constitution Alignment |
|------|------------------------|
| Monorepo (2 projects) | ✅ Allowed: frontend + backend per Clean Architecture |
| No user table in backend | ✅ Simplifies architecture, Better Auth owns users |
| API route proxies | ✅ Clean separation, hides backend from client |
| No Dockerfiles | ⚠️ Deferred to Phase III per scope |

---

## Architectural Decisions

### ADR-001: Better Auth on Frontend, JWT Verification on Backend

**Decision**: Use Better Auth on the Next.js frontend for authentication; FastAPI backend only verifies JWTs using the shared BETTER_AUTH_SECRET.

**Rationale**:
- Single source of truth for user management
- No user table synchronization needed
- Stateless backend authentication
- Reduced complexity

**Alternatives Rejected**:
- Backend-issued tokens: Duplicates Better Auth functionality
- Session-based auth: Less portable for potential future microservices

---

### ADR-002: API Route Proxies for Backend Communication

**Decision**: Use Next.js API routes to proxy requests to FastAPI backend rather than direct client-to-backend calls.

**Rationale**:
- Backend URL stays server-side only (security)
- CORS handled server-side
- Single point for auth header injection
- Consistent error handling

**Alternatives Rejected**:
- Direct fetch to backend: Exposes backend URL, CORS complexity
- GraphQL: Over-engineered for simple REST operations

---

### ADR-003: Transaction Pooling for Neon Connection

**Decision**: Use Neon's pgbouncer transaction pooling (port 6432) with conservative pool sizing (5-10).

**Rationale**:
- Serverless-friendly: connections returned immediately after each transaction
- Prevents connection exhaustion on Neon's limits
- pool_pre_ping handles cold starts

**Alternatives Rejected**:
- NullPool: 10x slower performance
- Large pools: Exceed Neon connection limits

---

## Dependencies & Execution Order

```
Phase 1 (Backend Foundation)
    └── Phase 2 (Backend Auth)
         └── Phase 3 (Backend API)
              │
Phase 4 (Frontend Foundation) ─────┐
    └── Phase 5 (Frontend Auth)    │
         └── Phase 6 (Frontend Tasks)
              └── Phase 7 (Polish)
```

**Parallelization Opportunities**:
- Phases 1-3 (Backend) and Phase 4 (Frontend Foundation) can run in parallel
- Phase 5-6 depend on Phase 3 completion for API testing

---

## Validation Checkpoints

| Phase | Checkpoint | Pass Criteria |
|-------|------------|---------------|
| 1 | Backend Foundation | Health check returns 200, DB connected |
| 2 | Backend Auth | Valid JWT accepted, invalid rejected (401) |
| 3 | Backend API | All 6 endpoints work with user isolation |
| 4 | Frontend Foundation | App loads, routing works |
| 5 | Frontend Auth | Sign up, sign in, protected routes work |
| 6 | Frontend Tasks | All CRUD operations work |
| 7 | Polish | All 28 acceptance scenarios pass |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Better Auth integration issues | Research completed; fallback to manual JWT handling |
| Neon cold start latency | pool_pre_ping enabled; health check warms connection |
| Cross-user data leakage | All queries scoped by user_id; manual isolation testing |
| JWT secret mismatch | Same BETTER_AUTH_SECRET in both .env files; validation in quickstart |

---

## Generated Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| research.md | `specs/002-fullstack-todo-web/research.md` | Technical decisions and rationale |
| data-model.md | `specs/002-fullstack-todo-web/data-model.md` | Entity definitions and schemas |
| openapi.yaml | `specs/002-fullstack-todo-web/contracts/openapi.yaml` | REST API contract |
| quickstart.md | `specs/002-fullstack-todo-web/quickstart.md` | Setup guide |

---

## Next Steps

1. Run `/sp.tasks` to generate detailed implementation tasks
2. Execute tasks via `/sp.implement`
3. Test each user story after its phase completes
4. Commit after each task completion
