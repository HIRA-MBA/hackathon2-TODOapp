# Feature Specification: Advanced Cloud-Native Todo Chatbot (Phase V)

**Feature Branch**: `005-cloud-native-doks`
**Created**: 2026-01-26
**Status**: Draft
**Input**: User description: "Evolve the Phase IV Todo App into a production-ready, event-driven system deployed on DigitalOcean Kubernetes (DOKS) with Dapr and Redpanda messaging."

---

## Clarifications

### Session 2026-01-26

- Q: How do recurring tasks stop recurring? → A: Explicit end date or occurrence count set when creating the recurrence
- Q: Which container registry for Docker images? → A: DigitalOcean Container Registry (DOCR) for native DOKS integration
- Q: What observability strategy for distributed tracing? → A: Dapr built-in observability with structured JSON logs and correlation IDs

---

## Overview

Phase V transforms the existing Todo Chatbot application from a monolithic deployment into a fully event-driven, microservices-based architecture. The system will leverage Dapr (Distributed Application Runtime) for service-to-service communication, pub/sub messaging, and state management, deployed on DigitalOcean Kubernetes (DOKS) with automated CI/CD pipelines.

The core value proposition is enabling real-time collaboration, automated recurring tasks, and proactive notifications—all while maintaining the simplicity of the existing user experience.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Event-Driven Task Operations (Priority: P1)

As a user, when I create, update, or delete a task, the system publishes events that trigger downstream services (notifications, real-time sync, recurring task creation) without blocking my interaction.

**Why this priority**: This is the foundational event-driven capability. Without events flowing through the system, no other microservice can react. This must work before any other feature can be verified.

**Independent Test**: Can be fully tested by creating a task via the UI and verifying the event appears in the Redpanda topic using `rpk topic consume task-events`. Delivers value by decoupling task operations from downstream processing.

**Acceptance Scenarios**:

1. **Given** I am logged in, **When** I create a new task, **Then** a `task.created` event is published to the `task-events` topic containing task ID, title, user ID, and timestamp.
2. **Given** I have an existing task, **When** I mark it as completed, **Then** a `task.updated` event is published with the updated completion status.
3. **Given** I have an existing task, **When** I delete it, **Then** a `task.deleted` event is published with the task ID.
4. **Given** the messaging system is temporarily unavailable, **When** I perform a task operation, **Then** the operation succeeds locally and the event is queued for later delivery (at-least-once guarantee).

---

### User Story 2 - Real-Time Task Synchronization (Priority: P1)

As a user with multiple devices or browser tabs open, when any task changes occur (by me or collaborators), I see updates reflected instantly without manually refreshing.

**Why this priority**: Real-time sync is essential for a modern collaborative application. Users expect changes to appear immediately across all connected clients.

**Independent Test**: Can be tested by opening two browser tabs, creating a task in one tab, and verifying it appears in the other tab within 2 seconds. Delivers value by eliminating the need for manual refresh.

**Acceptance Scenarios**:

1. **Given** I have two browser tabs open to the dashboard, **When** I create a task in tab A, **Then** the task appears in tab B within 2 seconds without refreshing.
2. **Given** another user shares a task list with me, **When** they modify a shared task, **Then** I see the update in real-time.
3. **Given** I lose WebSocket connection temporarily, **When** the connection is restored, **Then** I receive any missed updates since disconnection.
4. **Given** 100 concurrent users are connected, **When** a task is updated, **Then** all connected clients receive the update within 3 seconds.

---

### User Story 3 - Recurring Task Automation (Priority: P2)

As a user with recurring responsibilities, when I complete a recurring task, the system automatically creates the next instance based on my defined schedule, so I never have to manually recreate routine tasks.

**Why this priority**: Recurring tasks are a significant productivity feature but depend on the event system (P1) being operational first.

**Independent Test**: Can be tested by creating a daily recurring task, completing it, and verifying a new task instance is created for the next day. Delivers value by automating repetitive task management.

**Acceptance Scenarios**:

1. **Given** I have a task marked as "daily recurring", **When** I complete it, **Then** a new task instance is automatically created for the next day with the same title and properties.
2. **Given** I have a task marked as "weekly recurring on Mondays", **When** I complete it on Monday, **Then** a new task is created for the following Monday.
3. **Given** I have a recurring task, **When** I delete the recurring task (not just complete it), **Then** no future instances are created.
4. **Given** I modify the recurrence pattern of a task, **When** I complete it, **Then** the new instance follows the updated pattern.

---

### User Story 4 - Proactive Notifications (Priority: P2)

As a user with upcoming deadlines, I receive notifications (simulated push/email) when tasks are due soon or when important events occur, so I never miss a deadline.

**Why this priority**: Notifications add significant user value but are not core to task management. They enhance the experience rather than enable it.

**Independent Test**: Can be tested by creating a task with a due date 5 minutes in the future and verifying a notification is logged/simulated when the reminder triggers. Delivers value by proactively alerting users.

**Acceptance Scenarios**:

