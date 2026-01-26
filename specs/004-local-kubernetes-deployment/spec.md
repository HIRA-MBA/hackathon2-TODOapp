# Phase IV Specification: Local Kubernetes Deployment

**Project:** Cloud Native Todo Chatbot
**Phase:** IV - Local Kubernetes Deployment
**Status:** Draft
**Created:** 2026-01-22

---

## 1. Overview

### 1.1 Purpose

Deploy a LOCAL Kubernetes version of the Cloud Native Todo Chatbot using Minikube and Helm Charts for learning and development purposes. This phase enables developers to run the full application stack in a containerized, orchestrated environment without impacting existing production deployments on Vercel (frontend) and Render (backend).

### 1.2 Current System State

| Component | Current Deployment | Technology |
|-----------|-------------------|------------|
| Frontend | Vercel | Next.js 15.1.0, React 19, TypeScript 5.7 |
| Backend | Render | FastAPI 0.115+, Python 3.13+, Uvicorn |
| Database | Neon (Managed) | PostgreSQL with asyncpg |
| AI Integration | OpenAI | ChatKit 1.4.1, FastMCP 2.0+, Agents SDK |

### 1.3 Goals

1. **Containerization**: Package frontend and backend as production-ready Docker images
2. **Local Orchestration**: Deploy and manage containers via Minikube
3. **Configuration Management**: Use Helm Charts for declarative, repeatable deployments
4. **AI-Assisted DevOps**: Leverage kubectl-ai and kagent for intelligent cluster operations
5. **Learning Platform**: Provide a safe environment for Kubernetes experimentation

### 1.4 Non-Goals

- Running PostgreSQL inside Kubernetes (continues using external Neon)
- Replacing or affecting Vercel/Render production deployments
- Implementing CI/CD pipelines
- Handling production traffic
- Multi-node cluster setup

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DEVELOPER WORKSTATION                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      MINIKUBE CLUSTER                         │  │
│  │  ┌─────────────────┐         ┌─────────────────────────────┐  │  │
│  │  │   FRONTEND POD  │         │      BACKEND POD            │  │  │
│  │  │  ┌───────────┐  │         │  ┌───────────────────────┐  │  │  │
│  │  │  │ Next.js   │  │  ──────►│  │ FastAPI + Uvicorn     │  │  │  │
│  │  │  │ App       │  │         │  │ + FastMCP Server      │  │  │  │
│  │  │  └───────────┘  │         │  └───────────────────────┘  │  │  │
│  │  └────────┬────────┘         └─────────────┬───────────────┘  │  │
│  │           │                                │                   │  │
│  │  ┌────────▼────────┐         ┌─────────────▼───────────────┐  │  │
│  │  │ Service         │         │ Service                     │  │  │
│  │  │ (NodePort)      │         │ (ClusterIP)                 │  │  │
│  │  │ :30080          │         │ :8000                       │  │  │
│  │  └─────────────────┘         └─────────────────────────────┘  │  │
│  │                                                                │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │              OPTIONAL: INGRESS CONTROLLER               │  │  │
│  │  │         todo.local → frontend / api.todo.local → backend│  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  │                                                                │  │
│  │  ┌─────────────────┐         ┌─────────────────────────────┐  │  │
│  │  │   ConfigMap     │         │      Secrets                │  │  │
│  │  │ - APP_NAME      │         │ - DATABASE_URL              │  │  │
│  │  │ - ENVIRONMENT   │         │ - OPENAI_API_KEY            │  │  │
│  │  │ - CORS_ORIGINS  │         │ - BETTER_AUTH_SECRET        │  │  │
│  │  └─────────────────┘         │ - MCP_API_KEY               │  │  │
│  │                              └─────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────┐    ┌─────────────────────────────────────┐  │
│  │   Docker Desktop   │    │        AI DevOps Tools              │  │
│  │   + Gordon (AI)    │    │  kubectl-ai / kagent                │  │
│  └────────────────────┘    └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ TCP/SSL
                                      ▼
                     ┌────────────────────────────────┐
                     │   NEON PostgreSQL (External)   │
                     │   - Tasks, Conversations       │
                     │   - ChatKit Sessions           │
                     │   - User Authentication        │
                     └────────────────────────────────┘
