# Phase 0 Research: Local Kubernetes Deployment

**Feature**: Phase IV - Local Kubernetes Deployment
**Date**: 2026-01-22
**Status**: Complete

---

## 1. Minikube Best Practices

### Decision: Use Minikube with Docker driver on Windows

**Rationale**:
- Docker Desktop integration is seamless on Windows
- Driver auto-detects Docker and uses it by default
- Memory/CPU allocation configurable via CLI

**Alternatives considered**:
- Hyper-V driver: More complex setup, requires admin privileges
- VirtualBox driver: Slower, additional installation
- Kind (Kubernetes in Docker): Good alternative but Minikube has better addon ecosystem

**Configuration**:
```powershell
minikube start --driver=docker --memory=4096 --cpus=2
minikube addons enable metrics-server
minikube addons enable ingress  # Optional
```

---

## 2. Docker Multi-Stage Build Patterns

### Decision: Use 3-stage builds for both frontend and backend

**Rationale**:
- Stage separation: dependencies → build → runtime
- Minimal final image size
- Reproducible builds

### Frontend (Next.js with pnpm)

**Key findings**:
- Next.js 13+ supports `output: 'standalone'` for minimal production builds
- pnpm requires `--frozen-lockfile` for reproducibility
- Build args for `NEXT_PUBLIC_*` vars must be at build time

**Pattern**:
```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
RUN corepack enable pnpm
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Stage 2: Build
FROM node:20-alpine AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

# Stage 3: Runtime
FROM node:20-alpine AS runner
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
CMD ["node", "server.js"]
```

### Backend (FastAPI with uv)

**Key findings**:
- `uv` is the recommended fast Python package manager (successor to pip-tools)
- Virtual environments should be created inside the image
- Alembic migrations should run at container startup

**Pattern**:
```dockerfile
# Stage 1: Build
FROM python:3.13-slim AS builder
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.13-slim AS runner
COPY --from=builder /app/.venv ./.venv
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
CMD ["sh", "-c", ".venv/bin/alembic upgrade head && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

---

## 3. Kubernetes Secret Management (Local)

### Decision: Use Helm values file for local secrets

**Rationale**:
- Simple for local development
- No external dependencies (Vault, External Secrets Operator)
- values-local.yaml is gitignored

**Alternatives considered**:
- kubectl create secret: Manual, not version-controlled
- External Secrets Operator: Overkill for local dev
- SOPS encrypted files: Added complexity

**Pattern**:
```yaml
# values-local.yaml (gitignored)
secrets:
  databaseUrl: "postgresql+asyncpg://user:pass@host/db"
  betterAuthSecret: "jwt-secret-here"
  openaiApiKey: "sk-..."
  mcpApiKey: "mcp-key-here"
```

---

## 4. Helm Chart Structure

### Decision: Single chart with frontend/backend subcharts-style values

**Rationale**:
- Simpler than multiple charts
- Values grouped by component
- Easy to upgrade individual components

**Key template patterns**:
- Use `_helpers.tpl` for common labels and selectors
- Environment variables from both ConfigMap and Secret refs
- Resource requests/limits for predictable scheduling

---

## 5. Health Check Implementation

### Decision: HTTP probes on `/api/health` endpoints

**Rationale**:
- Both applications already expose health endpoints
- HTTP probes are simple and well-supported
- Startup probes prevent premature readiness checks

**Configuration**:
```yaml
livenessProbe:
  httpGet:
    path: /api/health
    port: 3000  # or 8000 for backend
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /api/health
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 10

startupProbe:
  httpGet:
    path: /api/health
    port: 3000
  failureThreshold: 30
  periodSeconds: 10
```

---

## 6. Networking in Minikube

### Decision: NodePort for frontend, ClusterIP for backend

**Rationale**:
- NodePort provides direct access without LoadBalancer
- Backend only needs cluster-internal access
- Port 30080 chosen (within NodePort range 30000-32767)

**Alternatives considered**:
- LoadBalancer with `minikube tunnel`: Adds complexity
- Ingress: Good for multi-host but overhead for single app
- Port-forward only: Less production-like

---

## 7. AI DevOps Tools

### kubectl-ai

**Installation**:
```bash
go install github.com/sozercan/kubectl-ai@latest
# Requires OPENAI_API_KEY environment variable
```

**Best use cases**:
- Natural language cluster queries
- Generating kubectl commands
- Debugging pod issues

### kagent

**Status**: Evaluate availability and installation for Windows

**Fallback**: kubectl-ai covers most use cases

### Docker AI Agent (Gordon)

**Status**: Built into Docker Desktop (if enabled)
**Use case**: Dockerfile optimization and debugging

---

## 8. Windows-Specific Considerations

### Docker Environment for Minikube

**PowerShell equivalent** of `eval $(minikube docker-env)`:
```powershell
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
```

### Path Handling

- Use forward slashes in Dockerfiles
- Mount paths may need adjustment for WSL2 backend

### Script Compatibility

- Provide both `.sh` (Git Bash) and `.ps1` (PowerShell) scripts

---

## Resolved Clarifications

| Item | Resolution |
|------|------------|
| Image pull policy | `Never` - images built locally in Minikube |
| Database access | Backend connects to Neon via public endpoint |
| Frontend build args | Injected at Docker build time via `--build-arg` |
| Secret rotation | Manual - rebuild/redeploy for changes |
| Ingress | Optional - NodePort sufficient for local dev |