1. **Given** I have a task due in 1 hour, **When** the reminder time arrives (30 minutes before default), **Then** a notification event is published to the `reminders` topic.
2. **Given** I have notification preferences set to "email only", **When** a reminder triggers, **Then** the notification service simulates sending an email (logs the action).
3. **Given** I have disabled notifications for a specific task, **When** that task's reminder time arrives, **Then** no notification is sent for that task.
4. **Given** multiple tasks are due at the same time, **When** reminders trigger, **Then** each task generates its own notification event.

---

### User Story 5 - Automated Cloud Deployment (Priority: P1)

As a developer, when I push code to the main branch, the system automatically builds, tests, and deploys to DigitalOcean Kubernetes, so I can deliver features quickly and reliably.

**Why this priority**: Without automated deployment, no other features can be delivered to production. This is infrastructure-critical.

**Independent Test**: Can be tested by pushing a commit to main and verifying the new version is running on DOKS within 10 minutes. Delivers value by enabling continuous delivery.

**Acceptance Scenarios**:

1. **Given** I push a commit to the `main` branch, **When** GitHub Actions workflow triggers, **Then** Docker images are built and pushed to a container registry.
2. **Given** images are built successfully, **When** the deployment step runs, **Then** Helm upgrades the release on DOKS with the new images.
3. **Given** a deployment is in progress, **When** I check `kubectl get pods`, **Then** I see a rolling update with zero-downtime.
4. **Given** a deployment fails health checks, **When** the rollout times out, **Then** Kubernetes automatically rolls back to the previous version.

---

### User Story 6 - Operational Visibility (Priority: P3)

As an operator, I can view the health and connectivity of all Dapr components and services through dashboards and CLI tools, so I can quickly diagnose issues.

**Why this priority**: Operational tooling is important for maintenance but not required for core functionality.

**Independent Test**: Can be tested by running `dapr dashboard` and verifying all components show healthy status. Delivers value by enabling rapid troubleshooting.

**Acceptance Scenarios**:

1. **Given** the system is deployed, **When** I run `dapr dashboard`, **Then** I see all Dapr components (pub/sub, state store, secret store) in healthy status.
2. **Given** the system is deployed, **When** I run `kubectl get pods`, **Then** all service pods and Dapr sidecars show Running status.
3. **Given** a service is failing, **When** I view Dapr dashboard, **Then** I can see error counts and failed invocations for that service.

---

### Edge Cases

- What happens when Redpanda is unavailable during task creation? → Task succeeds locally; event is retried with exponential backoff.
- How does the system handle duplicate events (at-least-once delivery)? → Consumers use idempotency keys to prevent duplicate processing.
- What if WebSocket connection drops during a task update? → Client reconnects automatically and fetches missed updates.
- What if a recurring task service crashes mid-processing? → Dapr ensures message redelivery; idempotent handlers prevent duplicates.
- What if GitHub Actions deployment fails? → Workflow notifies via GitHub status; manual rollback instructions documented.

---

## Requirements *(mandatory)*

### Functional Requirements

**Event Publishing (Task Service)**

- **FR-001**: System MUST publish a `task.created` event when a new task is created, containing task ID, title, description, due date, user ID, recurrence pattern, and timestamp.
- **FR-002**: System MUST publish a `task.updated` event when a task is modified, containing task ID, changed fields, and timestamp.
- **FR-003**: System MUST publish a `task.deleted` event when a task is deleted, containing task ID and timestamp.
- **FR-004**: System MUST use Dapr Pub/Sub component for all event publishing (no direct Kafka client libraries).
- **FR-005**: System MUST guarantee at-least-once delivery for all events with configurable retry policies.

**Real-Time Synchronization (WebSocket Service)**

- **FR-006**: System MUST maintain WebSocket connections to all active browser clients.
- **FR-007**: System MUST subscribe to `task-updates` topic and broadcast relevant updates to connected clients.
- **FR-008**: System MUST filter updates so users only receive events for their own tasks or shared tasks.
- **FR-009**: System MUST support reconnection with state recovery for clients that temporarily disconnect.
- **FR-010**: System MUST handle at least 500 concurrent WebSocket connections per service instance.

**Recurring Task Service**

- **FR-011**: System MUST subscribe to `task-events` topic and filter for completed recurring tasks.
- **FR-012**: System MUST create a new task instance when a recurring task is completed, with the due date calculated from the recurrence pattern.
- **FR-013**: System MUST support recurrence patterns: daily, weekly (specific days), monthly (specific date), and custom intervals, with mandatory end condition (end date or max occurrence count).
- **FR-014**: System MUST NOT create new instances when a recurring task is deleted (only on completion).
- **FR-015**: System MUST process recurring task events idempotently to handle redelivery.

**Notification Service**

- **FR-016**: System MUST subscribe to `reminders` topic for notification triggers.
- **FR-017**: System MUST simulate notification delivery by logging the notification details (email/push simulation).
- **FR-018**: System MUST respect user notification preferences (enabled/disabled, channels).
- **FR-019**: System MUST publish reminder events 30 minutes before task due date by default (configurable per task).
- **FR-020**: System MUST batch multiple simultaneous reminders to avoid notification flooding.

**Deployment & Infrastructure**

