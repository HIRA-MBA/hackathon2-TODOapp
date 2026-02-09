# Cloud Native Todo Chatbot

A multi-phase hackathon project demonstrating the evolution of a simple CLI application into a full-stack, AI-powered, event-driven, multi-cloud Kubernetes application.

## Project Overview

This project showcases progressive software development through five distinct phases:

| Phase | Name | Description | Status |
|-------|------|-------------|--------|
| I | In-Memory CLI | Python command-line todo app | Completed |
| II | Full-Stack Web | Next.js + FastAPI with PostgreSQL | Completed |
| III | AI Chatbot | Natural language task management with MCP | Completed |
| IV | Kubernetes | Local deployment with Minikube + Helm | Completed |
| V | Cloud-Native | Event-driven microservices on multi-cloud K8s | Completed |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Frontend   │◄───►│   Backend    │────►│   Redpanda      │
│  (Next.js)   │     │  (FastAPI)   │     │  (Pub/Sub)      │
└──────┬───────┘     └──────┬───────┘     └───────┬─────────┘
       │                    │                     │
       │              ┌─────┴──────┐    ┌─────────┼──────────┐
       │              │  Neon DB   │    │         │          │
       │              │ (Postgres) │    ▼         ▼          ▼
       │              └────────────┘  ┌──────┐ ┌──────┐ ┌──────────┐
       │                              │Recur.│ │Notif.│ │WebSocket │
       └──────────────────────────────│Task  │ │Svc   │ │  Svc     │
                          WebSocket   └──────┘ └──────┘ └──────────┘
                                        Dapr Sidecars (pub/sub, state, secrets)
```

## Tech Stack

### Frontend
- **Framework**: Next.js 15.1, React 19, TypeScript 5.7
- **Styling**: Tailwind CSS 3.4
- **AI/Chat**: ChatKit 1.4.1 (OpenAI-powered)
- **Real-Time**: WebSocket client with auto-reconnection
- **Authentication**: Better Auth

### Backend
- **Framework**: FastAPI 0.115+
- **Language**: Python 3.13+
- **ORM**: SQLModel with asyncpg
- **MCP Server**: FastMCP 2.0+
- **Events**: Dapr Pub/Sub (CloudEvents format)

### Microservices (Phase V)
- **WebSocket Service**: Real-time task synchronization across browser tabs
- **Recurring Task Service**: Automatic next-instance creation on task completion
- **Notification Service**: Proactive reminders with configurable preferences

### Infrastructure
- **Database**: Neon PostgreSQL (serverless)
- **Messaging**: Redpanda Cloud (Kafka-compatible, SASL_SSL)
- **State Store**: Redis (in-cluster or managed)
- **Runtime**: Dapr 1.12+ (pub/sub, state, secrets)
- **Containers**: Docker (multi-stage builds)
- **Orchestration**: Kubernetes (Docker Desktop, DOKS, GKE, OKE)
- **Configuration**: Helm Charts with per-environment values
- **CI/CD**: GitHub Actions (build, test, deploy)
- **AI DevOps**: kubectl-ai, kagent (10 AI agents for K8s operations)

## Project Structure

```
.
├── backend/                        # FastAPI backend (Phase II+)
│   ├── app/
│   │   ├── agent/                 # AI agent for chatbot (Phase III)
│   │   ├── api/v1/               # API endpoints (tasks, notifications, health)
│   │   ├── config/               # Configuration
│   │   ├── middleware/            # Correlation ID middleware (Phase V)
│   │   ├── models/               # SQLModel models (task, recurrence, events)
│   │   └── services/             # Event publisher, idempotency, notifications
│   ├── alembic/                   # Database migrations
│   ├── tests/                     # Backend tests
│   └── Dockerfile
│
├── frontend/                       # Next.js frontend (Phase II+)
│   ├── src/
│   │   ├── app/                   # App router pages
│   │   ├── components/            # React components (recurrence UI, notifications)
│   │   ├── hooks/                 # useRealTimeSync hook (Phase V)
│   │   └── lib/                   # WebSocket client manager
│   └── Dockerfile
│
├── services/                       # Phase V microservices
│   ├── websocket/                 # Real-time sync via WebSocket + Dapr
│   │   ├── app/                   # connections, auth, handlers, filters
│   │   └── Dockerfile
│   ├── recurring-task/            # Recurring task automation via Dapr events
│   │   ├── app/                   # handlers, recurrence calculator
│   │   └── Dockerfile
│   └── notification/              # Proactive notifications via Dapr events
│       ├── app/                   # handlers, scheduler
│       └── Dockerfile
│
├── helm/                           # Kubernetes Helm charts
│   ├── todo-chatbot/
│   │   └── templates/             # Deployments, services, ingress, Dapr components
│   ├── values-doks.yaml           # DigitalOcean Kubernetes
│   ├── values-gke.yaml            # Google Kubernetes Engine
│   └── values-oke.yaml            # Oracle Cloud OKE (Always Free)
│
├── dapr/                           # Local Dapr configuration
│   ├── config.yaml                # Tracing, metrics, access control
│   └── components/                # pubsub.yaml (Redpanda), statestore.yaml (Redis)
│
├── .github/workflows/              # CI/CD pipelines
│   ├── ci.yaml                    # Lint, test, build validation
│   ├── deploy-doks.yaml           # Deploy to DigitalOcean
│   ├── deploy-gke.yaml            # Deploy to Google Cloud
│   └── deploy-oke.yaml            # Deploy to Oracle Cloud
│
├── docker-compose.yaml             # All services with Dapr sidecars
├── docker-compose.infra.yaml       # Redpanda, Redis, Zipkin
│
├── src/                            # Phase I CLI application
├── specs/                          # Feature specifications (5 phases)
├── docs/                           # Guides and operational runbook
├── history/prompts/                # Prompt History Records (PHRs)
└── .specify/                       # SDD templates and tooling
```

## Quick Start

### Phase I: CLI Application

```bash
uv sync
uv run python main.py
```

**Commands**: `add`, `view`, `update`, `delete`, `toggle`, `exit`

### Phase II-III: Full-Stack Web Application

**Prerequisites**: Node.js 20+, Python 3.13+, Neon PostgreSQL account

```bash
# Backend
cd backend
cp .env.example .env          # Configure environment variables
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
pnpm install
cp .env.local.example .env.local
pnpm dev
```

**Access**: http://localhost:3000

### Phase IV: Local Kubernetes Deployment

**Prerequisites**: Docker Desktop, Minikube, Helm 3+

```bash
minikube start --memory=4096 --cpus=2
eval $(minikube docker-env)

