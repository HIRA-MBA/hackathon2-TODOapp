# Feature Specification: Phase II - Full-Stack Todo Web Application

**Feature Branch**: `002-fullstack-todo-web`
**Created**: 2026-01-02
**Status**: Draft
**Input**: User description: "Transition the project to Phase II: Full-Stack Web Application - Evolve the Phase I console todo app into a secure, multi-user, full-stack web application with Next.js frontend, FastAPI backend, Neon PostgreSQL, and Better Auth JWT authentication"

---

## Clarifications

### Session 2026-01-02

- Q: How long should JWT tokens remain valid before requiring re-authentication? → A: 30 days
- Q: How should user data be handled between Better Auth and backend? → A: Better Auth owns users, backend references user_id only (no user table in backend)
- Q: How should tasks be ordered when displayed? → A: Newest first (created_at DESC)
- Q: How should completed tasks be displayed relative to incomplete tasks? → A: Show inline with visual distinction (strikethrough/muted)

---

## Overview

This specification defines the evolution of the Phase I in-memory console todo application into a secure, multi-user, full-stack web application. The system will support user registration, authentication, and personal task management where each user can only access their own tasks.

### Architecture Summary

- **Frontend**: Next.js (App Router) with TypeScript and Tailwind CSS
- **Backend**: FastAPI with SQLModel ORM
- **Database**: Neon Serverless PostgreSQL
- **Authentication**: Better Auth with JWT tokens
- **Structure**: Monorepo with `/frontend` and `/backend` directories

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - User Registration (Priority: P1)

As a new user, I want to create an account so that I can have my own private todo list that persists across sessions.

**Why this priority**: Without user registration, there is no multi-user support. This is the foundational capability that enables all other user-specific features.

**Independent Test**: Navigate to signup page → enter email and password → submit → verify account created and user redirected to dashboard

**Acceptance Scenarios**:

1. **Given** I am on the signup page, **When** I enter a valid email and password (min 8 characters), **Then** my account is created and I am automatically signed in and redirected to the task dashboard
2. **Given** I am on the signup page, **When** I enter an email that already exists, **Then** I see an error message "An account with this email already exists"
3. **Given** I am on the signup page, **When** I enter a password shorter than 8 characters, **Then** I see a validation error before submission
4. **Given** I am on the signup page, **When** I enter an invalid email format, **Then** I see a validation error before submission

---

### User Story 2 - User Sign In (Priority: P1)

As a registered user, I want to sign in to my account so that I can access my personal tasks.

**Why this priority**: Sign-in is required for users to access their tasks after registration. Without this, users cannot return to their data.

**Independent Test**: Navigate to signin page → enter valid credentials → submit → verify redirected to dashboard with user's tasks visible

**Acceptance Scenarios**:

1. **Given** I am on the signin page with valid credentials, **When** I submit the form, **Then** I am authenticated and redirected to the task dashboard
2. **Given** I am on the signin page with invalid credentials, **When** I submit the form, **Then** I see an error message "Invalid email or password"
3. **Given** I am signed in, **When** I close and reopen the browser, **Then** I remain signed in (session persists via JWT)
4. **Given** I am on the signin page, **When** I click "Sign up", **Then** I am redirected to the signup page

---

### User Story 3 - View My Tasks (Priority: P1)

As a signed-in user, I want to see all my tasks so that I can track what I need to do.

**Why this priority**: Viewing tasks is the core functionality users expect immediately after signing in. This validates the entire authentication and data isolation flow.

**Independent Test**: Sign in → verify task list displays only the current user's tasks with correct status indicators

**Acceptance Scenarios**:

1. **Given** I am signed in and have tasks, **When** I view the dashboard, **Then** I see all my tasks with their title, description (if any), and completion status
2. **Given** I am signed in and have no tasks, **When** I view the dashboard, **Then** I see an empty state message "No tasks yet. Create your first task!"
3. **Given** I am signed in, **When** another user creates tasks, **Then** I do not see their tasks in my dashboard
4. **Given** I am signed in, **When** I view the dashboard, **Then** tasks show checkbox indicators: checked for complete, unchecked for incomplete
5. **Given** I am signed in, **When** I view the dashboard, **Then** completed tasks are shown inline with visual distinction (strikethrough/muted styling) rather than hidden or separated

---

### User Story 4 - Create a New Task (Priority: P1)

As a signed-in user, I want to create new tasks so that I can track my work items.

**Why this priority**: Task creation is essential for users to populate their todo list. Combined with viewing, this forms the minimum viable product.

**Independent Test**: Sign in → click "Add Task" → enter title → submit → verify task appears in list

**Acceptance Scenarios**:

1. **Given** I am signed in, **When** I enter a task title and submit, **Then** the task is created and appears in my task list
2. **Given** I am signed in, **When** I enter a task title and optional description and submit, **Then** the task is created with both title and description
3. **Given** I am signed in, **When** I try to create a task with an empty title, **Then** I see a validation error "Title is required"
4. **Given** I am signed in, **When** I create a task, **Then** it is initially marked as incomplete

---

### User Story 5 - Toggle Task Completion (Priority: P2)

As a signed-in user, I want to mark tasks as complete or incomplete so that I can track my progress.

**Why this priority**: Toggling completion is the primary interaction with tasks after creation, enabling users to track progress.

**Independent Test**: Sign in → create a task → click checkbox → verify status changes → click again → verify status reverts

**Acceptance Scenarios**:

1. **Given** I have an incomplete task, **When** I click the checkbox, **Then** the task is marked as complete with visual feedback
2. **Given** I have a complete task, **When** I click the checkbox, **Then** the task is marked as incomplete
3. **Given** I toggle a task's status, **When** I refresh the page, **Then** the status persists

---

### User Story 6 - Update Task Details (Priority: P2)

As a signed-in user, I want to edit my task's title and description so that I can correct or update information.

**Why this priority**: Users need the ability to modify tasks as requirements change or to fix mistakes.

**Independent Test**: Sign in → select a task → click edit → modify title/description → save → verify changes persist

**Acceptance Scenarios**:

1. **Given** I have an existing task, **When** I click edit and change the title, **Then** the new title is saved and displayed
2. **Given** I have an existing task, **When** I click edit and change the description, **Then** the new description is saved and displayed
3. **Given** I am editing a task, **When** I try to save with an empty title, **Then** I see a validation error
4. **Given** I am editing a task, **When** I click cancel, **Then** no changes are saved

---

### User Story 7 - Delete a Task (Priority: P2)

As a signed-in user, I want to delete tasks I no longer need so that I can keep my list clean.

**Why this priority**: Task deletion allows users to manage their list over time by removing completed or irrelevant items.

**Independent Test**: Sign in → select a task → click delete → confirm → verify task is removed from list

**Acceptance Scenarios**:

1. **Given** I have an existing task, **When** I click delete and confirm, **Then** the task is permanently removed from my list
2. **Given** I click delete, **When** a confirmation dialog appears, **Then** I can cancel to keep the task
3. **Given** I delete a task, **When** I refresh the page, **Then** the task remains deleted

---

### User Story 8 - Sign Out (Priority: P3)

As a signed-in user, I want to sign out so that I can secure my account when using shared devices.

**Why this priority**: Sign out is important for security but less critical than core task management features.

**Independent Test**: Sign in → click sign out → verify redirected to signin page → verify cannot access dashboard without signing in again

**Acceptance Scenarios**:

1. **Given** I am signed in, **When** I click "Sign out", **Then** I am signed out and redirected to the signin page
2. **Given** I have signed out, **When** I try to access the dashboard directly, **Then** I am redirected to the signin page
3. **Given** I have signed out, **When** I sign in again, **Then** I see my tasks as before

---

### Edge Cases

- What happens when the user's session expires? → User is redirected to signin page with message "Session expired. Please sign in again."
- What happens when the backend is unavailable? → User sees a friendly error message "Unable to connect. Please try again later." with retry option
- What happens when a user tries to access another user's task by ID manipulation? → API returns 404 (not 403) to prevent information leakage
- What happens when the database connection fails? → API returns 503 with appropriate error message
- What happens when JWT token is invalid or tampered? → Request is rejected with 401, user redirected to signin
- What happens if a user submits extremely long title/description? → Validation limits: title max 200 characters, description max 2000 characters

---

## Requirements *(mandatory)*

### Functional Requirements

#### Frontend Requirements

- **FR-001**: System MUST provide a signup page accessible at `/signup` path
- **FR-002**: System MUST provide a signin page accessible at `/signin` path
- **FR-003**: System MUST provide a protected dashboard page at `/` or `/dashboard` path
- **FR-004**: System MUST redirect unauthenticated users to signin page when accessing protected routes
- **FR-005**: System MUST store JWT token securely on the client (httpOnly cookie preferred)
- **FR-006**: System MUST attach JWT token to all API requests to the backend
- **FR-007**: System MUST handle 401 responses by redirecting to signin page
- **FR-008**: System MUST handle 403 responses by showing access denied message
- **FR-009**: System MUST provide form validation feedback before submission
- **FR-010**: System MUST display loading states during API operations
- **FR-011**: System MUST display success/error notifications for user actions
- **FR-011a**: System MUST display completed tasks inline with visual distinction (strikethrough text, muted colors)

#### Backend Requirements

