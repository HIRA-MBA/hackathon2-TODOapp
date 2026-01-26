# Local Kubernetes Deployment Guide

This guide walks you through deploying the Todo Chatbot application to a local Kubernetes cluster using Minikube and Helm.

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| Docker Desktop | 4.x+ | `winget install Docker.DockerDesktop` |
| Minikube | 1.32+ | `winget install Kubernetes.minikube` |
| Helm | 3.14+ | `winget install Helm.Helm` |
| kubectl | (bundled with Docker Desktop) | - |

### System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 8GB | 16GB |
| CPU | 4 cores | 8 cores |
| Disk | 20GB free | 40GB free |

Verify installations:

```powershell
docker --version
minikube version
helm version --short
kubectl version --client
```

## Quick Start

### 1. Start Minikube

```powershell
minikube start --memory=4096 --cpus=2
minikube addons enable metrics-server
```

### 2. Configure Docker Environment

```powershell
# Point Docker CLI to Minikube's Docker daemon
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
```

> **Note**: Run this command in every new terminal session.

### 3. Build Docker Images

```powershell
# Using the build script
.\scripts\k8s-build.ps1

# Or manually
docker build -t todo-frontend:local ./frontend
docker build -t todo-backend:local ./backend
```

Verify images:

```powershell
docker images | Select-String "todo"
```

### 4. Configure Secrets

```powershell
# Copy the example file
cp helm/todo-chatbot/values-local.yaml.example helm/todo-chatbot/values-local.yaml

# Edit with your actual values
notepad helm/todo-chatbot/values-local.yaml
```

**Required secrets:**

- `databaseUrl`: Neon PostgreSQL connection string (async format)
- `betterAuthSecret`: JWT signing secret
- `openaiApiKey`: OpenAI API key (sk-...)
- `mcpApiKey`: MCP server authentication key
- `openaiDomainKey`: ChatKit domain key

### 5. Deploy with Helm

```powershell
# Using the deploy script
.\scripts\k8s-deploy.ps1

# Or manually
helm install todo ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml
```

### 6. Verify Deployment

```powershell
# Watch pods start
kubectl get pods -w

# Expected output (after ~60s):
# NAME                               READY   STATUS    RESTARTS   AGE
# todo-todo-chatbot-frontend-xxx     1/1     Running   0          30s
# todo-todo-chatbot-backend-xxx      1/1     Running   0          30s
```

### 7. Access the Application

```powershell
# Option 1: Direct access via NodePort
start http://localhost:30080

# Option 2: Get Minikube service URL
minikube service todo-todo-chatbot-frontend --url
```

## Common Operations

### Upgrade Deployment

```powershell
helm upgrade todo ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml
```

### View Logs

```powershell
# Frontend logs
kubectl logs -f deployment/todo-todo-chatbot-frontend

# Backend logs
kubectl logs -f deployment/todo-todo-chatbot-backend
```

### Scale Deployments

```powershell
# Scale backend to 2 replicas
kubectl scale deployment/todo-todo-chatbot-backend --replicas=2
```

### Check Resource Usage

```powershell
kubectl top pods
```

### Restart Pods

```powershell
kubectl rollout restart deployment/todo-todo-chatbot-frontend
kubectl rollout restart deployment/todo-todo-chatbot-backend
```

### Uninstall

```powershell
# Using the teardown script
.\scripts\k8s-teardown.ps1

# Or manually
helm uninstall todo
```

### Stop Minikube

```powershell
minikube stop
```

### Delete Minikube Cluster

```powershell
minikube delete
```

## Development Workflow

### Quick Rebuild

When you make code changes:

```powershell
# 1. Rebuild the image
docker build -t todo-frontend:local ./frontend

# 2. Restart the deployment
kubectl rollout restart deployment/todo-todo-chatbot-frontend

# 3. Watch pods restart
kubectl get pods -w
```

### Environment Variables

ConfigMap values (non-sensitive):

```powershell
kubectl get configmap todo-todo-chatbot-config -o yaml
```

Secret values are base64 encoded:

```powershell
# View secret keys (not values)
kubectl get secret todo-todo-chatbot-secrets -o jsonpath='{.data}' | ConvertFrom-Json
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MINIKUBE CLUSTER                         │
│                                                              │
│  ┌────────────────────┐      ┌────────────────────┐         │
│  │  Frontend Pod      │      │  Backend Pod       │         │
│  │  (Next.js)         │─────▶│  (FastAPI)         │         │
│  │  Port: 3000        │      │  Port: 8000        │         │
│  └─────────┬──────────┘      └─────────┬──────────┘         │
│            │                           │                     │
│  ┌─────────▼──────────┐      ┌─────────▼──────────┐         │
│  │  frontend-service  │      │  backend-service   │         │
│  │  NodePort: 30080   │      │  ClusterIP: 8000   │         │
│  └────────────────────┘      └────────────────────┘         │
│                                         │                    │
│  ┌────────────────────┐                 │                    │
│  │     ConfigMap      │                 │                    │
│  │     Secrets        │                 │                    │
│  └────────────────────┘                 │                    │
└─────────────────────────────────────────┼────────────────────┘
                                          │
                                          ▼ (External SSL)
                               ┌────────────────────┐
                               │  Neon PostgreSQL   │
                               └────────────────────┘
```

## Next Steps

- [AI DevOps Tools Guide](./ai-devops-tools.md) - Using kubectl-ai and kagent
- [Troubleshooting Guide](./kubernetes-troubleshooting.md) - Common issues and solutions