```

### 2.2 Network Flow

1. **User Access**: Browser → `localhost:30080` (NodePort) or `todo.local` (Ingress)
2. **Frontend → Backend**: Next.js API routes → `backend-service:8000` (ClusterIP)
3. **Backend → Database**: FastAPI → Neon PostgreSQL (external, SSL required)
4. **ChatKit Flow**: OpenAI ChatKit → Backend MCP Server → Task Operations → Database

### 2.3 Container Registry

- **Local Only**: Images built and stored in Minikube's Docker daemon
- **Command**: `eval $(minikube docker-env)` to use Minikube's Docker
- **Image Pull Policy**: `Never` (local images) or `IfNotPresent`

---

## 3. Components

### 3.1 Frontend Container

**Base Image**: `node:20-alpine`

**Multi-Stage Build**:
1. **Stage 1 (deps)**: Install dependencies with pnpm
2. **Stage 2 (builder)**: Build Next.js production bundle
3. **Stage 3 (runner)**: Minimal runtime with standalone output

**Dockerfile Location**: `frontend/Dockerfile`

**Build Arguments**:
| Arg | Description | Default |
|-----|-------------|---------|
| `NEXT_PUBLIC_APP_NAME` | Application display name | `Todo App` |
| `NEXT_PUBLIC_BACKEND_URL` | Backend API URL for ChatKit MCP | (required) |
| `NEXT_PUBLIC_BETTER_AUTH_URL` | Auth service URL | (required) |
| `NEXT_PUBLIC_OPENAI_DOMAIN_KEY` | ChatKit domain key | (required) |

**Runtime Environment**:
| Variable | Source | Description |
|----------|--------|-------------|
| `DATABASE_URL` | Secret | PostgreSQL connection (sync format) |
| `BETTER_AUTH_SECRET` | Secret | JWT signing secret |
| `BACKEND_URL` | ConfigMap | Internal backend service URL |
| `OPENAI_API_KEY` | Secret | OpenAI API authentication |
| `OPENAI_CHATKIT_WORKFLOW_ID` | ConfigMap | ChatKit workflow identifier |

**Exposed Port**: 3000

**Health Check**: `curl -f http://localhost:3000/api/health || exit 1`

**Health Response Format**:
```json
{
  "status": "ok",
  "service": "frontend",
  "timestamp": "<ISO-8601>"
}
```

### 3.2 Backend Container

**Base Image**: `python:3.13-slim`

**Multi-Stage Build**:
1. **Stage 1 (builder)**: Install uv, sync dependencies
2. **Stage 2 (runner)**: Copy virtual environment, app code

**Dockerfile Location**: `backend/Dockerfile`

**Runtime Environment**:
| Variable | Source | Description |
|----------|--------|-------------|
| `DATABASE_URL` | Secret | PostgreSQL connection (async format) |
| `BETTER_AUTH_SECRET` | Secret | JWT validation secret |
| `BETTER_AUTH_URL` | ConfigMap | Auth service base URL |
| `CORS_ORIGINS` | ConfigMap | Allowed CORS origins |
| `ENVIRONMENT` | ConfigMap | `development` or `production` |
| `OPENAI_API_KEY` | Secret | OpenAI API key |
| `MCP_API_KEY` | Secret | MCP server authentication |
| `MCP_DEFAULT_USER_ID` | ConfigMap | Default user for testing |

**Exposed Port**: 8000

**Startup Command**:
```bash
uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Health Check**: `curl -f http://localhost:8000/api/health || exit 1`

**Health Response Format**:
```json
{
  "status": "ok",
  "service": "backend",
  "timestamp": "<ISO-8601>"
}
```

