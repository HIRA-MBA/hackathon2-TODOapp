# Tasks: Advanced Cloud-Native Todo Chatbot (Phase V)

**Input**: Design documents from `/specs/005-cloud-native-doks/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the feature specification. Only verification tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md structure:
- **Backend**: `backend/app/` (FastAPI)
- **Frontend**: `frontend/src/` (Next.js)
- **Services**: `services/{service-name}/app/` (microservices)
- **Helm**: `helm/todo-chatbot/` (Kubernetes deployment)
- **Dapr**: `dapr/components/` (local), `helm/todo-chatbot/templates/dapr/` (production)
- **CI/CD**: `.github/workflows/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, Dapr components, and Docker infrastructure

- [ ] T001 Create services directory structure per plan.md: `services/recurring-task/`, `services/notification/`, `services/websocket/`
- [ ] T002 [P] Initialize recurring-task microservice with FastAPI in `services/recurring-task/app/main.py` and `services/recurring-task/pyproject.toml`
- [ ] T003 [P] Initialize notification microservice with FastAPI in `services/notification/app/main.py` and `services/notification/pyproject.toml`
- [ ] T004 [P] Initialize websocket microservice with FastAPI in `services/websocket/app/main.py` and `services/websocket/pyproject.toml`
- [ ] T005 [P] Create Dockerfile for recurring-task service in `services/recurring-task/Dockerfile`
- [ ] T006 [P] Create Dockerfile for notification service in `services/notification/Dockerfile`
- [ ] T007 [P] Create Dockerfile for websocket service in `services/websocket/Dockerfile`
- [ ] T008 Create local Dapr pub/sub component configuration in `dapr/components/pubsub.yaml` (Kafka/Redpanda)
- [ ] T009 [P] Create local Dapr state store component in `dapr/components/statestore.yaml` (Redis)
- [ ] T010 [P] Create local Dapr config in `dapr/config.yaml`
- [ ] T011 Create `docker-compose.infra.yaml` for local Redpanda and Redis
- [ ] T012 Create `docker-compose.yaml` for all services with Dapr sidecars

**Checkpoint**: Local infrastructure ready for development

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Database Extensions

- [ ] T013 Create RecurrencePattern SQLModel entity in `backend/app/models/recurrence.py` per data-model.md
- [ ] T014 Extend Task model with recurrence fields (`recurrence_id`, `parent_task_id`, `reminder_offset`) in `backend/app/models/task.py`
- [ ] T015 [P] Create NotificationPreference SQLModel entity in `backend/app/models/notification.py`
- [ ] T016 [P] Create ProcessedEvent SQLModel entity for idempotency in `backend/app/models/processed_event.py`
- [ ] T017 Create Alembic migration for Phase V schema changes in `backend/alembic/versions/`
- [ ] T018 Run migration against Neon PostgreSQL and verify schema

### Event Infrastructure

- [ ] T019 Create TaskEvent Pydantic models (CloudEvents format) in `backend/app/models/events.py` per contracts/task-events.yaml
- [ ] T020 [P] Create ReminderEvent Pydantic model in `backend/app/models/events.py`
- [ ] T021 Implement Dapr event publisher service in `backend/app/services/event_publisher.py` with at-least-once guarantee
- [ ] T022 Add dapr-ext-fastapi and dapr SDK dependencies to `backend/pyproject.toml`

### Shared Service Utilities

