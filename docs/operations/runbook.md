# Operational Runbook: Todo Chatbot (Phase V)

Per T094: Operational procedures for the cloud-native event-driven architecture.

---

## Service Overview

| Service | Port | Description | Health Endpoint |
|---------|------|-------------|-----------------|
| Backend (FastAPI) | 8000 | Core API, task CRUD, auth | `/api/health`, `/api/health/ready` |
| Frontend (Next.js) | 3000 | Web UI | `/` |
| WebSocket Service | 8001 | Real-time task sync | `/health`, `/health/ready` |
| Recurring Task Service | 8002 | Auto-creates recurring task instances | `/health`, `/health/ready` |
| Notification Service | 8003 | Reminder delivery | `/health`, `/health/ready` |

### Infrastructure Dependencies

| Component | Purpose | Local | Production |
|-----------|---------|-------|------------|
| PostgreSQL (Neon) | Primary database | Neon Cloud | Neon Cloud |
| Redpanda | Event streaming (Kafka-compatible) | Docker / Redpanda Cloud | Redpanda Cloud |
| Redis | Dapr state store | Docker | In-cluster or managed |
| Dapr | Sidecar for pub/sub, state, secrets | `dapr init` | Dapr on K8s |

---

## Common Operations

### 1. Check Service Health

```bash
# Backend
curl http://localhost:8000/api/health
curl http://localhost:8000/api/health/ready

# WebSocket
curl http://localhost:8001/health
curl http://localhost:8001/health/ready
curl http://localhost:8001/stats

# Recurring Task
curl http://localhost:8002/health
curl http://localhost:8002/health/ready

# Notification
curl http://localhost:8003/health
curl http://localhost:8003/health/ready
```

### 2. Kubernetes Pod Health

```bash
# Check all pods
kubectl get pods -l app.kubernetes.io/instance=todo-chatbot

# Check specific service
kubectl get pods -l app.kubernetes.io/component=backend
kubectl get pods -l app.kubernetes.io/component=websocket
kubectl get pods -l app.kubernetes.io/component=recurring-task
kubectl get pods -l app.kubernetes.io/component=notification

# Describe a pod for events and probe status
kubectl describe pod <pod-name>

# Check pod logs
kubectl logs <pod-name> --tail=100 -f
```

### 3. Dapr Dashboard

```bash
# Local development
dapr dashboard
# Opens http://localhost:8080

# Kubernetes
kubectl port-forward svc/dapr-dashboard 8080:8080 -n dapr-system
```

Verify in the dashboard:
- All components show "healthy" status
- Subscriptions are correctly registered
- Application IDs match expected services

---

## Event Streaming Operations

### 4. Redpanda Topic Management

```bash
# List topics
rpk topic list --brokers localhost:9092

# Check topic details
rpk topic describe task-events --brokers localhost:9092
rpk topic describe task-updates --brokers localhost:9092
rpk topic describe reminders --brokers localhost:9092

# Consume recent messages (for debugging)
rpk topic consume task-events --brokers localhost:9092 --num 10
rpk topic consume task-updates --brokers localhost:9092 --num 10
rpk topic consume reminders --brokers localhost:9092 --num 10

# Check consumer groups (lag monitoring)
rpk group list --brokers localhost:9092
rpk group describe <group-name> --brokers localhost:9092
```

### 5. Redpanda Cloud (Production)

```bash
# Set profile
rpk profile create prod --set brokers=<cluster>.redpanda.cloud:9092 \
  --set tls.enabled=true \
  --set sasl.mechanism=SCRAM-SHA-256 \
  --set sasl.user=<username> \
  --set sasl.password=<password>

# Use profile
rpk topic list --profile prod
rpk group list --profile prod
```

---

## Troubleshooting

### 6. Events Not Flowing

**Symptoms**: Tasks created in UI don't trigger recurring task creation or real-time sync.

**Diagnosis**:
```bash
# 1. Check Dapr sidecar health
curl http://localhost:3500/v1.0/healthz

# 2. Check Dapr metadata (shows registered subscriptions)
curl http://localhost:3500/v1.0/metadata | python -m json.tool

# 3. Check backend logs for event publishing errors
kubectl logs -l app.kubernetes.io/component=backend --tail=50 | grep "event_publish"

# 4. Check consumer service logs
kubectl logs -l app.kubernetes.io/component=recurring-task --tail=50
kubectl logs -l app.kubernetes.io/component=notification --tail=50

# 5. Verify topics have messages
rpk topic consume task-events --brokers localhost:9092 --num 5
```

**Resolution**:
- If Dapr sidecar is unhealthy: restart the pod (`kubectl delete pod <name>`)
- If topics are empty: check backend event publisher logs
- If topics have messages but consumers aren't processing: check consumer group lag

### 7. WebSocket Connections Failing

**Symptoms**: Real-time sync not working, connection status shows disconnected.

**Diagnosis**:
```bash
# 1. Check WebSocket service health
curl http://localhost:8001/health

# 2. Check connection stats
curl http://localhost:8001/stats

# 3. Check WebSocket logs
kubectl logs -l app.kubernetes.io/component=websocket --tail=50

# 4. Test WebSocket connectivity
# In browser console:
# new WebSocket('ws://localhost:8001/ws?token=<jwt>')
```