### 3.3 Kubernetes Resources

#### 3.3.1 Deployments

**frontend-deployment**:
- Replicas: 1 (configurable)
- Container: `todo-frontend:local`
- Resources: 256Mi memory, 250m CPU (limits: 512Mi, 500m)
- Probes: liveness, readiness on `/api/health`

**backend-deployment**:
- Replicas: 1 (configurable)
- Container: `todo-backend:local`
- Resources: 256Mi memory, 250m CPU (limits: 512Mi, 500m)
- Probes: liveness, readiness on `/api/health`
  - initialDelaySeconds: 30, periodSeconds: 10, timeoutSeconds: 5, failureThreshold: 3
- Init Container: Database migration runner (optional)
- Expected cold-start time: 60 seconds (includes migrations and warm-up)

#### 3.3.2 Services

**frontend-service**:
- Type: `NodePort`
- Port: 80 → 3000
- NodePort: 30080
- Selector: `app: todo-frontend`

**backend-service**:
- Type: `ClusterIP`
- Port: 8000 → 8000
- Selector: `app: todo-backend`

#### 3.3.3 Ingress (Optional)

**todo-ingress**:
- Class: `nginx` (Minikube addon)
- Rules:
  - `todo.local` → frontend-service:80
  - `todo.local/api` → backend-service:8000
- TLS: Optional (self-signed for local)

#### 3.3.4 ConfigMaps

**app-config**:
```yaml
data:
  ENVIRONMENT: "development"
  NEXT_PUBLIC_APP_NAME: "Todo App (K8s)"
  CORS_ORIGINS: "http://localhost:30080,http://todo.local"
  BETTER_AUTH_URL: "http://frontend-service:80"
  BACKEND_URL: "http://backend-service:8000"
  OPENAI_CHATKIT_WORKFLOW_ID: "<workflow-id>"
  MCP_DEFAULT_USER_ID: "<test-user-id>"
```

#### 3.3.5 Secrets

**app-secrets** (base64 encoded):
```yaml
data:
  DATABASE_URL: <base64-encoded>
  BETTER_AUTH_SECRET: <base64-encoded>
  OPENAI_API_KEY: <base64-encoded>
  MCP_API_KEY: <base64-encoded>
  NEXT_PUBLIC_OPENAI_DOMAIN_KEY: <base64-encoded>
```

---

## 4. Configuration & Secrets

### 4.1 Helm Chart Structure

```
helm/todo-chatbot/
├── Chart.yaml
├── values.yaml
├── values-local.yaml          # Local overrides
├── templates/
│   ├── _helpers.tpl
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── ingress.yaml
│   └── NOTES.txt
└── .helmignore
```

### 4.2 Values Configuration

**values.yaml** (defaults):
```yaml
global:
  environment: development
  imageTag: local
  imagePullPolicy: Never

frontend:
  replicaCount: 1
  image:
    repository: todo-frontend
    tag: local
  service:
    type: NodePort
    port: 80
    nodePort: 30080
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  env:
    NEXT_PUBLIC_APP_NAME: "Todo App"

backend:
  replicaCount: 1
  image:
    repository: todo-backend
    tag: local
  service:
    type: ClusterIP
    port: 8000
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  runMigrations: true

ingress:
  enabled: false
  className: nginx
  hosts:
    - host: todo.local
      paths:
        - path: /
          pathType: Prefix
          service: frontend
        - path: /api
          pathType: Prefix
          service: backend

secrets:
  # Values provided via --set or values-local.yaml
  databaseUrl: ""
  betterAuthSecret: ""
  openaiApiKey: ""
  mcpApiKey: ""
  openaiDomainKey: ""
```

### 4.3 Secret Management

**Local Development**:
1. Create `values-local.yaml` (gitignored)
2. Populate with actual secret values
3. Deploy with: `helm install todo ./helm/todo-chatbot -f values-local.yaml`

