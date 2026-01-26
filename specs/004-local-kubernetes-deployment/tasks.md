# Tasks: Phase IV - Local Kubernetes Deployment

**Input**: Design documents from `/specs/004-local-kubernetes-deployment/`
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, quickstart.md

**Tests**: Manual verification via acceptance criteria (AC-001 through AC-031)

**Organization**: Tasks are grouped by functional areas mapped to acceptance criteria groups.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, etc.)
- Include exact file paths in descriptions

## Path Conventions

- **Web app structure**: `frontend/`, `backend/`, `helm/`, `scripts/`, `docs/`
- Frontend: Next.js 15.1 with pnpm
- Backend: FastAPI with uv (Python 3.13+)
- Infrastructure: Helm chart in `helm/todo-chatbot/`

---

## Phase 1: Setup (Prerequisites & Structure)

**Purpose**: Verify tools installed and create directory structure

- [X] T001 Verify Docker Desktop, Minikube, and Helm are installed (see quickstart.md prerequisites)
- [X] T002 [P] Create helm/todo-chatbot/ directory structure per plan.md
- [X] T003 [P] Create scripts/ directory for deployment automation
- [X] T004 [P] Create docs/ directory for deployment documentation
- [X] T005 Add helm/todo-chatbot/values-local.yaml to .gitignore

**Checkpoint**: Directory structure ready, tools verified

---

## Phase 2: Foundational (Docker Base Configuration)

**Purpose**: Core Docker configuration that MUST be complete before containerization

**Verification**: AC-003 (Docker environment configured for Minikube)

- [X] T006 Create frontend/.dockerignore with node_modules, .next, .git exclusions
- [X] T007 [P] Create backend/.dockerignore with .venv, __pycache__, .git exclusions
- [X] T008 Verify Next.js config has `output: 'standalone'` in frontend/next.config.ts

**Checkpoint**: Docker ignore files ready, Next.js standalone output configured

---

## Phase 3: User Story 1 - Containerization (Priority: P1)

**Goal**: Create production-ready Docker images for frontend and backend

**Independent Test**:
- AC-004: Frontend Dockerfile builds without errors
- AC-005: Backend Dockerfile builds without errors
- AC-006: Frontend image size < 500MB
- AC-007: Backend image size < 500MB
- AC-008: Images tagged as todo-frontend:local and todo-backend:local

### Implementation for User Story 1

- [X] T009 [US1] Create frontend/Dockerfile with 3-stage build (deps → builder → runner)
  - Stage 1: node:20-alpine, enable pnpm, install frozen dependencies
  - Stage 2: Copy source, set build args (NEXT_PUBLIC_*), run pnpm build
  - Stage 3: Minimal runtime with standalone output, expose port 3000
- [X] T010 [P] [US1] Create backend/Dockerfile with 2-stage build (builder → runner)
  - Stage 1: python:3.13-slim, install uv, sync frozen dependencies
  - Stage 2: Copy venv and app code, expose port 8000, CMD with alembic + uvicorn
- [X] T011 [US1] Build and verify frontend image size (docker build -t todo-frontend:local ./frontend) - 290MB ✓
- [X] T012 [US1] Build and verify backend image size (docker build -t todo-backend:local ./backend) - 401MB ✓

**Checkpoint**: Both Docker images build successfully, size < 500MB each

---

## Phase 4: User Story 2 - Helm Chart Creation (Priority: P1)

**Goal**: Create complete Helm chart for declarative Kubernetes deployment

**Independent Test**:
- AC-021: Secrets not visible in helm get values output
- AC-022: ConfigMap values correctly injected into pods
- Helm lint passes without errors

### Implementation for User Story 2

- [X] T013 [US2] Create helm/todo-chatbot/Chart.yaml with metadata (name: todo-chatbot, version: 0.1.0)
- [X] T014 [P] [US2] Create helm/todo-chatbot/values.yaml with defaults per data-model.md
  - global: environment, imageTag, imagePullPolicy (Never)
  - frontend: replicaCount, image, service (NodePort 30080), resources
  - backend: replicaCount, image, service (ClusterIP 8000), resources
  - ingress: enabled false
  - secrets: empty placeholders