**Resolution**:
- If service is unhealthy: check resource limits, restart pod
- If auth fails: verify JWT secret matches between backend and websocket service
- If Dapr subscription issues: check `/dapr/subscribe` endpoint returns correct config

### 8. Database Connection Issues

**Symptoms**: Backend returns 503, readiness probe fails.

**Diagnosis**:
```bash
# 1. Check readiness endpoint
curl http://localhost:8000/api/health/ready

# 2. Check backend logs
kubectl logs -l app.kubernetes.io/component=backend --tail=50 | grep "database"

# 3. Verify DATABASE_URL secret
kubectl get secret todo-chatbot-secrets -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

**Resolution**:
- Verify Neon database is accessible (check Neon dashboard)
- Ensure DATABASE_URL has `?sslmode=require` for Neon connections
- Check if connection pool is exhausted (restart pod to reset)

### 9. Reminder Notifications Not Sending

**Symptoms**: Tasks with due dates don't trigger reminder notifications.

**Diagnosis**:
```bash
# 1. Check notification service logs
kubectl logs -l app.kubernetes.io/component=notification --tail=50 | grep "reminder"

# 2. Check if reminder events are being published
rpk topic consume reminders --brokers localhost:9092 --num 5

# 3. Check scheduler status
kubectl logs -l app.kubernetes.io/component=notification --tail=50 | grep "scheduler"
```

**Resolution**:
- If no events on `reminders` topic: check backend reminder publisher
- If events exist but not processed: check notification service handlers
- If quiet hours: verify user preference settings

---

## Deployment Operations

### 10. Deploy with Helm

```bash
# Local (Minikube/Docker Desktop)
helm upgrade --install todo-chatbot helm/todo-chatbot \
  -f helm/todo-chatbot/values.yaml \
  -f helm/todo-chatbot/values-local.yaml

# DOKS (DigitalOcean)
helm upgrade --install todo-chatbot helm/todo-chatbot \
  -f helm/todo-chatbot/values.yaml \
  -f helm/values-doks.yaml

# GKE (Google Cloud)
helm upgrade --install todo-chatbot helm/todo-chatbot \
  -f helm/todo-chatbot/values.yaml \
  -f helm/values-gke.yaml

# OKE (Oracle Cloud)
helm upgrade --install todo-chatbot helm/todo-chatbot \
  -f helm/todo-chatbot/values.yaml \
  -f helm/values-oke.yaml
```

### 11. Rolling Restart (Zero-Downtime)

```bash
# Restart a specific component
kubectl rollout restart deployment/todo-chatbot-backend
kubectl rollout restart deployment/todo-chatbot-websocket
kubectl rollout restart deployment/todo-chatbot-recurring-task
kubectl rollout restart deployment/todo-chatbot-notification

# Watch rollout status
kubectl rollout status deployment/todo-chatbot-backend
```

### 12. Rollback

```bash
# Check rollout history
kubectl rollout history deployment/todo-chatbot-backend

# Rollback to previous version
kubectl rollout undo deployment/todo-chatbot-backend

# Rollback Helm release
helm rollback todo-chatbot <revision>
helm history todo-chatbot
```

---

## Monitoring

### 13. Log Aggregation

All services emit structured JSON logs with correlation IDs.

```bash
# Backend structured logs (JSON format)
kubectl logs -l app.kubernetes.io/component=backend --tail=100 | python -m json.tool

# Filter by correlation ID across services
CORR_ID="abc-123"
kubectl logs -l app.kubernetes.io/instance=todo-chatbot --all-containers \
  | grep "$CORR_ID"

# Follow logs for all services
kubectl logs -l app.kubernetes.io/instance=todo-chatbot --all-containers -f
```

### 14. Resource Monitoring

```bash
# Resource usage
kubectl top pods -l app.kubernetes.io/instance=todo-chatbot

# Check resource quotas
kubectl describe resourcequota

# Check HPA status (if configured)
kubectl get hpa
```

---

## Emergency Procedures

### 15. Service Isolation

If a microservice is causing issues, disable it without affecting the core:

```bash
# Scale down a problematic service
kubectl scale deployment/todo-chatbot-notification --replicas=0

# Re-enable
kubectl scale deployment/todo-chatbot-notification --replicas=1
```

### 16. Circuit Break Event Publishing

If event publishing is causing cascading failures:

```bash
# Check event publisher fallback queue
curl http://localhost:8000/api/health/ready  # Shows Dapr status

# Restart Dapr sidecar (kills sidecar, K8s recreates)
kubectl delete pod -l app.kubernetes.io/component=backend
```

### 17. Database Migration Rollback

```bash
# Check current migration
cd backend
uv run alembic current

# Rollback one migration
uv run alembic downgrade -1

# Rollback to specific revision
uv run alembic downgrade <revision>
```

---

## Scheduled Maintenance

| Task | Frequency | Procedure |
|------|-----------|-----------|
| Check pod health | Continuous | K8s probes (automated) |
| Review consumer lag | Daily | `rpk group list` |
| Check Neon DB size | Weekly | Neon dashboard |
| Update container images | Per release | CI/CD pipeline |
| Rotate secrets | Monthly | Update K8s secrets, restart pods |
| Review log volume | Weekly | Check storage usage |
