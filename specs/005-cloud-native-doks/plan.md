# Implementation Plan: Advanced Cloud-Native Todo Chatbot (Phase V)

**Branch**: `005-cloud-native-doks` | **Date**: 2026-02-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-cloud-native-doks/spec.md`

## Summary

Transform the Phase IV Todo application into an event-driven microservices architecture deployed on DigitalOcean Kubernetes (DOKS). The system will use Dapr for pub/sub messaging via Redpanda Cloud, enabling real-time task synchronization, recurring task automation, and proactive notifications. CI/CD will be fully automated via GitHub Actions with zero-downtime deployments.

## Technical Context

**Language/Version**: Python 3.13+ (Backend/Services), TypeScript/Node 20+ (Frontend)
**Primary Dependencies**: FastAPI 0.115+, SQLModel, Dapr SDK 1.12+, Next.js 15+, Better Auth
**Storage**: Neon Serverless PostgreSQL (existing), Dapr State Store (Redis-compatible)
**Testing**: pytest (backend), Vitest (frontend), rpk (Redpanda verification)
**Target Platform**: DigitalOcean Kubernetes (DOKS) with Dapr runtime
**Project Type**: Web application (frontend + backend + 3 microservices)
**Performance Goals**: 500ms task CRUD, 2s real-time sync, 500 concurrent WebSocket users
**Constraints**: At-least-once event delivery, zero-downtime deployments, Dapr-only pub/sub (no direct Kafka clients)
**Scale/Scope**: 500 concurrent users, 3 Redpanda topics, 4 services (backend + 3 microservices)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Spec-Driven Only | PASS | All implementation derived from `/specs/005-cloud-native-doks/spec.md` |
| II. Clean Architecture | PASS | Frontend (Next.js) / Backend (FastAPI) / Services (Dapr microservices) / Database (Neon PostgreSQL) |
| III. Accuracy | PASS | 31 functional requirements with testable acceptance criteria in spec |
| IV. Reproducibility | PASS | Helm charts + GitHub Actions CI/CD + DOKS deployment |

**Technology Standards Compliance:**

| Required | Actual | Status |
|----------|--------|--------|
| Python 3.13+ | Python 3.13+ | PASS |
| FastAPI 0.115+ | FastAPI 0.115+ | PASS |
| SQLModel | SQLModel | PASS |
| Neon PostgreSQL | Neon PostgreSQL | PASS |
| Next.js 15+ | Next.js 15+ | PASS |
| Better Auth | Better Auth (reused from Phase II) | PASS |
| Docker | Docker | PASS |
| Kubernetes | DOKS | PASS |
| Helm | Helm | PASS |

**Gate Result: PASS** - Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/005-cloud-native-doks/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts)
│   ├── task-events.yaml # CloudEvents schema for task events
│   ├── websocket.yaml   # WebSocket message protocol
│   └── api-extensions.yaml # New API endpoints
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/              # FastAPI routes (existing + event publishing)
│   │   └── v1/
│   │       └── tasks.py  # Extended with Dapr pub/sub
│   ├── models/           # SQLModel entities (existing + events)
│   │   ├── task.py       # Extended with recurrence fields
│   │   └── events.py     # NEW: Event schemas
│   ├── services/         # Business logic + Dapr integration
│   │   ├── task_service.py
│   │   └── event_publisher.py  # NEW: Dapr pub/sub client
│   └── dapr/             # NEW: Dapr component configurations (local dev)
│       ├── pubsub.yaml
│       └── config.yaml
├── tests/
│   ├── unit/
│   └── integration/
├── Dockerfile
└── pyproject.toml

frontend/
├── src/
│   ├── app/              # Next.js App Router (existing)
│   ├── components/       # React components (existing)
│   ├── lib/
│   │   └── websocket.ts  # NEW: WebSocket client
│   └── hooks/
│       └── useRealTimeSync.ts  # NEW: Real-time sync hook
├── tests/
├── Dockerfile
└── package.json

services/
├── recurring-task/       # NEW: Recurring task microservice
│   ├── app/
│   │   ├── main.py       # FastAPI app with Dapr subscriber
│   │   ├── handlers.py   # Event handlers for recurring logic
│   │   └── recurrence.py # Recurrence pattern calculator
│   ├── Dockerfile
│   └── pyproject.toml
├── notification/         # NEW: Notification microservice
│   ├── app/
│   │   ├── main.py       # FastAPI app with Dapr subscriber
│   │   ├── handlers.py   # Notification simulation handlers
│   │   └── scheduler.py  # Reminder scheduling logic
│   ├── Dockerfile
│   └── pyproject.toml
└── websocket/            # NEW: WebSocket relay service
    ├── app/
    │   ├── main.py       # FastAPI + WebSocket + Dapr subscriber
    │   ├── connections.py # Connection manager
    │   └── filters.py    # User-scoped message filtering
    ├── Dockerfile
    └── pyproject.toml

helm/
├── todo-chatbot/         # Existing Helm chart (extend)
│   ├── Chart.yaml
│   ├── templates/
│   │   ├── backend-deployment.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── recurring-task-deployment.yaml   # NEW
│   │   ├── notification-deployment.yaml     # NEW
│   │   ├── websocket-deployment.yaml        # NEW
│   │   └── dapr/                            # NEW
│   │       ├── pubsub.yaml
│   │       ├── statestore.yaml
│   │       └── secretstore.yaml
│   └── values.yaml
└── values-doks.yaml      # NEW: DOKS-specific values

.github/
└── workflows/
    └── deploy-doks.yaml  # NEW: GitHub Actions CI/CD

dapr/
├── components/           # Local Dapr component configs
│   ├── pubsub.yaml
│   ├── statestore.yaml
│   └── secretstore.yaml
└── config.yaml           # Dapr configuration
```

