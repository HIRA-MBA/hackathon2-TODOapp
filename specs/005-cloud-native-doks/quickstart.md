# Quickstart Guide: Phase V Cloud-Native Development

**Branch**: `005-cloud-native-doks` | **Date**: 2026-02-04

This guide covers local development setup for the event-driven microservices architecture.

---

## Prerequisites

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | Latest | Container runtime |
| Docker Compose | v2+ | Local orchestration |
| Dapr CLI | 1.12+ | Dapr sidecar management |
| Python | 3.13+ | Backend services |
| Node.js | 20+ | Frontend |
| kubectl | Latest | Kubernetes CLI |
| Helm | 3+ | Package management |
| rpk | Latest | Redpanda CLI (topic management) |

### Install Dapr CLI

```bash
# macOS/Linux
curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash

# Windows (PowerShell)
powershell -Command "iwr -useb https://raw.githubusercontent.com/dapr/cli/master/install/install.ps1 | iex"

# Verify installation
dapr --version
```

### Install Redpanda rpk

```bash
# macOS
brew install redpanda-data/tap/redpanda

# Linux
curl -LO https://github.com/redpanda-data/redpanda/releases/latest/download/rpk-linux-amd64.zip
unzip rpk-linux-amd64.zip -d /usr/local/bin/

# Windows
# Download from: https://github.com/redpanda-data/redpanda/releases
```

---

## Environment Setup

### 1. Clone and Setup

```bash
git clone <repository-url>
cd hackathone2
git checkout 005-cloud-native-doks
```

### 2. Environment Variables

Create `.env` file in repository root:

```env
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require

# Redpanda Cloud
REDPANDA_BOOTSTRAP_SERVERS=your-cluster.redpanda.cloud:9092
REDPANDA_USERNAME=your-sasl-username
REDPANDA_PASSWORD=your-sasl-password

# Better Auth
BETTER_AUTH_SECRET=your-auth-secret
BETTER_AUTH_URL=http://localhost:3000

# Service URLs (local development)
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
WEBSOCKET_URL=ws://localhost:8001

# Dapr
DAPR_HTTP_PORT=3500
DAPR_GRPC_PORT=50001
```

### 3. Initialize Dapr

```bash
# Initialize Dapr (first time only)
dapr init

# Verify Dapr is running
dapr --version
docker ps  # Should show dapr_placement, dapr_redis, dapr_zipkin
```

---

## Local Development (Docker Compose)

### Start All Services

```bash
# Start infrastructure (Redpanda, Redis)
docker-compose -f docker-compose.infra.yaml up -d

# Start application services with Dapr sidecars
docker-compose -f docker-compose.yaml up -d
```

### Docker Compose Configuration

Create `docker-compose.infra.yaml`:

```yaml
version: '3.8'
services:
  redpanda:
    image: redpandadata/redpanda:latest
    command:
      - redpanda
      - start
      - --smp=1
      - --memory=1G
      - --overprovisioned
      - --kafka-addr=PLAINTEXT://0.0.0.0:9092
      - --advertise-kafka-addr=PLAINTEXT://redpanda:9092
    ports:
      - "9092:9092"
      - "8081:8081"  # Schema Registry
      - "8082:8082"  # REST Proxy
    healthcheck:
      test: ["CMD", "rpk", "cluster", "health"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

Create `docker-compose.yaml`:

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - DAPR_HTTP_PORT=3500
    ports:
      - "8000:8000"
    depends_on:
      redpanda:
        condition: service_healthy
    networks:
      - dapr-network

  backend-dapr:
    image: daprio/daprd:latest
    command: ["./daprd",
      "-app-id", "backend",
      "-app-port", "8000",
      "-dapr-http-port", "3500",
      "-components-path", "/components"]
    volumes:
      - ./dapr/components:/components
    network_mode: "service:backend"
    depends_on:
      - backend

  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8001
    ports:
      - "3000:3000"
    depends_on:
      - backend

  websocket-service:
    build: ./services/websocket
    environment:
      - DAPR_HTTP_PORT=3500
    ports:
      - "8001:8001"
    networks:
      - dapr-network

  websocket-dapr:
    image: daprio/daprd:latest
    command: ["./daprd",
      "-app-id", "websocket-service",
      "-app-port", "8001",
      "-dapr-http-port", "3500",
      "-components-path", "/components"]
    volumes:
      - ./dapr/components:/components
    network_mode: "service:websocket-service"

  recurring-task-service:
    build: ./services/recurring-task
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - DAPR_HTTP_PORT=3500
    networks:
      - dapr-network

  recurring-task-dapr:
    image: daprio/daprd:latest
    command: ["./daprd",
      "-app-id", "recurring-task-service",
      "-app-port", "8002",
      "-dapr-http-port", "3500",
      "-components-path", "/components"]
    volumes:
      - ./dapr/components:/components
    network_mode: "service:recurring-task-service"

  notification-service:
    build: ./services/notification
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - DAPR_HTTP_PORT=3500
    networks:
      - dapr-network

  notification-dapr:
    image: daprio/daprd:latest
    command: ["./daprd",
      "-app-id", "notification-service",
      "-app-port", "8003",
      "-dapr-http-port", "3500",
      "-components-path", "/components"]
    volumes:
      - ./dapr/components:/components
    network_mode: "service:notification-service"

networks:
  dapr-network:
    driver: bridge
```

