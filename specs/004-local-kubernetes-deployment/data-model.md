# Data Model: Phase IV - Local Kubernetes Deployment

**Feature**: Local Kubernetes Deployment
**Date**: 2026-01-22
**Type**: Infrastructure/Configuration (not database entities)

---

## 1. Kubernetes Resource Model

### 1.1 Deployments

#### frontend-deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-frontend
spec:
  replicas: {{ .Values.frontend.replicaCount }}
  selector:
    matchLabels:
      app: todo-frontend
  template:
    spec:
      containers:
        - name: frontend
          image: todo-frontend:local
          ports:
            - containerPort: 3000
          envFrom:
            - configMapRef: app-config
            - secretRef: app-secrets
          resources:
            requests: { memory: 256Mi, cpu: 250m }
            limits: { memory: 512Mi, cpu: 500m }
```

#### backend-deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-backend
spec:
  replicas: {{ .Values.backend.replicaCount }}
  selector:
    matchLabels:
      app: todo-backend
  template:
    spec:
      containers:
        - name: backend
          image: todo-backend:local
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef: app-config
            - secretRef: app-secrets
          resources:
            requests: { memory: 256Mi, cpu: 250m }
            limits: { memory: 512Mi, cpu: 500m }
```

---

### 1.2 Services

#### frontend-service
| Field | Value |
|-------|-------|
| Type | NodePort |
| Port | 80 |
| TargetPort | 3000 |
| NodePort | 30080 |
| Selector | `app: todo-frontend` |

#### backend-service
| Field | Value |
|-------|-------|
| Type | ClusterIP |
| Port | 8000 |
| TargetPort | 8000 |
| Selector | `app: todo-backend` |

---

### 1.3 ConfigMap

**Name**: `app-config`

| Key | Value | Used By |
|-----|-------|---------|
| ENVIRONMENT | development | Backend |
| NEXT_PUBLIC_APP_NAME | Todo App (K8s) | Frontend |
| CORS_ORIGINS | http://localhost:30080 | Backend |
| BETTER_AUTH_URL | http://frontend-service:80 | Backend |
| BACKEND_URL | http://backend-service:8000 | Frontend |
| OPENAI_CHATKIT_WORKFLOW_ID | (from config) | Frontend |
| MCP_DEFAULT_USER_ID | (test user id) | Backend |

---

### 1.4 Secrets

**Name**: `app-secrets`

| Key | Source | Used By |
|-----|--------|---------|
| DATABASE_URL | values-local.yaml | Frontend, Backend |
| BETTER_AUTH_SECRET | values-local.yaml | Frontend, Backend |
| OPENAI_API_KEY | values-local.yaml | Frontend, Backend |
| MCP_API_KEY | values-local.yaml | Backend |
| NEXT_PUBLIC_OPENAI_DOMAIN_KEY | values-local.yaml | Frontend |

---

## 2. Helm Values Structure

### values.yaml (Schema)

```yaml
global:
  environment: string        # development | production
  imageTag: string           # default: local
  imagePullPolicy: string    # Never | IfNotPresent | Always

frontend:
  replicaCount: integer      # default: 1
  image:
    repository: string       # default: todo-frontend
    tag: string              # default: local
  service:
    type: string             # NodePort | LoadBalancer
    port: integer            # default: 80
    nodePort: integer        # default: 30080
  resources:
    requests:
      memory: string         # default: 256Mi
      cpu: string            # default: 250m
    limits:
      memory: string         # default: 512Mi
      cpu: string            # default: 500m

backend:
  replicaCount: integer
  image:
    repository: string
    tag: string
  service:
    type: string             # ClusterIP
    port: integer            # default: 8000
  resources:
    requests: { memory, cpu }
    limits: { memory, cpu }
  runMigrations: boolean     # default: true

ingress:
  enabled: boolean           # default: false
  className: string          # nginx
  hosts:
    - host: string
      paths:
        - path: string
          pathType: string   # Prefix | Exact
          service: string    # frontend | backend

secrets:                     # Populated in values-local.yaml
  databaseUrl: string
  betterAuthSecret: string
  openaiApiKey: string
  mcpApiKey: string
  openaiDomainKey: string
```

---

## 3. Docker Image Structure

### Frontend Image Layers

```
todo-frontend:local
├── /app
│   ├── server.js           # Next.js standalone server
│   ├── .next/
│   │   └── static/         # Static assets
│   └── public/             # Public files
└── node (runtime)
```

### Backend Image Layers

```
todo-backend:local
├── /app
│   ├── .venv/              # Python virtual environment
│   ├── app/                # FastAPI application
│   ├── alembic/            # Database migrations
│   └── alembic.ini
└── python (runtime)
```

---

## 4. Environment Variable Flow

```
┌─────────────────┐
│ values-local.yaml│ (secrets, gitignored)
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Helm Chart    │────►│ K8s Secrets     │
│   templates/    │     │ K8s ConfigMaps  │
└─────────────────┘     └────────┬────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌─────────────────┐                             ┌─────────────────┐
│ Frontend Pod    │                             │ Backend Pod     │
│ envFrom:        │                             │ envFrom:        │
│  - configMapRef │                             │  - configMapRef │
│  - secretRef    │                             │  - secretRef    │
└─────────────────┘                             └─────────────────┘
```

---

## 5. Network Topology

```
External Traffic
       │
       ▼ (localhost:30080)
┌──────────────────┐
│ frontend-service │ (NodePort)
│ port: 80         │
│ nodePort: 30080  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Frontend Pod     │
│ port: 3000       │
└────────┬─────────┘
         │ (API calls)
         ▼
┌──────────────────┐
│ backend-service  │ (ClusterIP)
│ port: 8000       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Backend Pod      │
│ port: 8000       │
└────────┬─────────┘
         │ (SSL/TCP)
         ▼
┌──────────────────┐
│ Neon PostgreSQL  │ (External)
└──────────────────┘
```