**Structure Decision**: Extended web application structure with 3 new microservices (recurring-task, notification, websocket) following the same FastAPI pattern as the main backend. Dapr components configured via Helm for Kubernetes deployment.

## Complexity Tracking

| Addition | Justification | Simpler Alternative Rejected |
|----------|---------------|------------------------------|
| 3 new microservices | Event-driven architecture requires separate consumers for isolation and independent scaling | Monolith would couple all event handlers, preventing independent deployment |
| Dapr sidecars | Abstracts messaging complexity, provides retries, circuit breaking, observability | Direct Kafka/Redpanda clients add complexity and vendor lock-in |
| GitHub Actions CI/CD | Required by spec FR-022 (no manual deployments) | Manual deployments explicitly out of scope |
| WebSocket service | Real-time sync (FR-006-010) requires dedicated connection management | Polling would not meet 2-second latency requirement |

---

## Phase 0: Research

*See [research.md](./research.md) for detailed findings.*

### Research Areas

1. **Dapr Pub/Sub with Redpanda Cloud** - SASL_SSL configuration patterns
2. **WebSocket scaling on Kubernetes** - Sticky sessions, HPA, connection limits
3. **GitHub Actions to DOKS** - doctl authentication, Helm deployment workflow
4. **Dapr Secret Store** - Kubernetes secrets integration
5. **CloudEvents schema design** - Event envelope format for task events
6. **Recurrence pattern calculation** - RFC 5545 (iCalendar) implementation

---

## Phase 1: Design

*See [data-model.md](./data-model.md) for entity definitions.*
*See [contracts/](./contracts/) for API specifications.*
*See [quickstart.md](./quickstart.md) for development setup.*

### Key Design Decisions

1. **Event Format**: CloudEvents v1.0 specification for all Dapr pub/sub messages
2. **Topic Strategy**: 3 topics (task-events, reminders, task-updates) with consumer groups per service
3. **WebSocket Protocol**: JSON messages with `type` field discrimination
4. **Idempotency**: Event ID + consumer-side deduplication via processed event tracking table
5. **Recurrence Calculation**: RFC 5545 (iCalendar) compatible patterns with `python-dateutil` rrule

---

## Post-Design Constitution Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Only | PASS | All designs derived from spec.md FRs |
| II. Clean Architecture | PASS | Clear service boundaries with Dapr abstraction |
| III. Accuracy | PASS | All 31 FRs addressed in design artifacts |
| IV. Reproducibility | PASS | Helm + GitHub Actions = fully reproducible |

**Final Gate: PASS** - Ready for `/sp.tasks`.