---

## Dapr Component Configuration

Create `dapr/components/pubsub.yaml`:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "redpanda:9092"  # Local: use container name
  - name: consumerGroup
    value: "${APP_ID}"
  - name: authType
    value: "none"  # Local dev only; production uses SASL
```

Create `dapr/components/statestore.yaml`:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
  - name: redisHost
    value: "redis:6379"
  - name: redisPassword
    value: ""
```

---

## Running Services Individually (Development Mode)

### Backend Service

```bash
cd backend

# Install dependencies
pip install -e ".[dev]"

# Run with Dapr sidecar
dapr run --app-id backend --app-port 8000 --dapr-http-port 3500 \
  --components-path ../dapr/components -- \
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Microservices

```bash
# Recurring Task Service
cd services/recurring-task
dapr run --app-id recurring-task-service --app-port 8002 \
  --components-path ../../dapr/components -- \
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

# Notification Service
cd services/notification
dapr run --app-id notification-service --app-port 8003 \
  --components-path ../../dapr/components -- \
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8003

# WebSocket Service
cd services/websocket
dapr run --app-id websocket-service --app-port 8001 \
  --components-path ../../dapr/components -- \
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

---

## Verifying the Setup

### 1. Check Dapr Dashboard

```bash
dapr dashboard
# Opens http://localhost:8080
```

### 2. Create Redpanda Topics

```bash
# Local Redpanda
rpk topic create task-events --brokers localhost:9092
rpk topic create task-updates --brokers localhost:9092
rpk topic create reminders --brokers localhost:9092

# List topics
rpk topic list --brokers localhost:9092
```

### 3. Test Event Publishing

```bash
# Publish a test event via Dapr
curl -X POST http://localhost:3500/v1.0/publish/pubsub/task-events \
  -H "Content-Type: application/json" \
  -d '{"taskId": "test-123", "action": "created"}'

# Consume to verify
rpk topic consume task-events --brokers localhost:9092 --num 1
```

### 4. Test WebSocket Connection

```javascript
// Browser console or Node.js
const ws = new WebSocket('ws://localhost:8001?token=YOUR_JWT_TOKEN');
ws.onmessage = (event) => console.log('Received:', event.data);
ws.onopen = () => ws.send(JSON.stringify({ type: 'subscribe', payload: { scopes: ['own_tasks'] } }));
```

---

## Running Tests

### Backend Unit Tests

```bash
cd backend
pytest tests/unit -v
```

### Integration Tests (requires running services)

```bash
cd backend
pytest tests/integration -v --tb=short
```

### Event Flow Tests

```bash
# Verify event publishing
cd backend
pytest tests/integration/test_event_publishing.py -v

# Verify WebSocket delivery
cd services/websocket
pytest tests/integration/test_realtime_sync.py -v
```

---

## Troubleshooting

### Dapr Sidecar Not Connecting

```bash
# Check Dapr logs
dapr logs --app-id backend

# Verify components loaded
curl http://localhost:3500/v1.0/metadata
```

### Events Not Flowing

```bash
# Check topic exists
rpk topic list --brokers localhost:9092

# Check consumer groups
rpk group list --brokers localhost:9092

# View recent messages
rpk topic consume task-events --brokers localhost:9092 --num 10
```

### WebSocket Connection Fails

```bash
# Check service is running
curl http://localhost:8001/health

# Check Dapr subscription
curl http://localhost:3500/v1.0/metadata | jq '.subscriptions'
```

---

## Next Steps

1. **Create topics on Redpanda Cloud** - Use `rpk` with SASL credentials
2. **Update Dapr components for production** - Add SASL_SSL configuration
3. **Deploy to DOKS** - Use Helm charts with `values-doks.yaml`
4. **Configure GitHub Actions** - Set up CI/CD workflow

See [plan.md](./plan.md) for the complete implementation roadmap.