- [X] T015 [P] [US2] Create helm/todo-chatbot/values-local.yaml.example as secret template
- [X] T016 [US2] Create helm/todo-chatbot/templates/_helpers.tpl with common labels and name helpers
- [X] T017 [P] [US2] Create helm/todo-chatbot/templates/configmap.yaml per data-model.md
  - ENVIRONMENT, NEXT_PUBLIC_APP_NAME, CORS_ORIGINS, BETTER_AUTH_URL, BACKEND_URL
- [X] T018 [P] [US2] Create helm/todo-chatbot/templates/secrets.yaml per data-model.md
  - DATABASE_URL, BETTER_AUTH_SECRET, OPENAI_API_KEY, MCP_API_KEY, NEXT_PUBLIC_OPENAI_DOMAIN_KEY
- [X] T019 [US2] Create helm/todo-chatbot/templates/frontend-deployment.yaml per data-model.md
  - Image: todo-frontend:local, port 3000, envFrom configmap/secret
  - Resources: 256Mi/250m requests, 512Mi/500m limits
  - Liveness/readiness probes on /api/health
- [X] T020 [P] [US2] Create helm/todo-chatbot/templates/backend-deployment.yaml per data-model.md
  - Image: todo-backend:local, port 8000, envFrom configmap/secret
  - Resources: 256Mi/250m requests, 512Mi/500m limits
  - Liveness/readiness probes on /api/health
- [X] T021 [P] [US2] Create helm/todo-chatbot/templates/frontend-service.yaml (NodePort 30080)
- [X] T022 [P] [US2] Create helm/todo-chatbot/templates/backend-service.yaml (ClusterIP 8000)
- [X] T023 [P] [US2] Create helm/todo-chatbot/templates/ingress.yaml (optional, controlled by values)
- [X] T024 [US2] Create helm/todo-chatbot/templates/NOTES.txt with post-install instructions
- [X] T025 [US2] Create helm/todo-chatbot/.helmignore
- [X] T026 [US2] Run helm lint ./helm/todo-chatbot to verify chart validity (Note: Helm v4 Windows bug - chart validated via deployment)

**Checkpoint**: Helm chart created, lint passes, ready for deployment

---

## Phase 5: User Story 3 - Minikube Deployment & Verification (Priority: P1)

**Goal**: Deploy application to Minikube and verify all acceptance criteria

**Independent Test**:
- AC-001: Minikube cluster starts successfully
- AC-009: helm install succeeds
- AC-010/011: Pods reach Running state within 60s
- AC-012: No pod restarts after 2 minutes
- AC-014: Frontend accessible at localhost:30080
- AC-015: Backend health check returns 200
- AC-016: Backend connects to external PostgreSQL
- AC-017-020: Auth, CRUD, ChatKit work

### Implementation for User Story 3

- [X] T027 [US3] Start Minikube cluster (minikube start --memory=4096 --cpus=2) ✓
- [X] T028 [US3] Enable Minikube addons (metrics-server, optionally ingress) ✓
- [X] T029 [US3] Configure Docker environment for Minikube (PowerShell: & minikube docker-env | Invoke-Expression) ✓
- [X] T030 [US3] Build frontend image inside Minikube Docker (docker build -t todo-frontend:local ./frontend) ✓
- [X] T031 [US3] Build backend image inside Minikube Docker (docker build -t todo-backend:local ./backend) ✓
- [X] T032 [US3] Create values-local.yaml with actual secrets from project .env files ✓
- [X] T033 [US3] Deploy with Helm (helm install todo ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml) ✓
- [X] T034 [US3] Verify pods reach Running state (kubectl get pods -w) ✓
- [X] T035 [US3] Verify no CrashLoopBackOff after 2 minutes ✓
- [X] T036 [US3] Test frontend accessibility at localhost:30080 or minikube service URL ✓
- [X] T037 [US3] Test backend health endpoint (/api/health returns 200) ✓
- [X] T038 [US3] Verify backend database connectivity via logs ✓
- [X] T039 [US3] Test user authentication flow (sign up / sign in) ✓
  - Sign up: POST /api/auth/sign-up/email returns user + token
  - Sign in: POST /api/auth/sign-in/email returns user + token
  - Sign out: POST /api/auth/sign-out returns {"success":true}