**Alternative - External Secrets**:
```bash
kubectl create secret generic app-secrets \
  --from-literal=DATABASE_URL='postgresql+asyncpg://...' \
  --from-literal=BETTER_AUTH_SECRET='...' \
  --from-literal=OPENAI_API_KEY='sk-...' \
  --from-literal=MCP_API_KEY='...'
```

### 4.4 Environment Variable Mapping

| Application Variable | Kubernetes Source | Template Reference |
|---------------------|-------------------|-------------------|
| `DATABASE_URL` | Secret: `app-secrets` | `{{ .Values.secrets.databaseUrl }}` |
| `BETTER_AUTH_SECRET` | Secret: `app-secrets` | `{{ .Values.secrets.betterAuthSecret }}` |
| `OPENAI_API_KEY` | Secret: `app-secrets` | `{{ .Values.secrets.openaiApiKey }}` |
| `MCP_API_KEY` | Secret: `app-secrets` | `{{ .Values.secrets.mcpApiKey }}` |
| `ENVIRONMENT` | ConfigMap: `app-config` | `{{ .Values.global.environment }}` |
| `CORS_ORIGINS` | ConfigMap: `app-config` | Computed from services |
| `BACKEND_URL` | ConfigMap: `app-config` | `http://backend-service:8000` |

---

## 5. Constraints

### 5.1 Technical Constraints

| Constraint | Description | Rationale |
|------------|-------------|-----------|
| Minikube Only | Kubernetes runs locally via Minikube | Learning environment, no cloud costs |
| External Database | PostgreSQL hosted on Neon | Avoid stateful workload complexity |
| Single Node | No multi-node cluster support | Simplified local setup |
| Local Images | No external registry push | Development workflow only |
| Manual Secrets | No external secrets operator | Minimal tooling for learning |

### 5.2 Resource Constraints

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| Minikube Memory | 4GB | 6GB |
| Minikube CPUs | 2 | 4 |
| Docker Disk | 20GB | 40GB |
| Host RAM | 8GB | 16GB |

### 5.3 Network Constraints

- Backend must have outbound access to Neon PostgreSQL (port 5432/6432)
- Backend must have outbound access to OpenAI API (HTTPS)
- Frontend must reach backend via Kubernetes service DNS
- NodePort range: 30000-32767 (Minikube default)

### 5.4 Security Constraints (Minimal Posture)

Security posture is minimal for this learning environment. No NetworkPolicies or RBAC are implemented.

- Secrets must never be committed to Git
- `.env.local` and `values-local.yaml` must be gitignored
- No hardcoded credentials in Dockerfiles or templates
- SSL/TLS required for external database connections
- Kubernetes Secrets used for sensitive configuration (base64 encoded)
- No NetworkPolicies or PodSecurityPolicies required

---

## 6. Acceptance Criteria

### 6.1 Infrastructure Setup

- [ ] **AC-001**: Minikube cluster starts successfully with `minikube start --memory=4096 --cpus=2`
- [ ] **AC-002**: Minikube ingress addon enabled (if using Ingress)
- [ ] **AC-003**: Docker environment configured for Minikube (`eval $(minikube docker-env)`)

### 6.2 Container Build

- [ ] **AC-004**: Frontend Dockerfile builds without errors
- [ ] **AC-005**: Backend Dockerfile builds without errors
- [ ] **AC-006**: Frontend image size < 500MB (multi-stage optimization)
- [ ] **AC-007**: Backend image size < 500MB (multi-stage optimization)
- [ ] **AC-008**: Images tagged as `todo-frontend:local` and `todo-backend:local`

### 6.3 Kubernetes Deployment

- [ ] **AC-009**: `helm install todo ./helm/todo-chatbot -f values-local.yaml` succeeds
- [ ] **AC-010**: Frontend pod reaches `Running` state within 60 seconds
- [ ] **AC-011**: Backend pod reaches `Running` state within 60 seconds
- [ ] **AC-012**: No pod restarts due to failed health checks after 2 minutes
- [ ] **AC-013**: `kubectl get pods` shows all pods as `1/1 Ready`

