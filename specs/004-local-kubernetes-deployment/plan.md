# Implementation Plan: Phase IV - Local Kubernetes Deployment

**Branch**: `main` | **Date**: 2026-01-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-local-kubernetes-deployment/spec.md`

## Summary

Deploy the Cloud Native Todo Chatbot to local Kubernetes (Minikube) using Helm Charts. Containerize frontend (Next.js 15.1/pnpm) and backend (FastAPI/uv), configure secrets/configmaps for external Neon PostgreSQL and OpenAI, and enable AI-assisted operations via kubectl-ai and kagent.

## Technical Context

**Language/Version**: TypeScript 5.7 (frontend), Python 3.13+ (backend)
**Primary Dependencies**: Next.js 15.1, FastAPI 0.115+, pnpm, uv
**Storage**: External Neon PostgreSQL (asyncpg)
**Testing**: Manual verification via acceptance criteria
**Target Platform**: Minikube (Windows/Docker Desktop)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Local development only
**Constraints**: 4GB RAM minimum, no cloud deployment
**Scale/Scope**: Single developer workstation

## Constitution Check

*GATE: This is an infrastructure/DevOps task. No code logic changes. Constitution gates pass by default.*

- Test-First: N/A (infrastructure)
- Library-First: N/A (containerization)
- Simplicity: Helm chart follows standard patterns

## Project Structure

### Documentation (this feature)

```text
specs/004-local-kubernetes-deployment/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── quickstart.md        # Quick deployment guide
└── tasks.md             # Phase 2 output (by /sp.tasks)
```

### Source Code (repository root)

```text
frontend/
├── Dockerfile           # Multi-stage Next.js build
└── .dockerignore

backend/
├── Dockerfile           # Multi-stage Python/uv build
└── .dockerignore

helm/todo-chatbot/
├── Chart.yaml
├── values.yaml
├── values-local.yaml.example
└── templates/
    ├── _helpers.tpl
    ├── frontend-deployment.yaml
    ├── frontend-service.yaml
    ├── backend-deployment.yaml
    ├── backend-service.yaml
    ├── configmap.yaml
    ├── secrets.yaml
    └── NOTES.txt

