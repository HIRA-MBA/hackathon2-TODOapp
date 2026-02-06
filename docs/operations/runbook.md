# Operational Runbook - Todo Chatbot (Phase V)

This runbook provides operational procedures for managing the Todo Chatbot application on DigitalOcean Kubernetes Service (DOKS).

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Health Checks](#health-checks)
3. [Common Operations](#common-operations)
4. [Troubleshooting](#troubleshooting)
5. [Incident Response](#incident-response)
6. [Monitoring](#monitoring)

---

## Architecture Overview

### Services

| Service | Port | Description |
|---------|------|-------------|
| backend | 8000 | FastAPI main API server |
| frontend | 3000 | Next.js web application |
| websocket | 8001 | WebSocket real-time sync |
| recurring-task | 8002 | Recurring task automation |
| notification | 8003 | Notification delivery |

### Dependencies

- **PostgreSQL**: Neon serverless (external)
- **Redis**: DigitalOcean Managed Redis (state store)
- **Redpanda/Kafka**: DigitalOcean Managed Kafka (pub/sub)
- **Dapr**: Sidecar for service mesh

### Topics

| Topic | Publishers | Consumers |
|-------|------------|-----------|
| task-events | backend | recurring-task, websocket |
| task-updates | backend | websocket |
| reminders | backend | notification |

---

## Health Checks

### Check All Pods Status

```bash
kubectl get pods -n todo-chatbot
```

Expected: All pods should be `Running` with `READY` status matching container count.

### Check Individual Service Health

```bash
# Backend
kubectl exec -it deploy/todo-chatbot-backend -n todo-chatbot -- curl localhost:8000/health

# WebSocket
kubectl exec -it deploy/todo-chatbot-websocket -n todo-chatbot -- curl localhost:8001/health

# Recurring Task
kubectl exec -it deploy/todo-chatbot-recurring-task -n todo-chatbot -- curl localhost:8002/health

# Notification
kubectl exec -it deploy/todo-chatbot-notification -n todo-chatbot -- curl localhost:8003/health
```

### Check Dapr Sidecar Health

```bash
# View Dapr dashboard (port-forward)
kubectl port-forward svc/dapr-dashboard -n dapr-system 8080:8080

# Or check via CLI
dapr dashboard -k -n todo-chatbot
```

### Check Readiness Probes

```bash
# Check if services are ready to accept traffic
kubectl get endpoints -n todo-chatbot
```

---

## Common Operations

### View Logs

```bash
# Backend logs
kubectl logs -f deploy/todo-chatbot-backend -n todo-chatbot

# WebSocket logs (with Dapr sidecar)
kubectl logs -f deploy/todo-chatbot-websocket -n todo-chatbot -c websocket

# Dapr sidecar logs
kubectl logs -f deploy/todo-chatbot-backend -n todo-chatbot -c daprd
```

### View Structured Logs (JSON)

```bash
# Parse JSON logs with jq
kubectl logs deploy/todo-chatbot-backend -n todo-chatbot | jq '.'

# Filter by log level
kubectl logs deploy/todo-chatbot-backend -n todo-chatbot | jq 'select(.level == "ERROR")'

# Filter by correlation ID
kubectl logs deploy/todo-chatbot-backend -n todo-chatbot | jq 'select(.correlation_id == "abc123")'
```

### Scale Services

```bash
# Scale WebSocket for more connections
kubectl scale deploy/todo-chatbot-websocket -n todo-chatbot --replicas=3

# Scale via Helm
helm upgrade todo-chatbot ./helm/todo-chatbot \
  --set websocket.replicaCount=3 \
  -n todo-chatbot
```

### Rolling Restart

```bash
# Restart backend (triggers rolling update)
kubectl rollout restart deploy/todo-chatbot-backend -n todo-chatbot

# Check rollout status
kubectl rollout status deploy/todo-chatbot-backend -n todo-chatbot
```

### Rollback Deployment

```bash
# View rollout history
kubectl rollout history deploy/todo-chatbot-backend -n todo-chatbot

# Rollback to previous version
kubectl rollout undo deploy/todo-chatbot-backend -n todo-chatbot

# Rollback to specific revision
kubectl rollout undo deploy/todo-chatbot-backend -n todo-chatbot --to-revision=2
```

---

## Troubleshooting

### Pod Not Starting

1. Check pod events:
   ```bash
   kubectl describe pod <pod-name> -n todo-chatbot
   ```

2. Common issues:
   - **ImagePullBackOff**: Check image registry credentials
   - **CrashLoopBackOff**: Check container logs
   - **Pending**: Check node resources or PVC status

### Dapr Sidecar Issues

1. Check Dapr status:
   ```bash
   kubectl get pods -n todo-chatbot -o wide
   # Look for 2/2 Ready (app + sidecar)
   ```

2. Check Dapr components:
   ```bash
   kubectl get components -n todo-chatbot
   ```

3. Check Dapr subscriptions:
   ```bash
   kubectl get subscriptions -n todo-chatbot
   ```

4. Verify pub/sub connectivity:
   ```bash
   kubectl exec -it deploy/todo-chatbot-backend -n todo-chatbot -c daprd -- \
     wget -qO- http://localhost:3500/v1.0/metadata
   ```

### WebSocket Connection Issues

1. Check WebSocket stats:
   ```bash
   kubectl exec -it deploy/todo-chatbot-websocket -n todo-chatbot -- curl localhost:8001/stats
   ```

2. Check for connection limits:
   ```bash
   kubectl top pod -n todo-chatbot | grep websocket
   ```

3. Verify JWT authentication:
   - Check `JWT_SECRET` environment variable matches `BETTER_AUTH_SECRET`

### Database Connection Issues

1. Test database connectivity:
   ```bash
   kubectl exec -it deploy/todo-chatbot-backend -n todo-chatbot -- \
     python -c "from app.database import engine; print('Connected!')"
   ```

2. Check secrets:
   ```bash
   kubectl get secret todo-chatbot-secrets -n todo-chatbot -o yaml
   ```

### Event Publishing Failures

1. Check Redpanda/Kafka connectivity:
   ```bash
   # From backend pod
   kubectl exec -it deploy/todo-chatbot-backend -n todo-chatbot -c daprd -- \
     wget -qO- http://localhost:3500/v1.0/healthz
   ```

2. Check topic exists:
   ```bash
   rpk topic list --brokers <broker-url> --tls-enabled --sasl-mechanism SCRAM-SHA-256
   ```

3. Monitor failed publishes in logs:
   ```bash
   kubectl logs deploy/todo-chatbot-backend -n todo-chatbot | grep -i "publish.*fail"
   ```

---

## Incident Response

### High Error Rate

1. Check error logs:
   ```bash
   kubectl logs deploy/todo-chatbot-backend -n todo-chatbot --since=5m | jq 'select(.level == "ERROR")'
   ```

2. Check external dependencies:
   - Neon dashboard for database status
   - DigitalOcean dashboard for Kafka/Redis status

3. Scale up if needed:
   ```bash
   kubectl scale deploy/todo-chatbot-backend -n todo-chatbot --replicas=3
   ```

### WebSocket Disconnections

1. Check connection count:
   ```bash
   kubectl exec -it deploy/todo-chatbot-websocket -n todo-chatbot -- curl localhost:8001/stats
   ```

2. Check for OOM kills:
   ```bash
   kubectl describe pod -l app.kubernetes.io/component=websocket -n todo-chatbot | grep -A5 "State:"
   ```

3. Increase resources if needed:
   ```bash
   helm upgrade todo-chatbot ./helm/todo-chatbot \
     --set websocket.resources.limits.memory=512Mi \
     -n todo-chatbot
   ```

### Message Processing Delays

1. Check consumer lag:
   ```bash
   rpk group describe recurring-task-service --brokers <broker-url>
   ```

2. Scale consumers:
   ```bash
   kubectl scale deploy/todo-chatbot-recurring-task -n todo-chatbot --replicas=2
   ```

3. Check for processing errors:
   ```bash
   kubectl logs deploy/todo-chatbot-recurring-task -n todo-chatbot | grep -i error
   ```

### Complete Outage

1. Check all pods:
   ```bash
   kubectl get pods -n todo-chatbot
   ```

2. Check node status:
   ```bash
   kubectl get nodes
   kubectl describe node <node-name>
   ```

3. Check recent events:
   ```bash
   kubectl get events -n todo-chatbot --sort-by='.lastTimestamp'
   ```

4. Emergency rollback:
   ```bash
   helm rollback todo-chatbot -n todo-chatbot
   ```

---

## Monitoring

### Key Metrics

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Pod restart count | > 3/hour | > 10/hour | Check logs, scale |
| API latency p95 | > 500ms | > 2s | Scale, check DB |
| WebSocket connections | > 400 | > 480 | Scale websocket |
| Kafka consumer lag | > 100 | > 1000 | Scale consumers |
| Error rate | > 1% | > 5% | Check logs, rollback |

### Prometheus Queries (if configured)

```promql
# Request rate
rate(http_requests_total{namespace="todo-chatbot"}[5m])

# Error rate
sum(rate(http_requests_total{namespace="todo-chatbot",status=~"5.."}[5m]))
/ sum(rate(http_requests_total{namespace="todo-chatbot"}[5m]))

# Latency p95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{namespace="todo-chatbot"}[5m]))

# WebSocket connections
websocket_active_connections{namespace="todo-chatbot"}
```

### Dapr Dashboard

Access Dapr dashboard for service mesh visibility:

```bash
kubectl port-forward svc/dapr-dashboard -n dapr-system 8080:8080
```

Dashboard shows:
- Component health (pub/sub, state store)
- Service invocation metrics
- Pub/sub message flow

---

## Maintenance Windows

### Before Maintenance

1. Notify users via status page
2. Scale up services for buffer
3. Ensure recent backup exists

### During Maintenance

1. Apply changes via Helm
2. Monitor rollout status
3. Verify health checks pass

### After Maintenance

1. Run smoke tests
2. Monitor error rates for 15 minutes
3. Update status page

---

## Contact

- **On-call**: Check PagerDuty rotation
- **Escalation**: Platform team Slack channel
- **External**: DigitalOcean support (for managed services)

---

## Appendix

### Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| DATABASE_URL | backend, recurring-task, notification | Neon PostgreSQL connection |
| BETTER_AUTH_SECRET | backend, frontend, websocket | JWT signing secret |
| DAPR_HTTP_PORT | all services | Dapr sidecar port (3500) |
| BACKEND_URL | frontend, recurring-task, notification | Internal backend URL |

### Useful Commands

```bash
# Get all resources
kubectl get all -n todo-chatbot

# Watch pods
kubectl get pods -n todo-chatbot -w

# Port forward for local access
kubectl port-forward svc/todo-chatbot-frontend -n todo-chatbot 3000:3000

# Execute shell in pod
kubectl exec -it deploy/todo-chatbot-backend -n todo-chatbot -- /bin/sh

# Copy files from pod
kubectl cp todo-chatbot/todo-chatbot-backend-xxx:/app/logs ./local-logs
```