### 6.4 Application Functionality

- [ ] **AC-014**: Frontend accessible at `http://localhost:30080` (or `http://todo.local`)
- [ ] **AC-015**: Backend health check returns 200 at `/api/health`
- [ ] **AC-016**: Backend connects to external PostgreSQL (logs show successful connection)
- [ ] **AC-017**: User can sign up / sign in via the frontend
- [ ] **AC-018**: User can create, list, and complete tasks
- [ ] **AC-019**: ChatKit widget loads and connects to MCP server
- [ ] **AC-020**: AI agent responds to natural language task commands

### 6.5 Configuration Management

- [ ] **AC-021**: Secrets are not visible in `helm get values` output
- [ ] **AC-022**: ConfigMap values correctly injected into pods
- [ ] **AC-023**: `helm upgrade` applies configuration changes without downtime
- [ ] **AC-024**: Environment variables match between local dev and K8s deployment

### 6.6 AI DevOps Tools

- [ ] **AC-025**: `kubectl-ai` successfully executes basic queries (e.g., "show all pods")
- [ ] **AC-026**: `kubectl-ai` can scale deployments (e.g., "scale backend to 2 replicas")
- [ ] **AC-027**: `kagent` provides cluster health insights
- [ ] **AC-028**: AI tools can diagnose pod issues (e.g., "why is pod failing?")

### 6.7 Observability (Minimal Scope)

Observability is limited to kubectl logs and Minikube metrics-server. No Prometheus, Grafana, or distributed tracing tooling is included.

- [ ] **AC-029**: `kubectl logs` shows structured JSON logs from backend
- [ ] **AC-030**: Request IDs traceable across frontend → backend
- [ ] **AC-031**: Health check endpoints return appropriate status codes
- [ ] **AC-032**: `kubectl top pods` displays resource usage via metrics-server

---

## 7. Deliverables

### 7.1 Docker Artifacts

| Deliverable | Path | Description |
|-------------|------|-------------|
| Frontend Dockerfile | `frontend/Dockerfile` | Multi-stage Next.js build |
| Backend Dockerfile | `backend/Dockerfile` | Multi-stage Python/uv build |
| Docker Ignore (Frontend) | `frontend/.dockerignore` | Build exclusions |
| Docker Ignore (Backend) | `backend/.dockerignore` | Build exclusions |

### 7.2 Helm Chart

| Deliverable | Path | Description |
|-------------|------|-------------|
| Chart Definition | `helm/todo-chatbot/Chart.yaml` | Chart metadata |
| Default Values | `helm/todo-chatbot/values.yaml` | Configuration defaults |
| Local Values Template | `helm/todo-chatbot/values-local.yaml.example` | Secret template |
| Deployment Templates | `helm/todo-chatbot/templates/*.yaml` | K8s resource definitions |

### 7.3 Documentation

| Deliverable | Path | Description |
|-------------|------|-------------|
| Deployment Guide | `docs/kubernetes-local-deployment.md` | Step-by-step setup |
| AI Tools Guide | `docs/ai-devops-tools.md` | kubectl-ai/kagent usage |
| Troubleshooting Guide | `docs/kubernetes-troubleshooting.md` | Common issues & solutions |

### 7.4 Scripts

| Deliverable | Path | Description |
|-------------|------|-------------|
| Build Script | `scripts/k8s-build.sh` | Build all images |
| Deploy Script | `scripts/k8s-deploy.sh` | Deploy to Minikube |
| Teardown Script | `scripts/k8s-teardown.sh` | Clean up resources |

---

## 8. AI DevOps Integration

### 8.1 kubectl-ai Usage Examples

