# Phase 0 Research: Advanced Cloud-Native Todo Chatbot (Phase V)

**Branch**: `005-cloud-native-doks` | **Date**: 2026-02-04
**Purpose**: Resolve all technical unknowns before design phase

---

## 1. Dapr Pub/Sub with Redpanda Cloud (SASL_SSL)

**Decision**: Use Dapr's Kafka pub/sub component with SASL_SSL authentication, storing credentials in Kubernetes secrets via `secretKeyRef`.

**Rationale**:
- Redpanda Cloud natively supports SASL over TLS 1.2 for Kafka clients
- Storing passwords in Kubernetes secrets aligns with Dapr's security best practices
- SASL_SSL provides both authentication (SASL) and encryption (TLS) in a single configuration
- Dapr automatically handles credential injection into the component

**Alternatives Considered**:
| Alternative | Rejected Because |
|-------------|------------------|
| mTLS only | More complex certificate management; less common for Redpanda Cloud |
| SASL without TLS | Security risk; Redpanda Cloud requires TLS for SASL |
| API key authentication | Not applicable; Redpanda Cloud uses SASL credentials |

**Key Configuration**:
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: redpanda-pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "${REDPANDA_BOOTSTRAP_SERVERS}"
  - name: authType
    value: "password"
  - name: saslUsername
    secretKeyRef:
      name: redpanda-credentials
      key: username
  - name: saslPassword
    secretKeyRef:
      name: redpanda-credentials
      key: password
  - name: saslMechanism
    value: "SCRAM-SHA-512"
  - name: tls
    value: "true"
  - name: consumerGroup
    value: "${SERVICE_NAME}"
```

---

## 2. WebSocket Scaling on Kubernetes

**Decision**: Implement sticky sessions at the ingress controller level with NGINX Ingress Controller, extended timeouts, connection affinity, and KEDA-based HPA using custom Prometheus metrics.

**Rationale**:
- NGINX Ingress Controller is widely adopted and provides cookie-based session affinity
- Long-lived WebSocket connections require 3600+ second timeouts
- Sticky sessions ensure clients reconnect to the same pod during scaling events
- KEDA custom metrics enable autoscaling based on actual connection count

**Alternatives Considered**:
| Alternative | Rejected Because |
|-------------|------------------|
| Traefik Ingress | Fewer configuration options for fine-tuning |
| HAProxy Ingress | Overkill; higher operational complexity |
| Standard HPA (CPU) | CPU doesn't correlate with WebSocket connection load |

**Key Configuration**:

**Ingress Annotations**:
```yaml
nginx.ingress.kubernetes.io/affinity: cookie
nginx.ingress.kubernetes.io/affinity-mode: persistent
nginx.ingress.kubernetes.io/session-cookie-max-age: "10800"
nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
nginx.ingress.kubernetes.io/proxy-buffering: "off"
```

**KEDA Scaler**:
```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: websocket-scaler
spec:
  scaleTargetRef:
    name: websocket-service
  minReplicaCount: 2
  maxReplicaCount: 10
  triggers:
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      metricName: websocket_active_connections
      query: sum(websocket_active_connections) / count(count(websocket_active_connections) by (pod))
      threshold: "500"
```

---

## 3. GitHub Actions to DigitalOcean DOKS

**Decision**: Use `digitalocean/action-doctl@v2` for authentication, retrieve kubeconfig with temporary credentials, and deploy Helm charts using standard `helm` commands.

**Rationale**:
- Official DigitalOcean GitHub Action handles authentication securely
- Temporary kubeconfig credentials expire, reducing token exposure window
- Standard Helm CLI integration avoids custom wrappers

**Alternatives Considered**:
| Alternative | Rejected Because |
|-------------|------------------|
| doctl-helm-action | Third-party; less official support |
| Manual doctl commands | More verbose; requires explicit kubeconfig management |
| ArgoCD | Adds operational complexity for simple deployments |

**Key Configuration**:
```yaml
name: Deploy to DOKS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: digitalocean/action-doctl@v2
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}

      - name: Get kubeconfig
        run: doctl kubernetes cluster kubeconfig save ${{ secrets.DOKS_CLUSTER_NAME }}

      - uses: azure/setup-helm@v3

      - name: Deploy
        run: |
          helm upgrade --install todo-chatbot ./helm/todo-chatbot \
            --namespace production \
            --create-namespace \
            --values ./helm/values-doks.yaml \
            --set image.tag=${{ github.sha }} \
            --wait --timeout 5m
```

**Required GitHub Secrets**:
- `DIGITALOCEAN_ACCESS_TOKEN` - DigitalOcean API token
- `DOKS_CLUSTER_NAME` - Name of the DOKS cluster
- `DOCR_REGISTRY` - DigitalOcean Container Registry URL

---

## 4. Dapr Secret Store with Kubernetes Secrets

**Decision**: Use Dapr's automatic Kubernetes secret store (named `kubernetes`), which is pre-provisioned on all Kubernetes deployments.

**Rationale**:
- Automatic provisioning requires zero configuration
- Native Kubernetes secret store avoids external dependencies
- Supports secret scoping to restrict component access
- Aligns with Kubernetes security model and RBAC

**Alternatives Considered**:
| Alternative | Rejected Because |
|-------------|------------------|
| Azure Key Vault | Cloud-specific dependency |
| HashiCorp Vault | Requires separate deployment and management |
| AWS Secrets Manager | Cloud-specific; requires IAM configuration |

**Usage in Components**:
```yaml
# No component definition needed - automatically available
# Reference in other components:
- name: redisPassword
  secretKeyRef:
    name: redis-credentials
    key: password
