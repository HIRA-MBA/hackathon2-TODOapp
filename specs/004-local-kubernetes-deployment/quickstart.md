# Quickstart: Local Kubernetes Deployment

**Time**: ~15 minutes | **Prerequisites**: Docker Desktop, 8GB RAM

---

## Prerequisites Check

```powershell
# Verify installations
docker --version    # Docker Desktop 4.x+
minikube version    # v1.32+
helm version        # v3.14+
```

If missing, install:
```powershell
winget install Docker.DockerDesktop
winget install Kubernetes.minikube
winget install Helm.Helm
```

---

## Step 1: Start Minikube

```powershell
minikube start --memory=4096 --cpus=2
minikube addons enable metrics-server
```

---

## Step 2: Configure Docker Environment

```powershell
# Point Docker CLI to Minikube's Docker daemon
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
```

> Note: Run this in every new terminal session, or add to your profile.

---

## Step 3: Build Images

```powershell
docker build -t todo-frontend:local ./frontend
docker build -t todo-backend:local ./backend
```

Verify:
```powershell
docker images | Select-String "todo"
```

---

## Step 4: Configure Secrets

```powershell
# Copy template
cp helm/todo-chatbot/values-local.yaml.example helm/todo-chatbot/values-local.yaml

# Edit with your actual values
notepad helm/todo-chatbot/values-local.yaml
```

Required secrets:
- `DATABASE_URL`: Neon PostgreSQL connection string
- `BETTER_AUTH_SECRET`: JWT signing secret
- `OPENAI_API_KEY`: OpenAI API key
- `MCP_API_KEY`: MCP server key
- `NEXT_PUBLIC_OPENAI_DOMAIN_KEY`: ChatKit domain key

---

## Step 5: Deploy with Helm

```powershell
helm install todo ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml
```

---

## Step 6: Verify Deployment

```powershell
# Watch pods start
kubectl get pods -w

# Expected output (after ~60s):
# NAME                        READY   STATUS    RESTARTS   AGE
# todo-frontend-xxx           1/1     Running   0          30s
# todo-backend-xxx            1/1     Running   0          30s
```

---

## Step 7: Access Application

```powershell
# Get frontend URL
minikube service todo-frontend --url

# Or access directly
start http://localhost:30080
```

---

## Common Commands

| Action | Command |
|--------|---------|
| View pods | `kubectl get pods` |
| View logs | `kubectl logs -f deployment/todo-backend` |
| Upgrade | `helm upgrade todo ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml` |
| Uninstall | `helm uninstall todo` |
| Stop cluster | `minikube stop` |
| Delete cluster | `minikube delete` |

---

## AI-Assisted Operations

```powershell
# Set API key for kubectl-ai
$env:OPENAI_API_KEY = "sk-..."

# Examples
kubectl-ai "show all running pods"
kubectl-ai "why is the backend pod not ready?"
kubectl-ai "scale frontend to 2 replicas"
```

---

## Troubleshooting

### Pods stuck in Pending
```powershell
kubectl describe pod <pod-name>
# Check Events section for resource issues
```

### Backend can't connect to database
```powershell
kubectl logs deployment/todo-backend | Select-String "database"
# Verify DATABASE_URL in secrets
```

### Image pull errors
```powershell
# Ensure Docker env is set
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
# Rebuild images
docker build -t todo-backend:local ./backend
# Delete and recreate pod
kubectl delete pod -l app=todo-backend
```

---

## Cleanup

```powershell
helm uninstall todo
minikube stop
# Or full cleanup:
minikube delete
```