scripts/
├── k8s-build.sh         # Build Docker images
├── k8s-deploy.sh        # Deploy to Minikube
└── k8s-teardown.sh      # Clean up resources
```

---

## Phase IV Execution Plan

### Step 1: Environment Setup

**Goal**: Install and configure local Kubernetes tooling

- Install Docker Desktop with Kubernetes support
- Install Minikube: `winget install Kubernetes.minikube`
- Install Helm: `winget install Helm.Helm`
- Install kubectl-ai: `go install github.com/sozercan/kubectl-ai@latest`
- Install kagent (if available): follow kagent GitHub instructions

**Verification**:
```powershell
docker --version
minikube version
helm version
kubectl-ai --help
```

---

### Step 2: Containerization - Frontend Dockerfile

**Goal**: Create multi-stage Dockerfile for Next.js frontend

**Key actions**:
- Stage 1 (deps): `node:20-alpine`, install pnpm, copy package.json/pnpm-lock.yaml, run `pnpm install --frozen-lockfile`
- Stage 2 (builder): Copy source, set build args, run `pnpm build`
- Stage 3 (runner): Minimal image with `standalone` output, copy `.next/standalone`, `.next/static`, `public`
- Expose port 3000, use `node server.js` as CMD

**Location**: `frontend/Dockerfile`, `frontend/.dockerignore`

---

### Step 3: Containerization - Backend Dockerfile

**Goal**: Create multi-stage Dockerfile for FastAPI backend

**Key actions**:
- Stage 1 (builder): `python:3.13-slim`, install uv, copy pyproject.toml/uv.lock, run `uv sync --frozen`
- Stage 2 (runner): Copy virtual env and app code
- Expose port 8000
- CMD: `uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`

**Location**: `backend/Dockerfile`, `backend/.dockerignore`

---

### Step 4: Kubernetes Secrets & ConfigMaps

**Goal**: Define Kubernetes resource templates for configuration

**Secrets** (base64 encoded in values-local.yaml):
- `DATABASE_URL` - Neon PostgreSQL connection string
- `BETTER_AUTH_SECRET` - JWT signing secret
- `OPENAI_API_KEY` - OpenAI API key
- `MCP_API_KEY` - MCP server authentication
- `NEXT_PUBLIC_OPENAI_DOMAIN_KEY` - ChatKit domain key

**ConfigMaps**:
- `ENVIRONMENT` = "development"
- `CORS_ORIGINS` = "http://localhost:30080"
- `BACKEND_URL` = "http://backend-service:8000"
- `BETTER_AUTH_URL` = "http://frontend-service:80"
- `MCP_DEFAULT_USER_ID` = test user ID

---

### Step 5: Helm Chart Creation

**Goal**: Create complete Helm chart for todo-chatbot

**Key actions**:
- Create `Chart.yaml` with metadata (name: todo-chatbot, version: 0.1.0)
- Create `values.yaml` with defaults (imagePullPolicy: Never, nodePort: 30080)
- Create `values-local.yaml.example` as secret template
- Create deployment templates with:
  - Resource limits (256Mi/250m requests, 512Mi/500m limits)
  - Liveness/readiness probes on `/api/health`
  - Environment variable injection from secrets/configmaps
- Create service templates (NodePort for frontend, ClusterIP for backend)
- Create `_helpers.tpl` for common labels/names
- Create `NOTES.txt` for post-install instructions

---

### Step 6: Minikube Deployment Workflow

**Goal**: Create deployment scripts and procedures

**Key actions**:
- Start Minikube: `minikube start --memory=4096 --cpus=2`
- Configure Docker env: `eval $(minikube docker-env)` (or PowerShell equivalent)
- Build images inside Minikube:
  ```bash
  docker build -t todo-frontend:local ./frontend
  docker build -t todo-backend:local ./backend
  ```
- Create values-local.yaml with actual secrets
- Deploy: `helm install todo ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml`
- Upgrade: `helm upgrade todo ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml`
- Uninstall: `helm uninstall todo`

---

### Step 7: AI-Assisted Operations

**Goal**: Document kubectl-ai and kagent usage patterns

**kubectl-ai examples**:
```bash
kubectl-ai "show all pods in default namespace"
kubectl-ai "why is backend pod not ready?"
kubectl-ai "scale frontend to 2 replicas"
kubectl-ai "show logs from backend pod"
```

**kagent examples** (if available):
```bash
kagent health check
kagent diagnose pod <pod-name>
```

---

### Step 8: Local Access & Verification

**Goal**: Verify application works in Kubernetes

**Access methods**:
- NodePort: `http://localhost:30080`
- Minikube service: `minikube service frontend-service --url`
- Port-forward: `kubectl port-forward svc/frontend-service 3000:80`

**Verification steps**:
1. Access frontend URL
2. Check backend health: `curl http://$(minikube ip):30081/api/health` (if exposed)
3. Review pod logs: `kubectl logs -f deployment/backend-deployment`
4. Test authentication flow
5. Test task CRUD operations
6. Test ChatKit widget

---

### Step 9: Validation Checklist

**Infrastructure**:
- [ ] Minikube cluster running
- [ ] Docker env configured for Minikube

**Containers**:
- [ ] Frontend image builds < 500MB
- [ ] Backend image builds < 500MB
- [ ] No build errors

**Kubernetes**:
- [ ] Helm install succeeds
- [ ] Frontend pod Running
- [ ] Backend pod Running
- [ ] No CrashLoopBackOff

**Application**:
- [ ] Frontend accessible at localhost:30080
- [ ] Backend health check returns 200
- [ ] Database connection successful
- [ ] Authentication works
- [ ] Task CRUD works
- [ ] ChatKit loads

**Configuration**:
- [ ] Secrets not in git
- [ ] ConfigMaps injected correctly

---

## Deliverables Summary

| Category | Files |
|----------|-------|
| Dockerfiles | `frontend/Dockerfile`, `backend/Dockerfile` |
| Docker Ignore | `frontend/.dockerignore`, `backend/.dockerignore` |
| Helm Chart | `helm/todo-chatbot/*` (Chart.yaml, values.yaml, templates/) |
| Scripts | `scripts/k8s-build.sh`, `scripts/k8s-deploy.sh`, `scripts/k8s-teardown.sh` |
| Docs | `docs/kubernetes-local-deployment.md`, `docs/ai-devops-tools.md` |

---

## Constraints Reminder

- **NO** PostgreSQL in Kubernetes (use external Neon)
- **NO** CI/CD pipelines
- **NO** cloud/production deployment
- **NO** MCP usage in Phase IV (already configured from Phase III)
- **LOCAL ONLY** - Minikube on developer workstation