- **FR-021**: System MUST deploy to DigitalOcean Kubernetes (DOKS) using Helm charts.
- **FR-022**: System MUST use GitHub Actions for CI/CD with automatic deployment on main branch push, pushing images to DigitalOcean Container Registry (DOCR).
- **FR-023**: System MUST store all secrets (API keys, database URLs) in Kubernetes Secrets accessed via Dapr Secret Store.
- **FR-024**: System MUST connect to Redpanda Cloud using SASL_SSL authentication.
- **FR-025**: System MUST connect to Neon PostgreSQL for persistent storage.
- **FR-026**: System MUST use `doctl` CLI for DigitalOcean infrastructure management in automation scripts.

**Authentication & Authorization**

- **FR-027**: System MUST reuse Better Auth from Phase II for user authentication.
- **FR-028**: System MUST include user context in all published events for authorization filtering.
- **FR-029**: System MUST validate JWT tokens for WebSocket connections.

**Observability**

- **FR-030**: System MUST emit structured JSON logs from all services with Dapr correlation IDs for request tracing.
- **FR-031**: System MUST propagate correlation IDs across all event-driven message flows for end-to-end traceability.

### Key Entities

- **TaskEvent**: Represents a domain event for task operations. Contains event type (created/updated/deleted), task data snapshot, user ID, timestamp, and correlation ID for tracing.
- **ReminderEvent**: Represents a scheduled notification trigger. Contains task reference, user ID, notification channels, and scheduled time.
- **RecurrencePattern**: Defines the repeat schedule for a task. Contains frequency (daily/weekly/monthly/custom), interval, specific days/dates, and end condition (either end date or max occurrence count, required).
- **NotificationPreference**: User settings for notification delivery. Contains enabled channels (email/push), quiet hours, and per-task overrides.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Task CRUD operations complete in under 500ms from user action to UI confirmation, regardless of downstream event processing.
- **SC-002**: Real-time updates are delivered to all connected clients within 2 seconds of the originating action.
- **SC-003**: Recurring task instances are created within 10 seconds of the parent task being completed.
- **SC-004**: Notification events are generated within 1 minute of the scheduled reminder time.
- **SC-005**: System supports 500 concurrent users with real-time sync enabled without degradation.
- **SC-006**: Automated deployment completes within 10 minutes from push to production availability.
- **SC-007**: Zero-downtime deployments achieve 100% availability during rollout (no failed requests).
- **SC-008**: All Dapr components show healthy status in `dapr dashboard` after deployment.
- **SC-009**: All service pods show Running status with 0 restarts after 5 minutes of deployment.
- **SC-010**: Event delivery achieves 99.9% reliability (measured over 24 hours of operation).

---

## Assumptions

- Redpanda Cloud account and cluster are pre-provisioned with SASL credentials available.
- DigitalOcean account with DOKS cluster already created or will be created via doctl during setup.
- Neon PostgreSQL database from Phase II/III/IV is reused without schema changes for core task data.
- Better Auth session tokens are valid across all services (shared secret configuration).
- GitHub repository has Actions enabled with appropriate secrets configured (DO token, registry credentials).
- Users have modern browsers supporting WebSocket connections (Chrome, Firefox, Safari, Edge).
- Dapr runtime version 1.12+ is available in the DOKS cluster.

---

## Out of Scope

- Local database deployment (must use managed Neon PostgreSQL).
- Manual deployment scripts (must use GitHub Actions for all deployments).
- Custom authentication system (reuse Better Auth from Phase II).
- Direct Kafka client library usage (must use Dapr Pub/Sub abstraction exclusively).
- Actual email/SMS delivery integration (notifications are simulated/logged only).
- Mobile push notification infrastructure (simulated only in this phase).
- Multi-region deployment or disaster recovery configurations.
- Cost optimization, resource auto-scaling policies, or spot instances.
- Task sharing/collaboration features (events include user context but sharing logic is not implemented).

---

## Dependencies

- **Phase IV**: Kubernetes deployment knowledge and Helm charts structure (to be extended for DOKS).
- **Phase II/III**: Better Auth integration, existing API routes, and task data model.
- **External Services**: Redpanda Cloud, Neon PostgreSQL, DigitalOcean DOKS, GitHub Actions.
- **Tooling**: Dapr CLI (v1.12+), kubectl, helm (v3+), doctl, rpk (Redpanda CLI).

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Redpanda Cloud connectivity issues | High - Events not delivered | Implement circuit breaker pattern and local queue fallback |
| Dapr sidecar injection failures | High - Services cannot communicate | Pre-test Dapr installation in dev cluster; document manual injection steps |
| WebSocket scaling limits | Medium - Real-time sync degraded under load | Configure horizontal pod autoscaling; use sticky sessions for connection affinity |
| GitHub Actions secrets exposure | High - Security breach | Use GitHub encrypted secrets; implement secret rotation policy |
| DOKS cluster resource exhaustion | Medium - Deployments fail | Set resource requests/limits; monitor via DigitalOcean metrics dashboard |
| Event ordering not guaranteed | Medium - Data consistency issues | Use correlation IDs and timestamps; design consumers to handle out-of-order events |