docker build -t todo-frontend:local ./frontend
docker build -t todo-backend:local ./backend

cp helm/todo-chatbot/values-local.yaml.example helm/todo-chatbot/values-local.yaml
helm install todo ./helm/todo-chatbot -f helm/todo-chatbot/values-local.yaml
minikube service frontend-service --url
```

### Phase V: Cloud-Native Event-Driven Deployment

**Prerequisites**: Docker Desktop, Helm 3+, Redpanda Cloud account, Neon PostgreSQL

#### Local Development (Docker Compose + Dapr)

```bash
# Start infrastructure (Redpanda, Redis, Zipkin)
docker compose -f docker-compose.infra.yaml up -d

# Start all services with Dapr sidecars
docker compose up -d

# Access
# Frontend:         http://localhost:3000
# Backend API:      http://localhost:8000
# WebSocket:        ws://localhost:8001
# Redpanda Console: http://localhost:8080
# Zipkin Tracing:   http://localhost:9411
```

#### Cloud Deployment (Kubernetes)

Supports three cloud targets via GitHub Actions:

| Target | Workflow | Registry | Values File |
|--------|----------|----------|-------------|
| DigitalOcean DOKS | `deploy-doks.yaml` | DOCR | `values-doks.yaml` |
| Google Cloud GKE | `deploy-gke.yaml` | GAR | `values-gke.yaml` |
| Oracle Cloud OKE | `deploy-oke.yaml` | OCIR | `values-oke.yaml` |

Push to `main` triggers the configured workflow. Required GitHub Secrets:

```
DATABASE_URL, BETTER_AUTH_SECRET, OPENAI_API_KEY
REDPANDA_BROKERS, REDPANDA_USERNAME, REDPANDA_PASSWORD
```

Plus cloud-specific secrets (DOKS token, GKE credentials, or OCI keys).

#### AI-Powered Kubernetes Operations

```bash
# kubectl-ai: Natural language Kubernetes queries
export OPENAI_API_KEY="your-key"
kubectl-ai "show me all pods in the kagent namespace"