```bash
# Query cluster state
kubectl-ai "show me all running pods in default namespace"
kubectl-ai "what services are exposing port 8000?"

# Deployment operations
kubectl-ai "scale the backend deployment to 2 replicas"
kubectl-ai "restart all pods in the frontend deployment"

# Debugging
kubectl-ai "why is the backend pod in CrashLoopBackOff?"
kubectl-ai "show me the last 50 log lines from the backend"
kubectl-ai "check if backend can reach the database"

# Resource management
kubectl-ai "show resource usage for all pods"
kubectl-ai "which pod is using the most memory?"
```

### 8.2 kagent Usage Examples

```bash
# Cluster health
kagent health check
kagent analyze cluster

# Optimization
kagent suggest optimizations
kagent check resource limits

# Diagnostics
kagent diagnose pod backend-xxx-xxx
kagent explain error "ImagePullBackOff"
```

### 8.3 Docker AI Agent (Gordon)

```bash
# If available in Docker Desktop
docker ai "create a Dockerfile for a Next.js app with pnpm"
docker ai "optimize this Dockerfile for smaller image size"
docker ai "debug why my container keeps restarting"
```

---

## 9. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Database connectivity from K8s | High | Medium | Graceful degradation with user-visible error messages; test connection early; document SSL config |
| Image size bloat | Medium | Medium | Use multi-stage builds; verify sizes in AC |
| Secret exposure | High | Low | Strict gitignore; use K8s secrets properly |
| Resource constraints on host | Medium | Medium | Document minimum requirements; provide tuning guide |
| ChatKit initialization failure | High | Medium | Validate environment variables; add startup probes |

---

## 10. Clarifications

### Session 2026-01-22

- Q: When external dependencies (Neon PostgreSQL or OpenAI) are unreachable from within Kubernetes, what should happen? → A: Graceful degradation with user-visible error messages (e.g., "Database unavailable")
- Q: What level of observability tooling should be included in this local Kubernetes deployment? → A: Minimal - kubectl logs + Minikube metrics-server only (no additional tooling)
- Q: How should developers iterate on code changes while using this local Kubernetes setup? → A: Quick rebuild - Rebuild images only, use `kubectl rollout restart` to redeploy
- Q: What is the acceptable cold-start time for pods before they're ready to serve traffic? → A: 60 seconds (allows for migrations and health check warm-up)
- Q: What security controls should be enforced in this local Kubernetes deployment? → A: Minimal - Protect secrets via K8s Secrets and gitignore; no network policies or RBAC

---

## 11. References

- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Helm Charts Guide](https://helm.sh/docs/chart_template_guide/)
- [kubectl-ai GitHub](https://github.com/sozercan/kubectl-ai)
- [Docker Desktop AI Agent](https://docs.docker.com/desktop/features/gordon/)
- [Next.js Docker Guide](https://nextjs.org/docs/deployment#docker-image)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)

---

## Appendix A: Quick Start Commands

```bash
# 1. Start Minikube
minikube start --memory=4096 --cpus=2

# 2. Enable addons
minikube addons enable ingress
minikube addons enable metrics-server

# 3. Configure Docker environment
eval $(minikube docker-env)

# 4. Build images
docker build -t todo-frontend:local ./frontend
docker build -t todo-backend:local ./backend

# 5. Create values-local.yaml with secrets
cp helm/todo-chatbot/values-local.yaml.example helm/todo-chatbot/values-local.yaml
# Edit values-local.yaml with actual secrets

# 6. Deploy
helm install todo ./helm/todo-chatbot -f helm/todo-chatbot/values-local.yaml

# 7. Access application
minikube service frontend-service --url
# Or add to /etc/hosts: $(minikube ip) todo.local

# 8. View logs
kubectl logs -f deployment/backend-deployment

# 9. Iterate on changes (quick rebuild workflow)
docker build -t todo-frontend:local ./frontend   # or backend
kubectl rollout restart deployment/frontend-deployment

# 10. Teardown
helm uninstall todo
minikube stop
```
