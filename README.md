# Cloud Native Todo Chatbot

A multi-phase hackathon project demonstrating the evolution of a simple CLI application into a full-stack, AI-powered, Kubernetes-deployed cloud-native application.

## Project Overview

This project showcases progressive software development through four distinct phases:

| Phase | Name | Description | Status |
|-------|------|-------------|--------|
| I | In-Memory CLI | Python command-line todo app | Completed |
| II | Full-Stack Web | Next.js + FastAPI with PostgreSQL | Completed |
| III | AI Chatbot | Natural language task management with MCP | Completed |
| IV | Kubernetes | Local deployment with Minikube + Helm | In Progress |

## Tech Stack

### Frontend
- **Framework**: Next.js 15.1, React 19, TypeScript 5.7
- **Styling**: Tailwind CSS 3.4
- **AI/Chat**: ChatKit 1.4.1 (OpenAI-powered)
- **Authentication**: Better Auth

### Backend
- **Framework**: FastAPI 0.115+
- **Language**: Python 3.13+
- **ORM**: SQLModel with asyncpg
- **MCP Server**: FastMCP 2.0+

### Infrastructure
- **Database**: Neon PostgreSQL (serverless)
- **Containers**: Docker (multi-stage builds)
- **Orchestration**: Kubernetes via Minikube
- **Configuration**: Helm Charts

## Project Structure

```
.
├── backend/                    # FastAPI backend (Phase II+)
│   ├── app/
│   │   ├── agent/             # AI agent for chatbot (Phase III)
│   │   ├── api/routes/        # API endpoints
│   │   ├── config/            # Configuration
│   │   └── models/            # SQLModel data models
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Backend tests
│   └── Dockerfile             # Container definition
│
├── frontend/                   # Next.js frontend (Phase II+)
│   ├── src/
│   │   ├── app/               # App router pages
│   │   │   ├── (auth)/        # Sign in/up pages
│   │   │   ├── (protected)/   # Dashboard, chat
│   │   │   └── api/           # API routes
│   │   └── components/        # React components
│   └── Dockerfile             # Container definition
│
├── src/                        # Phase I CLI application
│   ├── cli/                   # CLI commands
│   ├── models/                # Data models
│   └── services/              # Business logic
│
├── specs/                      # Feature specifications
│   ├── 001-in-memory-todo-cli/
│   ├── 002-fullstack-todo-web/
│   ├── 003-ai-todo-chatbot/
│   └── 004-local-kubernetes-deployment/
│
├── helm/                       # Kubernetes Helm charts
│   └── todo-chatbot/
│
├── docs/                       # Documentation
│   ├── kubernetes-local-deployment.md
│   ├── kubernetes-troubleshooting.md
│   └── ai-devops-tools.md
│
├── scripts/                    # Build and deployment scripts
├── history/prompts/            # Prompt History Records (PHRs)
└── .specify/                   # SDD templates and tooling
```

## Quick Start

### Phase I: CLI Application

```bash
# Setup
uv sync

# Run
uv run python main.py
```

**Commands**: `add`, `view`, `update`, `delete`, `toggle`, `exit`

### Phase II-III: Full-Stack Web Application

**Prerequisites**:
- Node.js 20+
- Python 3.13+
- PostgreSQL (Neon account)

**Backend Setup**:
```bash
cd backend
cp .env.example .env          # Configure environment variables
uv sync
uv run alembic upgrade head   # Run migrations
uv run uvicorn app.main:app --reload --port 8000
```

**Frontend Setup**:
```bash
cd frontend
pnpm install
cp .env.local.example .env.local  # Configure environment variables
pnpm dev
```

**Access**: Open http://localhost:3000

### Phase IV: Kubernetes Deployment

**Prerequisites**:
- Docker Desktop
- Minikube
- Helm 3+

```bash
# Start Minikube
minikube start --memory=4096 --cpus=2

# Configure Docker for Minikube
eval $(minikube docker-env)

# Build images
docker build -t todo-frontend:local ./frontend
docker build -t todo-backend:local ./backend

# Deploy with Helm
cp helm/todo-chatbot/values-local.yaml.example helm/todo-chatbot/values-local.yaml
# Edit values-local.yaml with your secrets
helm install todo ./helm/todo-chatbot -f helm/todo-chatbot/values-local.yaml

# Access
minikube service frontend-service --url
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
- AI DevOps tools (kubectl-ai, kagent)

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

## Documentation

- [Kubernetes Local Deployment Guide](docs/kubernetes-local-deployment.md)
- [Kubernetes Troubleshooting](docs/kubernetes-troubleshooting.md)
- [AI DevOps Tools Guide](docs/ai-devops-tools.md)

## Specifications

Each phase has detailed specifications in the `specs/` directory:
- `spec.md` - Feature requirements and acceptance criteria
- `plan.md` - Implementation architecture
- `tasks.md` - Task breakdown with test cases

## Development

This project follows **Spec-Driven Development (SDD)**:
1. Specify requirements in `spec.md`
2. Plan architecture in `plan.md`
3. Break down tasks in `tasks.md`
4. Implement with test coverage
5. Record decisions in PHRs and ADRs

## License

MIT