# kagent: 10 specialized AI agents deployed in-cluster
kubectl -n kagent port-forward service/kagent-ui 8080:8080
# Open http://localhost:8080
# Agents: k8s-agent, helm-agent, istio-agent, cilium-*, argo-rollouts,
#          kgateway, observability, promql
```

## Features by Phase

### Phase I - In-Memory CLI
- Add, view, update, delete tasks
- Toggle task completion
- Case-insensitive commands
- In-memory storage (no persistence)

### Phase II - Full-Stack Web
- User registration and authentication (Better Auth + JWT)
- Persistent task storage (PostgreSQL)
- Task CRUD operations via REST API
- Protected routes with session management
- Responsive web UI

### Phase III - AI Chatbot
- Natural language task management
- ChatKit integration with OpenAI
- MCP server with 5 tools: `add_task`, `list_tasks`, `update_task`, `complete_task`, `delete_task`
- Conversation persistence
- Due date parsing from natural language
- Rate limiting (20 req/min)

### Phase IV - Kubernetes
- Docker containerization (multi-stage builds)
- Helm chart for declarative deployment
- ConfigMaps and Secrets management
- Health checks and probes

### Phase V - Cloud-Native Event-Driven Architecture
- **Event-Driven Tasks**: Task CRUD publishes CloudEvents to Redpanda via Dapr pub/sub with at-least-once delivery
- **Real-Time Sync**: WebSocket service broadcasts task updates to all connected browser tabs within 2 seconds
- **Recurring Tasks**: Automatic next-instance creation when recurring tasks are completed (daily, weekly, monthly, custom)
- **Proactive Notifications**: Reminder events fire 30 minutes before due dates with configurable preferences and quiet hours
- **Multi-Cloud CI/CD**: GitHub Actions pipelines deploy to DOKS, GKE, or OKE with zero-downtime rolling updates
- **Dapr Runtime**: Service-to-service pub/sub, Redis state store, Kubernetes secret store, correlation ID tracing
- **Observability**: Structured JSON logs, Zipkin distributed tracing, health/readiness probes on all services
- **AI DevOps**: kubectl-ai (natural language K8s queries) and kagent (10 AI agents for cluster operations)

## Environment Variables

### Backend
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (async format) |
| `BETTER_AUTH_SECRET` | JWT signing secret |
| `BETTER_AUTH_URL` | Auth service base URL |
| `OPENAI_API_KEY` | OpenAI API key |
| `MCP_API_KEY` | MCP server authentication |
| `CORS_ORIGINS` | Allowed CORS origins |

### Frontend
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (sync format) |
| `BETTER_AUTH_SECRET` | JWT signing secret |
| `NEXT_PUBLIC_BACKEND_URL` | Backend API URL |
| `OPENAI_API_KEY` | OpenAI API key |
| `NEXT_PUBLIC_OPENAI_DOMAIN_KEY` | ChatKit domain key |

### Phase V (Kubernetes Secrets)
| Variable | Description |
|----------|-------------|
| `REDPANDA_BROKERS` | Redpanda bootstrap server URL |
| `REDPANDA_USERNAME` | Redpanda SASL username |
| `REDPANDA_PASSWORD` | Redpanda SASL password |

## API Endpoints

### Authentication (Better Auth)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Register new user |
| POST | `/api/auth/signin` | Authenticate user |
| POST | `/api/auth/signout` | End session |
| GET | `/api/auth/session` | Get current session |

### Tasks (Backend API)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List user's tasks |
| POST | `/api/tasks` | Create task |
| GET | `/api/tasks/{id}` | Get task by ID |
| PUT | `/api/tasks/{id}` | Update task |
| PATCH | `/api/tasks/{id}/toggle` | Toggle completion |
| DELETE | `/api/tasks/{id}` | Delete task |

### Chat (Phase III)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send chat message |
| GET | `/api/chatkit/session` | Get ChatKit session |

### Phase V Extensions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tasks/{id}/recurrence` | Set recurrence pattern |
| GET | `/api/tasks/{id}/recurrence` | Get recurrence settings |
| DELETE | `/api/tasks/{id}/recurrence` | Remove recurrence |
| GET | `/api/tasks/{id}/instances` | List recurring task instances |
| GET | `/api/notifications/preferences` | Get notification preferences |
| PUT | `/api/notifications/preferences` | Update notification preferences |
| GET | `/health` | Liveness check |
| GET | `/health/ready` | Readiness check |

## Documentation

- [Kubernetes Local Deployment Guide](docs/kubernetes-local-deployment.md)
- [Kubernetes Troubleshooting](docs/kubernetes-troubleshooting.md)
- [AI DevOps Tools Guide](docs/ai-devops-tools.md)
- [Operational Runbook](docs/operations/runbook.md)
- [Oracle Cloud OKE Setup](docs/operations/oke-setup.md)
- [Phase V Quickstart](specs/005-cloud-native-doks/quickstart.md)

## Specifications

Each phase has detailed specifications in the `specs/` directory:

| Phase | Spec Directory | Key Artifacts |
|-------|---------------|---------------|
| I | `specs/001-in-memory-todo-cli/` | spec, plan, tasks |
| II | `specs/002-fullstack-todo-web/` | spec, plan, tasks |
| III | `specs/003-ai-todo-chatbot/` | spec, plan, tasks |
| IV | `specs/004-local-kubernetes-deployment/` | spec, plan, tasks |
| V | `specs/005-cloud-native-doks/` | spec, plan, tasks, research, data-model, contracts |

## Development

This project follows **Spec-Driven Development (SDD)**:
1. Specify requirements in `spec.md`
2. Plan architecture in `plan.md`
3. Break down tasks in `tasks.md`
4. Implement with test coverage
5. Record decisions in PHRs and ADRs

## License

MIT