- [ ] T023 Create idempotent event processor utility in `backend/app/services/idempotency.py` per data-model.md pattern
- [ ] T024 [P] Create correlation ID middleware for structured logging in `backend/app/middleware/correlation.py`
- [ ] T025 [P] Add health check endpoints (`/health`, `/health/ready`) to backend in `backend/app/api/v1/health.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Event-Driven Task Operations (Priority: P1) MVP

**Goal**: When users create, update, or delete tasks, events are published to Redpanda via Dapr pub/sub without blocking the user interaction.

**Independent Test**: Create a task via UI, verify event appears in `task-events` topic using `rpk topic consume task-events`

### Implementation for User Story 1

- [ ] T026 [US1] Integrate event publisher into TaskService for task.created events in `backend/app/services/task_service.py`
- [ ] T027 [US1] Add task.updated event publishing on task modifications in `backend/app/services/task_service.py`
- [ ] T028 [US1] Add task.deleted event publishing on task removal in `backend/app/services/task_service.py`
- [ ] T029 [US1] Add task.completed event publishing (triggers recurring logic) in `backend/app/services/task_service.py`
- [ ] T030 [US1] Implement retry/queue fallback for event publishing failures in `backend/app/services/event_publisher.py`
- [ ] T031 [US1] Add correlation ID propagation to all published events in `backend/app/services/event_publisher.py`
- [ ] T032 [US1] Extend task API endpoints to include recurrence in request/response in `backend/app/api/v1/tasks.py`
- [ ] T033 [US1] Add recurrence CRUD endpoints per api-extensions.yaml in `backend/app/api/v1/tasks.py`

### Verification for User Story 1

- [ ] T034 [US1] Verify event publishing with rpk: create task, consume from `task-events` topic
- [ ] T035 [US1] Verify at-least-once delivery: simulate Redpanda downtime, confirm retry behavior

**Checkpoint**: User Story 1 complete - events flow through Dapr to Redpanda

---

## Phase 4: User Story 2 - Real-Time Task Synchronization (Priority: P1) MVP

**Goal**: Multiple browser tabs/devices receive task updates instantly via WebSocket without manual refresh.

**Independent Test**: Open two browser tabs, create task in tab A, verify it appears in tab B within 2 seconds

### Implementation for User Story 2

- [ ] T036 [US2] Implement WebSocket connection manager in `services/websocket/app/connections.py`
- [ ] T037 [US2] Add JWT token validation for WebSocket connections in `services/websocket/app/auth.py`
- [ ] T038 [US2] Implement WebSocket message protocol (subscribe/unsubscribe/ping) in `services/websocket/app/main.py` per websocket.yaml contract
- [ ] T039 [US2] Create Dapr subscription handler for `task-updates` topic in `services/websocket/app/handlers.py`
- [ ] T040 [US2] Implement user-scoped message filtering in `services/websocket/app/filters.py`
- [ ] T041 [US2] Add reconnection with state recovery support in `services/websocket/app/connections.py`
- [ ] T042 [US2] Publish task-updates events from backend after task operations in `backend/app/services/event_publisher.py`
- [ ] T043 [P] [US2] Create WebSocket client hook in frontend: `frontend/src/hooks/useRealTimeSync.ts`
- [ ] T044 [P] [US2] Create WebSocket connection manager in frontend: `frontend/src/lib/websocket.ts`
- [ ] T045 [US2] Integrate real-time sync hook into task list component in `frontend/src/components/`
- [ ] T046 [US2] Add connection status indicator to frontend UI

### Verification for User Story 2

- [ ] T047 [US2] Verify two-tab sync: create task in tab A, confirm appearance in tab B within 2 seconds
- [ ] T048 [US2] Verify reconnection: disconnect WebSocket, reconnect, confirm missed updates received

**Checkpoint**: User Story 2 complete - real-time sync works across browser tabs

---

## Phase 5: User Story 5 - Automated Cloud Deployment (Priority: P1) MVP

**Goal**: Code pushed to main branch automatically builds, tests, and deploys to DOKS via GitHub Actions.

**Independent Test**: Push commit to main, verify new version running on DOKS within 10 minutes

### Implementation for User Story 5

- [ ] T049 [US5] Create GitHub Actions workflow for CI in `.github/workflows/ci.yaml` (lint, test, build)
- [ ] T050 [US5] Create GitHub Actions workflow for DOKS deployment in `.github/workflows/deploy-doks.yaml` per research.md
- [ ] T051 [US5] Configure Docker image build and push to DOCR in deploy workflow
- [ ] T052 [US5] Extend Helm chart with recurring-task deployment in `helm/todo-chatbot/templates/recurring-task-deployment.yaml`
- [ ] T053 [P] [US5] Add notification service deployment to Helm in `helm/todo-chatbot/templates/notification-deployment.yaml`
- [ ] T054 [P] [US5] Add websocket service deployment to Helm in `helm/todo-chatbot/templates/websocket-deployment.yaml`
- [ ] T055 [US5] Create Dapr pub/sub component for DOKS (SASL_SSL) in `helm/todo-chatbot/templates/dapr/pubsub.yaml`
- [ ] T056 [P] [US5] Create Dapr state store for DOKS in `helm/todo-chatbot/templates/dapr/statestore.yaml`
- [ ] T057 [P] [US5] Create Dapr secret store for DOKS in `helm/todo-chatbot/templates/dapr/secretstore.yaml`
- [ ] T058 [US5] Create DOKS-specific values file in `helm/values-doks.yaml`
- [ ] T059 [US5] Configure rolling update strategy with zero-downtime in Helm deployments
- [ ] T060 [US5] Add Kubernetes secrets for Redpanda SASL credentials, Neon connection

### Verification for User Story 5

- [ ] T061 [US5] Verify CI workflow: push branch, confirm tests run and images build
- [ ] T062 [US5] Verify deployment: push to main, confirm DOKS rollout completes within 10 minutes
- [ ] T063 [US5] Verify zero-downtime: monitor during deployment, confirm no failed requests

**Checkpoint**: User Story 5 complete - automated CI/CD to DOKS operational

---

## Phase 6: User Story 3 - Recurring Task Automation (Priority: P2)

**Goal**: When a recurring task is completed, the system automatically creates the next instance based on the schedule.

**Independent Test**: Create daily recurring task, complete it, verify new task instance created for next day

### Implementation for User Story 3

- [ ] T064 [US3] Implement recurrence pattern calculator using dateutil.rrule in `services/recurring-task/app/recurrence.py`
- [ ] T065 [US3] Create Dapr subscription for `task-events` topic in `services/recurring-task/app/main.py`
- [ ] T066 [US3] Implement event handler for task.completed events in `services/recurring-task/app/handlers.py`
- [ ] T067 [US3] Add idempotent processing using ProcessedEvent table in `services/recurring-task/app/handlers.py`
- [ ] T068 [US3] Implement next task instance creation via backend API call in `services/recurring-task/app/handlers.py`
- [ ] T069 [US3] Handle recurrence end conditions (end_date, max_occurrences) in `services/recurring-task/app/recurrence.py`
- [ ] T070 [US3] Add recurrence pattern validation in backend API in `backend/app/api/v1/tasks.py`
- [ ] T071 [P] [US3] Add recurrence UI components to frontend in `frontend/src/components/`
- [ ] T072 [US3] Add recurring task instances endpoint per api-extensions.yaml in `backend/app/api/v1/tasks.py`

### Verification for User Story 3

- [ ] T073 [US3] Verify daily recurrence: complete daily task, confirm next instance created
- [ ] T074 [US3] Verify weekly recurrence: complete weekly task on Monday, confirm next instance for following Monday
- [ ] T075 [US3] Verify end condition: complete task at max_occurrences, confirm no new instance created

**Checkpoint**: User Story 3 complete - recurring tasks automated

---

## Phase 7: User Story 4 - Proactive Notifications (Priority: P2)

**Goal**: Users receive notifications when tasks are due soon, without missing deadlines.

**Independent Test**: Create task due in 5 minutes, verify notification logged when reminder triggers

### Implementation for User Story 4

- [ ] T076 [US4] Create Dapr subscription for `reminders` topic in `services/notification/app/main.py`
- [ ] T077 [US4] Implement reminder event handler in `services/notification/app/handlers.py`
- [ ] T078 [US4] Create notification preference service in `backend/app/services/notification_service.py`
- [ ] T079 [US4] Add notification preferences API endpoints per api-extensions.yaml in `backend/app/api/v1/notifications.py`
- [ ] T080 [US4] Implement reminder scheduling logic in `services/notification/app/scheduler.py`
- [ ] T081 [US4] Implement notification delivery simulation (log email/push) in `services/notification/app/handlers.py`
- [ ] T082 [US4] Respect quiet hours and user preferences in `services/notification/app/handlers.py`
- [ ] T083 [US4] Implement reminder batching for simultaneous notifications in `services/notification/app/handlers.py`
- [ ] T084 [US4] Add reminder settings to backend API per api-extensions.yaml in `backend/app/api/v1/tasks.py`
- [ ] T085 [US4] Publish reminder events from backend scheduler in `backend/app/services/reminder_publisher.py`
- [ ] T086 [P] [US4] Add notification preferences UI to frontend in `frontend/src/components/`

### Verification for User Story 4

- [ ] T087 [US4] Verify reminder trigger: create task due in 35 minutes, confirm notification at 30-min mark
- [ ] T088 [US4] Verify quiet hours: set quiet hours, confirm notification deferred

**Checkpoint**: User Story 4 complete - proactive notifications operational

---

## Phase 8: User Story 6 - Operational Visibility (Priority: P3)

**Goal**: Operators can view health and status of all Dapr components and services.

**Independent Test**: Run `dapr dashboard`, verify all components show healthy status

### Implementation for User Story 6

- [ ] T089 [US6] Add health endpoints to recurring-task service in `services/recurring-task/app/main.py`
- [ ] T090 [P] [US6] Add health endpoints to notification service in `services/notification/app/main.py`
- [ ] T091 [P] [US6] Add health endpoints to websocket service in `services/websocket/app/main.py`
- [ ] T092 [US6] Configure Kubernetes liveness and readiness probes in all Helm deployments
- [ ] T093 [US6] Add structured JSON logging with correlation IDs to all services
- [ ] T094 [US6] Document operational runbook in `docs/operations/runbook.md`

### Verification for User Story 6

- [ ] T095 [US6] Verify Dapr dashboard: run `dapr dashboard`, confirm all components healthy
- [ ] T096 [US6] Verify pod health: run `kubectl get pods`, confirm all Running with 0 restarts

**Checkpoint**: User Story 6 complete - operational visibility established

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, documentation, and validation

- [ ] T097 [P] Update backend README with Phase V features in `backend/README.md`
- [ ] T098 [P] Update frontend README with WebSocket integration in `frontend/README.md`
- [ ] T099 Validate quickstart.md instructions end-to-end
- [ ] T100 Run full system integration test: create recurring task, complete, verify new instance, receive notification
- [ ] T101 Performance validation: verify 500ms task CRUD, 2s real-time sync latency
- [ ] T102 Load test: verify 500 concurrent WebSocket connections

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1, US2, US5 are P1 priority - complete for MVP
  - US3, US4 are P2 priority - add after MVP
  - US6 is P3 priority - operational polish
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - Foundation for all event-driven features
- **User Story 2 (P1)**: Can start after US1 (needs events flowing to consume)
- **User Story 5 (P1)**: Can start after Foundational - Infrastructure for deployment
- **User Story 3 (P2)**: Requires US1 complete (subscribes to task-events)
- **User Story 4 (P2)**: Requires US1 complete (publishes to reminders topic)
- **User Story 6 (P3)**: Can start after Foundational - No story dependencies

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Backend before frontend (for API-dependent features)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes:
  - US1 and US5 can start in parallel
  - US2 can start once US1 event publishing works
  - US3 and US4 can start in parallel after US1
  - US6 can run anytime after Foundational
- Frontend tasks marked [P] within a story can run in parallel with backend

---

## Parallel Example: Phase 1 Setup

```bash
# Launch all service initializations together:
Task: "Initialize recurring-task microservice in services/recurring-task/"
Task: "Initialize notification microservice in services/notification/"
Task: "Initialize websocket microservice in services/websocket/"