- **FR-012**: System MUST provide REST API endpoints for task CRUD operations
- **FR-012a**: System MUST return tasks ordered by created_at DESC (newest first) in list endpoints
- **FR-013**: System MUST validate JWT tokens on all protected endpoints
- **FR-014**: System MUST extract user identity from validated JWT token
- **FR-015**: System MUST enforce task ownership - users can only access their own tasks
- **FR-016**: System MUST never accept user_id from client input for task operations
- **FR-017**: System MUST return 401 for invalid/missing authentication
- **FR-018**: System MUST return 404 (not 403) when user tries to access another user's task
- **FR-019**: System MUST validate all input data before processing
- **FR-020**: System MUST use BETTER_AUTH_SECRET for JWT verification (shared with auth provider)

#### Database Requirements

- **FR-021**: System MUST persist tasks with association to user ID
- **FR-022**: System MUST support efficient querying of tasks by user ID
- **FR-023**: System MUST enforce referential integrity between tasks and users
- **FR-024**: System MUST use database-level indexes for user-based queries

#### Authentication Requirements

- **FR-025**: System MUST use Better Auth for user registration and authentication
- **FR-026**: System MUST issue JWT tokens upon successful authentication with 30-day expiration
- **FR-027**: System MUST support email/password authentication
- **FR-028**: System MUST hash passwords securely (handled by Better Auth)
- **FR-029**: System MUST enforce minimum password length of 8 characters

### Key Entities

- **User**: Represents an authenticated user. Managed entirely by Better Auth (no user table in backend). Key attributes: id (UUID), email, created_at. Users own zero or more tasks. Backend only references user_id from JWT claims.

- **Task**: Represents a todo item belonging to a user. Key attributes: id (UUID), title (string, required, max 200 chars), description (string, optional, max 2000 chars), completed (boolean, default false), user_id (foreign key referencing Better Auth user ID), created_at, updated_at. Each task belongs to exactly one user. Tasks are ordered by created_at DESC (newest first) when displayed.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete the signup process in under 30 seconds
- **SC-002**: Users can complete the signin process in under 15 seconds
- **SC-003**: Task list loads within 2 seconds for users with up to 100 tasks
- **SC-004**: System supports at least 100 concurrent users without degradation
- **SC-005**: All CRUD operations complete within 1 second under normal load
- **SC-006**: 100% of task access attempts by non-owners are correctly rejected
- **SC-007**: Users can create, view, update, and delete tasks without page refresh (SPA behavior)
- **SC-008**: Authentication state persists across browser sessions until explicit logout
- **SC-009**: Zero cross-user data leakage - users never see other users' tasks
- **SC-010**: All form validation errors are displayed before form submission

---

## API Endpoints *(reference)*

### Authentication (handled by Better Auth)

| Method | Endpoint           | Description          |
|--------|--------------------|----------------------|
| POST   | /api/auth/signup   | Register new user    |
| POST   | /api/auth/signin   | Authenticate user    |
| POST   | /api/auth/signout  | End user session     |
| GET    | /api/auth/session  | Get current session  |

### Task Management (Backend API)

| Method | Endpoint               | Description                       |
|--------|------------------------|-----------------------------------|
| GET    | /api/tasks             | List all tasks for authenticated user |
| POST   | /api/tasks             | Create new task                   |
| GET    | /api/tasks/{id}        | Get specific task (owner only)    |
| PUT    | /api/tasks/{id}        | Update task (owner only)          |
| PATCH  | /api/tasks/{id}/toggle | Toggle task completion            |
| DELETE | /api/tasks/{id}        | Delete task (owner only)          |

---

## Assumptions

1. Better Auth will be configured on the frontend (Next.js) and the backend will verify JWTs using the shared BETTER_AUTH_SECRET
2. Neon PostgreSQL connection will be managed via environment variables
3. CORS will be configured to allow frontend-backend communication in development and production
4. The application will run in development mode on localhost with frontend on port 3000 and backend on port 8000
5. Email verification is not required for MVP (can be added later)
6. Password reset functionality is not in scope for Phase II
7. The existing Phase I Python code in `/src` will remain for reference but the new backend will be in `/backend`

---

## Out of Scope

- Email verification
- Password reset/recovery
- Social authentication (OAuth providers)
- Task categories or labels
- Task due dates
- Task priority levels
- Sharing tasks between users
- Real-time updates (WebSockets)
- Mobile-specific UI
- Offline support
- Task search functionality
- Bulk task operations

---

## Dependencies

- Better Auth library for Next.js
- Neon PostgreSQL database instance
- BETTER_AUTH_SECRET environment variable shared between frontend and backend
- Node.js 18+ for frontend
- Python 3.11+ for backend