- [X] T040 [US3] Test task CRUD operations ✓
  - Create: POST /api/tasks returns new task with ID
  - Read: GET /api/tasks returns task list
  - Update: PATCH /api/tasks/{id}/toggle sets completed=true
  - Delete: DELETE /api/tasks/{id} removes task from list
- [X] T041 [US3] Test ChatKit widget loads and MCP connection works ✓
  - ChatKit session: POST /api/chatkit/session returns client_secret
  - MCP endpoint: POST /mcp responds with JSON-RPC

**Checkpoint**: Application fully functional in Minikube, all P1 acceptance criteria pass

---

## Phase 6: User Story 4 - AI DevOps Integration (Priority: P2)

**Goal**: Enable AI-assisted cluster operations with kubectl-ai and kagent

**Independent Test**:
- AC-025: kubectl-ai executes basic queries
- AC-026: kubectl-ai can scale deployments
- AC-027: kagent provides cluster health insights
- AC-028: AI tools diagnose pod issues

### Implementation for User Story 4

- [ ] T042 [US4] Install kubectl-ai (go install github.com/sozercan/kubectl-ai@latest) - Requires Go installation
- [ ] T043 [P] [US4] Configure OPENAI_API_KEY environment variable for kubectl-ai - Requires T042
- [ ] T044 [US4] Test kubectl-ai basic query ("show all running pods") - Requires T042
- [ ] T045 [US4] Test kubectl-ai scaling ("scale backend to 2 replicas") - Requires T042
- [ ] T046 [US4] Test kubectl-ai debugging ("why is pod not ready?") - Requires T042
- [ ] T047 [P] [US4] Install kagent if available on Windows - Optional
- [ ] T048 [US4] Test kagent health check and cluster analysis (if installed) - Optional

**Checkpoint**: AI DevOps tools operational for cluster management

---

## Phase 7: User Story 5 - Documentation & Scripts (Priority: P2)

**Goal**: Create deployment automation scripts and comprehensive documentation

**Independent Test**:
- Scripts execute without errors
- Documentation covers all quickstart steps
- Troubleshooting guide addresses common issues

### Implementation for User Story 5

- [X] T049 [US5] Create scripts/k8s-build.sh (or .ps1) to build both Docker images
- [X] T050 [P] [US5] Create scripts/k8s-deploy.sh (or .ps1) to deploy with Helm
- [X] T051 [P] [US5] Create scripts/k8s-teardown.sh (or .ps1) to clean up resources
- [X] T052 [US5] Create docs/kubernetes-local-deployment.md with step-by-step guide
- [X] T053 [P] [US5] Create docs/ai-devops-tools.md with kubectl-ai and kagent usage examples
- [X] T054 [P] [US5] Create docs/kubernetes-troubleshooting.md with common issues and solutions

**Checkpoint**: All scripts and documentation complete

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and observability verification

**Verification**: AC-023, AC-024, AC-029-032

- [X] T055 [P] Verify helm upgrade applies changes without downtime (AC-023) - Manual test ✓
- [X] T056 [P] Verify environment variables match between local dev and K8s (AC-024) - Manual test ✓
- [X] T057 Verify kubectl logs shows structured JSON from backend (AC-029) ✓
- [X] T058 [P] Implement request ID header propagation (X-Request-ID) from frontend to backend (AC-030) ✓
  - Frontend: Add middleware to generate/forward X-Request-ID header on API calls
  - Backend: Log X-Request-ID in all request logs for traceability
- [X] T059 Verify health check endpoints return appropriate status codes (AC-031) ✓
- [X] T060 Verify kubectl top pods displays resource usage via metrics-server (AC-032) ✓
- [X] T061 Run complete quickstart.md validation end-to-end - Manual test ✓

**Checkpoint**: All acceptance criteria verified, deployment complete

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup
    │
    ▼
Phase 2: Foundational (Docker config)
    │
    ├──────────────────────────────────┐
    ▼                                  ▼
Phase 3: US1 Containerization    Phase 4: US2 Helm Chart
    │                                  │
    └──────────────┬───────────────────┘
                   ▼
          Phase 5: US3 Deployment & Verification
                   │
    ┌──────────────┴───────────────┐
    ▼                              ▼
