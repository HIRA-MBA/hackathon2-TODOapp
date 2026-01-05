# Tasks: Phase II - Full-Stack Todo Web Application

**Input**: Design documents from `/specs/002-fullstack-todo-web/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Not explicitly requested - tests are OPTIONAL and not included in this task list.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app monorepo**: `backend/` and `frontend/` at repository root
- Backend: `backend/app/` for source, `backend/tests/` for tests
- Frontend: `frontend/src/` for source

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization for both backend and frontend

- [x] T001 Create backend project structure with uv in `backend/`
- [x] T002 [P] Create `backend/pyproject.toml` with FastAPI, SQLModel, asyncpg, PyJWT, Alembic dependencies
- [x] T003 [P] Create `backend/.env.example` with DATABASE_URL, BETTER_AUTH_SECRET placeholders
- [x] T004 [P] Create frontend project with Next.js 16+, TypeScript, Tailwind in `frontend/`
- [x] T005 [P] Create `frontend/.env.local.example` with BETTER_AUTH_SECRET, BACKEND_URL placeholders

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Backend Foundation

- [x] T006 Create settings module with Pydantic Settings in `backend/app/config/settings.py`
- [x] T007 Configure SQLModel async engine for Neon PostgreSQL in `backend/app/config/database.py`
- [x] T008 Create Task SQLModel entity in `backend/app/models/task.py` per data-model.md
- [x] T009 Initialize Alembic with async support in `backend/alembic/`
- [x] T010 Create initial migration for Task table in `backend/alembic/versions/`
- [x] T011 Create database session dependency in `backend/app/dependencies/database.py`
- [x] T012 Implement JWT verification dependency in `backend/app/dependencies/auth.py`
- [x] T013 [P] Create Pydantic schemas (TaskCreate, TaskUpdate, TaskResponse) in `backend/app/schemas/task.py`
- [x] T014 Implement TaskService with user-scoped queries in `backend/app/services/task_service.py`
- [x] T015 Create FastAPI app with CORS in `backend/app/main.py`
- [x] T016 Implement health check endpoint in `backend/app/api/routes/health.py`
- [x] T017 Wire up API routers in `backend/app/api/routes/__init__.py`

### Frontend Foundation

- [x] T018 [P] Create root layout with Tailwind imports in `frontend/src/app/layout.tsx`
- [x] T019 [P] Create global styles in `frontend/src/app/globals.css`
- [x] T020 [P] Create TypeScript interfaces (Task, User) in `frontend/src/lib/types.ts`
- [x] T021 [P] Create base UI Button component in `frontend/src/components/ui/button.tsx`
- [x] T022 [P] Create base UI Input component in `frontend/src/components/ui/input.tsx`
- [x] T023 [P] Create base UI Card component in `frontend/src/components/ui/card.tsx`
- [x] T024 Create route group structure `(auth)` and `(protected)` in `frontend/src/app/`
- [x] T025 Install and configure Better Auth in `frontend/`
- [x] T026 Create Better Auth client utilities in `frontend/src/lib/auth.client.ts`
- [x] T027 Create Better Auth server utilities in `frontend/src/lib/auth.server.ts`
- [x] T028 Create Better Auth API route handler in `frontend/src/app/api/auth/[...auth]/route.ts`
- [x] T029 Implement edge middleware for auth protection in `frontend/src/app/middleware.ts`
- [x] T030 Create API client utilities in `frontend/src/lib/api.client.ts`

**Checkpoint**: Foundation ready - Backend runs with health check, Frontend runs with auth configured

---

## Phase 3: User Story 1 - User Registration (Priority: P1)

**Goal**: Allow new users to create accounts and access their private todo list

**Independent Test**: Navigate to `/signup` → enter email and password → submit → verify redirected to dashboard

### Implementation for User Story 1

- [x] T031 [P] [US1] Create (auth) layout in `frontend/src/app/(auth)/layout.tsx`
- [x] T032 [P] [US1] Create signup form component in `frontend/src/components/auth/signup-form.tsx`
- [x] T033 [US1] Create signup page in `frontend/src/app/(auth)/signup/page.tsx`
- [x] T034 [US1] Add form validation (email format, password min 8 chars) in signup-form.tsx
- [x] T035 [US1] Handle duplicate email error display in signup-form.tsx
- [x] T036 [US1] Implement auto-redirect to dashboard after successful signup

**Checkpoint**: Users can register with email/password and are redirected to dashboard

---

## Phase 4: User Story 2 - User Sign In (Priority: P1)

**Goal**: Allow registered users to sign in and access their tasks

**Independent Test**: Navigate to `/signin` → enter valid credentials → submit → verify redirected to dashboard

### Implementation for User Story 2

- [x] T037 [P] [US2] Create signin form component in `frontend/src/components/auth/signin-form.tsx`
- [x] T038 [US2] Create signin page in `frontend/src/app/(auth)/signin/page.tsx`
- [x] T039 [US2] Add form validation in signin-form.tsx
- [x] T040 [US2] Handle invalid credentials error display in signin-form.tsx
- [x] T041 [US2] Add link to signup page from signin page
- [x] T042 [US2] Verify JWT persistence across browser sessions

**Checkpoint**: Users can sign in and session persists across browser restarts

---

## Phase 5: User Story 3 - View My Tasks (Priority: P1)

**Goal**: Display all tasks for the authenticated user with status indicators

**Independent Test**: Sign in → verify task list displays only current user's tasks with correct status

### Implementation for User Story 3

- [x] T043 [US3] Implement GET /api/tasks endpoint in `backend/app/api/routes/tasks.py`
- [x] T044 [US3] Create task list API proxy in `frontend/src/app/api/tasks/route.ts`
- [x] T045 [P] [US3] Create useTasks hook in `frontend/src/hooks/use-tasks.ts`
- [x] T046 [P] [US3] Create TaskItem component in `frontend/src/components/tasks/task-item.tsx`
- [x] T047 [US3] Create TaskList component in `frontend/src/components/tasks/task-list.tsx`
- [x] T048 [US3] Style completed tasks with strikethrough/muted in TaskItem
- [x] T049 [US3] Create (protected) layout with session check in `frontend/src/app/(protected)/layout.tsx`
- [x] T050 [US3] Create dashboard page in `frontend/src/app/(protected)/dashboard/page.tsx`
- [x] T051 [US3] Implement empty state "No tasks yet. Create your first task!" in TaskList
- [x] T052 [US3] Add loading state during task fetch in dashboard

**Checkpoint**: Authenticated users see their task list with visual status distinction

---

## Phase 6: User Story 4 - Create a New Task (Priority: P1)

**Goal**: Allow users to create new tasks with title and optional description

**Independent Test**: Sign in → click "Add Task" → enter title → submit → verify task appears in list

### Implementation for User Story 4

- [x] T053 [US4] Implement POST /api/tasks endpoint in `backend/app/api/routes/tasks.py`
- [x] T054 [US4] Add create task handler to API proxy in `frontend/src/app/api/tasks/route.ts`
- [x] T055 [P] [US4] Create TaskForm component in `frontend/src/components/tasks/task-form.tsx`
- [x] T056 [US4] Add title validation (required, max 200 chars) in TaskForm
- [x] T057 [US4] Add description validation (optional, max 2000 chars) in TaskForm
- [x] T058 [US4] Add create task mutation to useTasks hook
- [x] T059 [US4] Integrate TaskForm in dashboard page
- [x] T060 [US4] Show success feedback on task creation

**Checkpoint**: Users can create tasks that appear immediately in the list

---

## Phase 7: User Story 5 - Toggle Task Completion (Priority: P2)

**Goal**: Allow users to mark tasks complete/incomplete with visual feedback

**Independent Test**: Create task → click checkbox → verify visual change → click again → verify reverts

### Implementation for User Story 5

- [x] T061 [US5] Implement PATCH /api/tasks/{id}/toggle endpoint in `backend/app/api/routes/tasks.py`
- [x] T062 [US5] Create toggle API proxy in `frontend/src/app/api/tasks/[id]/route.ts`
- [x] T063 [US5] Add checkbox toggle handler in TaskItem component
- [x] T064 [US5] Add toggle mutation to useTasks hook
- [x] T065 [US5] Add optimistic UI update for toggle action
- [x] T066 [US5] Verify toggle persists after page refresh

**Checkpoint**: Task completion toggles with immediate visual feedback and persists

---

## Phase 8: User Story 6 - Update Task Details (Priority: P2)

**Goal**: Allow users to edit task title and description

**Independent Test**: Select task → click edit → modify title/description → save → verify changes

### Implementation for User Story 6

- [x] T067 [US6] Implement PUT /api/tasks/{id} endpoint in `backend/app/api/routes/tasks.py`
- [x] T068 [US6] Add update handler to task API proxy in `frontend/src/app/api/tasks/[id]/route.ts`
- [x] T069 [P] [US6] Create TaskEditDialog component in `frontend/src/components/tasks/task-edit-dialog.tsx`
- [x] T070 [US6] Add edit button to TaskItem component
- [x] T071 [US6] Add validation (title required, max lengths) in TaskEditDialog
- [x] T072 [US6] Add update mutation to useTasks hook
- [x] T073 [US6] Implement cancel functionality in TaskEditDialog
- [x] T074 [US6] Show success feedback on task update

**Checkpoint**: Users can edit tasks with validation and changes persist

---

## Phase 9: User Story 7 - Delete a Task (Priority: P2)

**Goal**: Allow users to permanently delete tasks with confirmation

**Independent Test**: Select task → click delete → confirm → verify task removed

### Implementation for User Story 7

- [x] T075 [US7] Implement DELETE /api/tasks/{id} endpoint in `backend/app/api/routes/tasks.py`
- [x] T076 [US7] Add delete handler to task API proxy in `frontend/src/app/api/tasks/[id]/route.ts`
- [x] T077 [US7] Add delete button to TaskItem component
- [x] T078 [US7] Implement confirmation dialog before delete
- [x] T079 [US7] Add delete mutation to useTasks hook
- [x] T080 [US7] Verify deleted task stays deleted after refresh

**Checkpoint**: Users can delete tasks with confirmation and deletion persists

---

## Phase 10: User Story 8 - Sign Out (Priority: P3)

**Goal**: Allow users to sign out and secure their account

**Independent Test**: Sign in → click sign out → verify redirected to signin → verify cannot access dashboard

### Implementation for User Story 8

- [x] T081 [US8] Create navbar component with user info and sign out button in `frontend/src/components/navbar.tsx`
- [x] T082 [US8] Add navbar to (protected) layout
- [x] T083 [US8] Implement sign out functionality with Better Auth client
- [x] T084 [US8] Redirect to signin page after sign out
- [x] T085 [US8] Verify protected routes redirect after sign out

**Checkpoint**: Users can sign out and are properly redirected

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, error handling, and final validation

- [x] T086 Handle session expiration with "Session expired" message and redirect
- [x] T087 Handle backend unavailable with "Unable to connect. Please try again later." message
- [x] T088 [P] Implement 401 response handling with redirect to signin
- [x] T089 [P] Add root page redirect to dashboard in `frontend/src/app/page.tsx`
- [x] T090 Verify cross-user task isolation (user A cannot see user B's tasks)
- [x] T091 Verify task access by ID returns 404 for other users' tasks
- [x] T092 Run all 28 acceptance scenarios from spec.md manually
- [x] T093 Update quickstart.md with final setup verification steps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-10)**: All depend on Foundational phase completion
  - US1-US4 (P1 stories): Core MVP functionality
  - US5-US7 (P2 stories): Enhanced task management
  - US8 (P3 story): Security feature
- **Polish (Phase 11)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Registration)**: Can start after Foundational - No dependencies on other stories
- **US2 (Sign In)**: Can start after Foundational - No dependencies on other stories
- **US3 (View Tasks)**: Requires backend task endpoints from Foundational
- **US4 (Create Task)**: Can run parallel with US3, integrates with task list
- **US5 (Toggle)**: Depends on US3/US4 for existing tasks to toggle
- **US6 (Update)**: Depends on US3/US4 for existing tasks to edit
- **US7 (Delete)**: Depends on US3/US4 for existing tasks to delete
- **US8 (Sign Out)**: Can run parallel with US3-US7

### Within Each User Story

- Backend endpoints before frontend API proxies
- API proxies before frontend hooks
- Hooks before components
- Components before page integration

### Parallel Opportunities

**Phase 1 (Setup)**: T002, T003, T004, T005 can run in parallel

**Phase 2 (Foundational)**:
- Backend: T013 can run parallel with T006-T012
- Frontend: T018-T023 can all run in parallel
- Frontend auth setup (T25-T30) after T24

**User Story phases**: Different user stories can be worked on in parallel by different team members after Foundational completes

---

## Parallel Example: Foundational Frontend

```bash
# Launch all UI components together:
Task: "Create base UI Button component in frontend/src/components/ui/button.tsx"
Task: "Create base UI Input component in frontend/src/components/ui/input.tsx"
Task: "Create base UI Card component in frontend/src/components/ui/card.tsx"
Task: "Create TypeScript interfaces in frontend/src/lib/types.ts"
Task: "Create root layout in frontend/src/app/layout.tsx"
Task: "Create global styles in frontend/src/app/globals.css"
```

---

## Implementation Strategy

### MVP First (User Stories 1-4 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Registration)
4. Complete Phase 4: User Story 2 (Sign In)
5. Complete Phase 5: User Story 3 (View Tasks)
6. Complete Phase 6: User Story 4 (Create Task)
7. **STOP and VALIDATE**: Test all P1 stories independently
8. Deploy/demo if ready - this is a functional MVP!

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 + US2 → User can register and sign in
3. Add US3 + US4 → User can view and create tasks (MVP!)
4. Add US5 → User can toggle completion
5. Add US6 → User can edit tasks
6. Add US7 → User can delete tasks
7. Add US8 → User can sign out securely
8. Polish phase → Production-ready

### Suggested MVP Scope

**Minimum Viable Product = Phase 1 + Phase 2 + Phases 3-6 (US1-US4)**

This delivers:
- User registration
- User sign in
- View task list
- Create tasks

Users can register, sign in, and manage a basic task list.

---

## Task Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| 1 | Setup | 5 |
| 2 | Foundational | 25 |
| 3 | US1 - Registration | 6 |
| 4 | US2 - Sign In | 6 |
| 5 | US3 - View Tasks | 10 |
| 6 | US4 - Create Task | 8 |
| 7 | US5 - Toggle | 6 |
| 8 | US6 - Update | 8 |
| 9 | US7 - Delete | 6 |
| 10 | US8 - Sign Out | 5 |
| 11 | Polish | 8 |
| **Total** | | **93** |

### Tasks by User Story

| Story | Priority | Tasks |
|-------|----------|-------|
| US1 - Registration | P1 | 6 |
| US2 - Sign In | P1 | 6 |
| US3 - View Tasks | P1 | 10 |
| US4 - Create Task | P1 | 8 |
| US5 - Toggle | P2 | 6 |
| US6 - Update | P2 | 8 |
| US7 - Delete | P2 | 6 |
| US8 - Sign Out | P3 | 5 |

### Parallel Opportunities

- **17 tasks** marked [P] can run in parallel within their phases
- All 8 user story phases can be parallelized across team members
- Setup tasks can be fully parallelized
- Frontend UI components can all be built simultaneously

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Backend runs on port 8000, Frontend runs on port 3000
- All task API endpoints require JWT authentication via Better Auth