auth:
  secretStore: kubernetes
```

**Application Code Access**:
```python
from dapr.clients import DaprClient

def get_secret(secret_name: str, key: str) -> str:
    with DaprClient() as client:
        secret = client.get_secret(store_name="kubernetes", key=secret_name)
        return secret.get(key)
```

---

## 5. CloudEvents Specification for Task Events

**Decision**: Use CloudEvents v1.0 specification with Dapr's automatic envelope wrapping.

**Rationale**:
- CloudEvents v1.0 is CNCF graduated standard (January 2024)
- Vendor-neutral, consistent event format across distributed systems
- Dapr automatically wraps messages in CloudEvents envelopes
- Enables routing, filtering, and deduplication at event level

**Alternatives Considered**:
| Alternative | Rejected Because |
|-------------|------------------|
| Custom JSON format | No standardization; system coupling |
| Apache Avro | Requires schema registry |
| Protocol Buffers | Binary format; less human-readable |

**Task Event Schema**:
```json
{
  "specversion": "1.0",
  "id": "evt-{uuid}",
  "source": "https://api.todo.example.com/tasks",
  "type": "com.todo.task.{action}",
  "datacontenttype": "application/json",
  "subject": "tasks/{task_id}",
  "time": "2026-02-04T10:30:00Z",
  "data": {
    "taskId": "12345",
    "title": "...",
    "status": "pending|completed|deleted",
    "userId": "user-456",
    "recurrence": { ... }
  }
}
```

**Event Types**:
- `com.todo.task.created` - New task created
- `com.todo.task.updated` - Task modified
- `com.todo.task.deleted` - Task removed
- `com.todo.task.completed` - Task marked done (triggers recurring)

---

## 6. Python dateutil rrule for Recurrence Patterns

**Decision**: Use Python `dateutil.rrule` module for RFC 5545 recurrence pattern implementation.

**Rationale**:
- RFC 5545 compliant implementation
- Fast, caching-enabled recurring date generation
- Handles edge cases (invalid dates like Feb 30) per RFC spec
- `rruleset` enables complex scenarios (exclusions, multiple rules)

**Alternatives Considered**:
| Alternative | Rejected Because |
|-------------|------------------|
| Manual date loop | No recurrence support; custom complexity |
| arrow library | Lacks RFC 5545 compliance |
| pandas date_range | Limited recurrence options |

**Implementation Pattern**:
```python
from dateutil.rrule import rrule, rrulestr, DAILY, WEEKLY, MONTHLY
from datetime import datetime

def get_next_occurrence(pattern: str, completed_date: datetime) -> datetime:
    """Calculate next task occurrence from RFC 5545 pattern"""
    rule = rrulestr(pattern, dtstart=completed_date)
    next_dates = list(rule.between(completed_date, completed_date.replace(year=completed_date.year + 1)))
    return next_dates[1] if len(next_dates) > 1 else None
```

**Supported Patterns**:
- `FREQ=DAILY;COUNT=10` - Daily for 10 occurrences
- `FREQ=WEEKLY;BYDAY=MO,WE,FR` - Every Mon/Wed/Fri
- `FREQ=MONTHLY;BYMONTHDAY=15;UNTIL=20261231` - Monthly on 15th until end of year
- `FREQ=WEEKLY;INTERVAL=2;BYDAY=FR` - Bi-weekly on Friday

**Important Notes**:
- Cannot mix `until` and `count` per RFC 5545 §3.3.10
- Invalid dates (Feb 30) are automatically skipped
- Use timezone-aware datetimes for DST handling

---

## Research Summary

| Topic | Decision | Key Technology |
|-------|----------|----------------|
| Dapr + Redpanda | SASL_SSL via K8s secrets | `pubsub.kafka`, SCRAM-SHA-512 |
| WebSocket Scaling | NGINX sticky sessions + KEDA | Cookie affinity, Prometheus metrics |
| GitHub Actions → DOKS | Official doctl action | `digitalocean/action-doctl@v2` |
| Dapr Secrets | Auto-provisioned K8s store | `secretKeyRef` in components |
| Event Format | CloudEvents v1.0 | Dapr auto-wrapping |
| Recurrence | dateutil.rrule | RFC 5545 compliant |

---

## Sources

1. [Apache Kafka | Dapr Docs](https://docs.dapr.io/reference/components-reference/supported-pubsub/setup-apache-kafka/)
2. [Kubernetes secrets | Dapr Docs](https://docs.dapr.io/reference/components-reference/supported-secret-stores/kubernetes-secret-store/)
3. [How to Deploy Using GitHub Actions | DigitalOcean](https://docs.digitalocean.com/products/kubernetes/how-to/deploy-using-github-actions/)
4. [CloudEvents Specification](https://cloudevents.io/)
5. [Publishing with CloudEvents | Dapr Docs](https://docs.dapr.io/developing-applications/building-blocks/pubsub/pubsub-cloudevents/)
6. [rrule — dateutil documentation](https://dateutil.readthedocs.io/en/stable/rrule.html)
7. [Redpanda Cloud Authentication](https://docs.redpanda.com/redpanda-cloud/security/cloud-authentication/)
8. [KEDA Prometheus Scaler](https://keda.sh/docs/2.17/scalers/prometheus/)