# Launch all Dockerfiles together:
Task: "Create Dockerfile for recurring-task service"
Task: "Create Dockerfile for notification service"
Task: "Create Dockerfile for websocket service"
```

## Parallel Example: Phase 5 Helm Templates

```bash
# Launch all Helm template creation together:
Task: "Add notification service deployment to Helm"
Task: "Add websocket service deployment to Helm"
Task: "Create Dapr state store for DOKS"
Task: "Create Dapr secret store for DOKS"
```

---

## Implementation Strategy

### MVP First (User Stories 1, 2, 5)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Event-Driven Task Operations)
4. Complete Phase 4: User Story 2 (Real-Time Sync)
5. Complete Phase 5: User Story 5 (Automated Deployment)
6. **STOP and VALIDATE**: Full MVP functional on DOKS
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational Foundation ready
2. Add User Story 1 Test event flow Deploy (Events work!)
3. Add User Story 2 Test real-time sync Deploy (Real-time works!)
4. Add User Story 5 Test CI/CD Deploy to DOKS (Production ready!)
5. Add User Story 3 Test recurring Deploy (Recurring works!)
6. Add User Story 4 Test notifications Deploy (Notifications work!)
7. Add User Story 6 Test observability Deploy (Ops ready!)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Event Publishing)
   - Developer B: User Story 5 (CI/CD + Helm)
   - Developer C: User Story 6 (Health + Observability)
3. After US1 complete:
   - Developer A: User Story 2 (WebSocket)
   - Developer B: User Story 3 (Recurring)
   - Developer C: User Story 4 (Notifications)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 102 |
| **Phase 1 (Setup)** | 12 tasks |
| **Phase 2 (Foundational)** | 13 tasks |
| **User Story 1 (Events)** | 10 tasks |
| **User Story 2 (WebSocket)** | 13 tasks |
| **User Story 5 (CI/CD)** | 15 tasks |
| **User Story 3 (Recurring)** | 12 tasks |
| **User Story 4 (Notifications)** | 13 tasks |
| **User Story 6 (Observability)** | 8 tasks |
| **Phase 9 (Polish)** | 6 tasks |
| **MVP Scope** | US1 + US2 + US5 (50 tasks) |
| **Parallel Opportunities** | 34 tasks marked [P] |
