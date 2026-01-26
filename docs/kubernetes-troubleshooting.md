# Kubernetes Troubleshooting Guide

Common issues and solutions for the local Kubernetes deployment.

## Quick Diagnostics

```powershell
# Overall cluster health
kubectl get pods
kubectl get events --sort-by='.lastTimestamp'

# Specific deployment status
kubectl describe deployment todo-todo-chatbot-backend
kubectl describe deployment todo-todo-chatbot-frontend
```

## Pod Issues

### Pods Stuck in Pending

**Symptom**: Pod status shows `Pending` for an extended time.

**Diagnosis**:

```powershell
kubectl describe pod <pod-name>
# Look for "Events" section
```

**Common Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| Insufficient resources | Increase Minikube resources: `minikube stop && minikube start --memory=6144 --cpus=4` |
| Node not ready | Check node status: `kubectl get nodes` |
| PVC not bound | Check persistent volumes if using any |

### Pods in CrashLoopBackOff

**Symptom**: Pod keeps restarting with `CrashLoopBackOff` status.

**Diagnosis**:

```powershell
# View logs from the crashed container
kubectl logs <pod-name> --previous

# Get detailed pod info
kubectl describe pod <pod-name>
```

**Common Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| Database connection failed | Verify `DATABASE_URL` in secrets, check SSL mode |
| Missing environment variables | Verify values-local.yaml has all required secrets |
| Application error | Check logs for stack traces |
| Liveness probe failing | Increase `initialDelaySeconds` in deployment |

### ImagePullBackOff

**Symptom**: Pod status shows `ImagePullBackOff` or `ErrImagePull`.

**Diagnosis**:

```powershell
kubectl describe pod <pod-name>
# Look for image pull errors
```

**Solutions**:

```powershell
# Verify Docker is configured for Minikube
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Check if images exist
docker images | Select-String "todo"

# If missing, rebuild
docker build -t todo-frontend:local ./frontend
docker build -t todo-backend:local ./backend

# Delete the pod to force recreation
kubectl delete pod <pod-name>
```

### OOMKilled

**Symptom**: Pod terminated with `OOMKilled` reason.

**Solutions**:

1. Increase memory limits in values.yaml:

```yaml
backend:
  resources:
    limits:
      memory: "1Gi"  # Increase from 512Mi
```

2. Upgrade and restart:

```powershell
helm upgrade todo ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml
```

## Service Issues

### Cannot Access Frontend

**Symptom**: `http://localhost:30080` doesn't load.

**Diagnosis**:

```powershell
# Check if service is created
kubectl get svc

# Verify NodePort
kubectl get svc todo-todo-chatbot-frontend -o jsonpath='{.spec.ports[0].nodePort}'

# Check if pods are ready
kubectl get pods -l app.kubernetes.io/component=frontend
```

**Solutions**:

```powershell
# Use Minikube service command
minikube service todo-todo-chatbot-frontend --url

# Or use port-forward
kubectl port-forward svc/todo-todo-chatbot-frontend 3000:80
```

### Backend Health Check Failing

**Symptom**: Backend pod not ready, health checks failing.

**Diagnosis**:

```powershell
# Test health endpoint from within the cluster
kubectl run test --rm -it --image=busybox -- wget -qO- http://todo-todo-chatbot-backend:8000/api/health

# Check backend logs
kubectl logs deployment/todo-todo-chatbot-backend
```

**Solutions**:

| Cause | Solution |
|-------|----------|
| Migrations still running | Wait longer (60s startup time) |
| Database unreachable | Verify DATABASE_URL and network connectivity |
| Port mismatch | Ensure backend listens on 8000 |

## Database Issues

### Backend Cannot Connect to Neon PostgreSQL

**Symptom**: Backend logs show database connection errors.

**Diagnosis**:

```powershell
kubectl logs deployment/todo-todo-chatbot-backend | Select-String -Pattern "database|postgres|connection"
```

**Solutions**:

1. **Verify DATABASE_URL format**:
   ```
   postgresql+asyncpg://user:password@host:port/database?sslmode=require
   ```

2. **Check SSL requirement**: Neon requires SSL. Ensure `?sslmode=require` is in the URL.

3. **Test from pod**:
   ```powershell
   kubectl exec -it deployment/todo-todo-chatbot-backend -- python -c "import asyncpg; print('asyncpg ok')"
   ```

4. **Network egress**: Ensure Minikube can reach external hosts:
   ```powershell
   kubectl run test --rm -it --image=busybox -- nslookup <your-neon-host>
   ```

## Helm Issues

### Helm Install Fails

**Symptom**: `helm install` returns errors.

**Solutions**:

```powershell
# Validate chart syntax
helm lint ./helm/todo-chatbot

# Template the chart to see generated YAML
helm template todo ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml > debug.yaml
notepad debug.yaml

# Check for missing values
helm install todo ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml --dry-run
```

### Helm Upgrade Stuck

**Symptom**: `helm upgrade` hangs or shows pending status.

**Solutions**:

```powershell
# Check release status
helm status todo

# Force rollback
helm rollback todo 1

# If needed, uninstall and reinstall
helm uninstall todo
helm install todo ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml
```

## Minikube Issues

### Minikube Won't Start

**Solutions**:

```powershell
# Delete and recreate
minikube delete
minikube start --memory=4096 --cpus=2

# Or try a different driver
minikube start --driver=hyperv --memory=4096 --cpus=2
```

### Docker Images Not Found After Restart

**Symptom**: Images existed before but are gone after Minikube restart.

**Solution**:

Images in Minikube's Docker daemon are preserved. Reconfigure the Docker environment:

```powershell
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
docker images | Select-String "todo"
```

If truly gone, rebuild:

```powershell
.\scripts\k8s-build.ps1
```

## Secrets Issues

### Secrets Not Applied

**Symptom**: Application shows empty or default values.

**Diagnosis**:

```powershell
# Verify secret exists
kubectl get secret todo-todo-chatbot-secrets

# Check mounted environment in pod
kubectl exec deployment/todo-todo-chatbot-backend -- env | Select-String "DATABASE_URL"
```

**Solutions**:

1. Ensure values-local.yaml has correct values
2. Re-deploy: `helm upgrade todo ./helm/todo-chatbot -f ./helm/todo-chatbot/values-local.yaml`
3. Restart pods: `kubectl rollout restart deployment/todo-todo-chatbot-backend`

## Useful Debug Commands

```powershell
# Watch all resources
kubectl get all -w

# Get events sorted by time
kubectl get events --sort-by='.lastTimestamp'

# Describe all pods
kubectl describe pods

# View resource usage
kubectl top pods

# Execute command in pod
kubectl exec -it deployment/todo-todo-chatbot-backend -- /bin/sh

# Port forward for direct access
kubectl port-forward deployment/todo-todo-chatbot-backend 8000:8000
```

## Reset Everything

When all else fails:

```powershell
# Uninstall Helm release
helm uninstall todo

# Delete all resources
kubectl delete all --all

# Stop and delete Minikube
minikube stop
minikube delete

# Start fresh
minikube start --memory=4096 --cpus=2
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
.\scripts\k8s-build.ps1
.\scripts\k8s-deploy.ps1
```

## See Also

- [Kubernetes Local Deployment](./kubernetes-local-deployment.md)
- [AI DevOps Tools](./ai-devops-tools.md)