Phase 6: US4 AI DevOps      Phase 7: US5 Docs & Scripts
    │                              │
    └──────────────┬───────────────┘
                   ▼
          Phase 8: Polish
```

### User Story Dependencies

| User Story | Depends On | Can Parallel With |
|------------|------------|-------------------|
| US1 (Containerization) | Phase 2 | US2 (after T008) |
| US2 (Helm Chart) | Phase 2 | US1 |
| US3 (Deployment) | US1, US2 | None |
| US4 (AI DevOps) | US3 | US5 |
| US5 (Documentation) | US3 | US4 |

### Within Each User Story

- Docker files before image builds
- Helm templates before helm lint
- helm install before verification tests
- Core functionality before AI tools

### Parallel Opportunities

**Phase 2 (all parallel)**:
- T006 (frontend .dockerignore) ‖ T007 (backend .dockerignore)

**Phase 3 (after T008)**:
- T009 (frontend Dockerfile) ‖ T010 (backend Dockerfile)

**Phase 4 (within chart creation)**:
- T014 (values.yaml) ‖ T015 (values-local example)
- T017 (configmap) ‖ T018 (secrets)
- T019 (frontend deploy) ‖ T020 (backend deploy)
- T021 (frontend svc) ‖ T022 (backend svc) ‖ T023 (ingress)

**Phase 5 (builds can parallel)**:
- T030 (frontend build) ‖ T031 (backend build) - after Docker env set

**Phase 6-7 (entire phases parallel)**:
- US4 (AI DevOps) ‖ US5 (Documentation)

---

## Parallel Example: Helm Chart Templates

```bash
# Launch all independent template files together:
Task: "Create configmap.yaml"
Task: "Create secrets.yaml"
Task: "Create frontend-deployment.yaml"
Task: "Create backend-deployment.yaml"
Task: "Create frontend-service.yaml"
Task: "Create backend-service.yaml"
Task: "Create ingress.yaml"
```

---

## Implementation Strategy

### MVP First (Deploy to Minikube)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T008)
3. Complete Phase 3: US1 Containerization (T009-T012)
4. Complete Phase 4: US2 Helm Chart (T013-T026)
5. Complete Phase 5: US3 Deployment (T027-T041)
6. **STOP and VALIDATE**: All P1 acceptance criteria pass
7. Demo working Kubernetes deployment

### Full Delivery (Add AI & Docs)

8. Complete Phase 6: US4 AI DevOps (T042-T048)
9. Complete Phase 7: US5 Documentation (T049-T054)
10. Complete Phase 8: Polish (T055-T060)
11. All acceptance criteria verified

### Parallel Team Strategy

With 2 developers after Phase 2:
- Developer A: US1 (Containerization) → helps US3
- Developer B: US2 (Helm Chart) → helps US3

After Phase 5 (US3 complete):
- Developer A: US4 (AI DevOps)
- Developer B: US5 (Documentation)

---

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 61 |
| Phase 1 (Setup) | 5 |
| Phase 2 (Foundational) | 3 |
| Phase 3 - US1 (Containerization) | 4 |
| Phase 4 - US2 (Helm Chart) | 14 |
| Phase 5 - US3 (Deployment) | 15 |
| Phase 6 - US4 (AI DevOps) | 7 |
| Phase 7 - US5 (Documentation) | 6 |
| Phase 8 (Polish) | 7 |
| Parallelizable [P] Tasks | 26 |

**MVP Scope**: Phases 1-5 (41 tasks) - Full Minikube deployment working

**Acceptance Criteria Coverage**:
- AC-001 to AC-003: Phase 5 (US3)
- AC-004 to AC-008: Phase 3 (US1)
- AC-009 to AC-013: Phase 5 (US3)
- AC-014 to AC-020: Phase 5 (US3)
- AC-021 to AC-024: Phase 4 (US2), Phase 8
- AC-025 to AC-028: Phase 6 (US4)
- AC-029 to AC-032: Phase 8

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [US#] label maps task to functional area for traceability
- Manual testing only - no automated test suite for infrastructure
- Secrets MUST be in values-local.yaml (gitignored), never committed
- All Docker images built inside Minikube Docker daemon
- External Neon PostgreSQL - no database in Kubernetes
