# Oracle Cloud OKE Setup Guide

Step-by-step guide to deploy the Todo Chatbot on Oracle Cloud OKE (Always Free tier) with Redpanda Serverless.

## Prerequisites

- [OCI CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm) installed
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed
- [Helm 3](https://helm.sh/docs/intro/install/) installed
- [Docker](https://docs.docker.com/get-docker/) installed
- GitHub repository with Actions enabled

## Architecture (All Free Tier)

| Component | Service | Free Tier Limits |
|-----------|---------|-----------------|
| Kubernetes | Oracle OKE | 4 ARM A1 OCPUs, 24GB RAM |
| Pub/Sub | Redpanda Serverless | Free tier |
| Database | Neon PostgreSQL | Already configured |
| Registry | Oracle OCIR | Included with OCI |
| Redis | Self-hosted on OKE | Runs in-cluster |
| Load Balancer | OCI Flexible LB | 1 free |
| Block Storage | OCI Block Volume | 200GB free |

## Step 1: Create Oracle Cloud Account

1. Sign up at [cloud.oracle.com](https://cloud.oracle.com) for an Always Free account
2. Note your **tenancy name** and **home region** (e.g., `us-phoenix-1`)
3. Navigate to **Identity & Security > Compartments** and note your compartment OCID

## Step 2: Generate API Key

1. Go to **Profile > My Profile > API Keys**
2. Click **Add API Key** > **Generate API Key Pair**
3. Download the private key (`.pem` file)
4. Note the **fingerprint** displayed after adding the key
5. Note your **user OCID** from the profile page
6. Note your **tenancy OCID** from **Administration > Tenancy Details**

## Step 3: Create OKE Cluster

1. Navigate to **Developer Services > Kubernetes Clusters (OKE)**
2. Click **Create Cluster** > **Quick Create**
3. Configure:
   - **Name**: `todo-chatbot-cluster`
   - **Kubernetes Version**: Latest stable (e.g., 1.30)
   - **Shape**: `VM.Standard.A1.Flex` (ARM - Always Free)
   - **OCPUs per node**: 1
   - **Memory per node**: 6 GB
   - **Number of nodes**: 4 (uses all 4 free ARM OCPUs)
   - **Networking**: Public endpoint, private workers (default)
4. Click **Create Cluster** and wait for it to become Active (~10 minutes)
5. Note the **Cluster OCID** from the cluster details page

## Step 4: Configure kubectl

```bash
# Install OCI CLI and configure
oci setup config

# Get kubeconfig for your cluster
oci ce cluster create-kubeconfig \
  --cluster-id <CLUSTER_OCID> \
  --file $HOME/.kube/config \
  --region <REGION> \
  --token-version 2.0.0 \
  --kube-endpoint PUBLIC_ENDPOINT

# Verify connection
kubectl get nodes
```

## Step 5: Create OCIR Repository

1. Navigate to **Developer Services > Container Registry**
2. Note your **Object Storage Namespace** (shown at the top, also called tenancy namespace)
3. Create repositories for each image:
   - `todo-backend`
   - `todo-frontend`
   - `websocket-service`
   - `recurring-task-service`
   - `notification-service`

### Generate Auth Token for OCIR

1. Go to **Profile > My Profile > Auth Tokens**
2. Click **Generate Token**
3. Save the token (shown only once)

### OCIR Login Format

```bash
# Login format: <region-key>.ocir.io
# Username format: <namespace>/<username>
docker login <region>.ocir.io \
  -u '<namespace>/<username>' \
  -p '<auth-token>'

# Example:
docker login phx.ocir.io \
  -u 'mytenancy/oracleidentitycloudservice/user@email.com' \
  -p 'myauthtoken'
```

## Step 6: Create Redpanda Serverless Cluster

1. Sign up at [redpanda.com](https://redpanda.com) (free tier)
2. Create a **Serverless** cluster
3. Create topics:
   - `task-events`
   - `notification-events`
   - `recurring-task-events`
4. Create a **SCRAM user** with produce/consume permissions
5. Note:
   - **Bootstrap server URL** (e.g., `seed-xxxxx.redpanda.com:9092`)
   - **SASL username**
   - **SASL password**

## Step 7: Install Cluster Prerequisites

### Install Dapr

```bash
# Install Dapr CLI
curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | bash

# Initialize Dapr on the cluster
dapr init -k --runtime-version 1.14.4

# Verify
dapr status -k
```

### Install NGINX Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.service.annotations."oci\.oraclecloud\.com/load-balancer-type"=nlb \
  --set controller.service.annotations."oci-network-load-balancer\.oraclecloud\.com/is-preserve-source"=true
```

### Install cert-manager (optional, for TLS)

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update

helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set crds.enabled=true
```

## Step 8: Create Kubernetes Secrets

```bash
# Create production namespace
kubectl create namespace production

# OCIR image pull secret
kubectl create secret docker-registry ocir-secret \
  --namespace production \
  --docker-server=<region>.ocir.io \
  --docker-username='<namespace>/<username>' \
  --docker-password='<auth-token>' \
  --docker-email='<email>'

# Application secrets
kubectl create secret generic todo-chatbot-secrets \
  --namespace production \
  --from-literal=DATABASE_URL='<neon-postgresql-url>' \
  --from-literal=BETTER_AUTH_SECRET='<auth-secret>' \
  --from-literal=OPENAI_API_KEY='<openai-key>'

# Redpanda credentials (for Dapr pubsub)
kubectl create secret generic redpanda-credentials \
  --namespace production \
  --from-literal=brokers='<redpanda-bootstrap-url>' \
  --from-literal=saslUsername='<redpanda-username>' \
  --from-literal=saslPassword='<redpanda-password>'
```

## Step 9: Configure GitHub Secrets

Go to your repository **Settings > Secrets and variables > Actions** and add:

| Secret | Description | Example |
|--------|-------------|---------|
| `OCI_CLI_USER` | User OCID | `ocid1.user.oc1..aaaa...` |
| `OCI_CLI_TENANCY` | Tenancy OCID | `ocid1.tenancy.oc1..aaaa...` |
| `OCI_CLI_FINGERPRINT` | API key fingerprint | `aa:bb:cc:dd:...` |
| `OCI_CLI_KEY_CONTENT` | Private key (base64) | `base64 -w0 < oci_api_key.pem` |
| `OCI_CLI_REGION` | OCI region | `us-phoenix-1` |
| `OKE_CLUSTER_OCID` | Cluster OCID | `ocid1.cluster.oc1...` |
| `OCIR_NAMESPACE` | Tenancy namespace | `mytenancy` |
| `OCIR_USERNAME` | OCIR username | `mytenancy/user@email.com` |
| `OCIR_TOKEN` | Auth token | Generated in Step 5 |
| `DATABASE_URL` | Neon PostgreSQL URL | `postgresql://...` |
| `BETTER_AUTH_SECRET` | Auth secret | 32+ char string |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `REDPANDA_BROKERS` | Bootstrap URL | `seed-xxx.redpanda.com:9092` |
| `REDPANDA_USERNAME` | SASL username | From Step 6 |
| `REDPANDA_PASSWORD` | SASL password | From Step 6 |

## Step 10: Deploy

### Option A: GitHub Actions (Recommended)

Push to `main` branch to trigger the `deploy-oke.yaml` workflow:

```bash
git push origin main
```

### Option B: Manual Deployment

```bash
# Build and push images (example for backend)
docker build -t <region>.ocir.io/<namespace>/todo-backend:latest ./backend
docker push <region>.ocir.io/<namespace>/todo-backend:latest

# Deploy with Helm
helm upgrade --install todo-chatbot ./helm/todo-chatbot \
  --namespace production \
  --values ./helm/values-oke.yaml \
  --set global.imageTag=latest \
  --set global.registry=<region>.ocir.io/<namespace> \
  --set secrets.databaseUrl='<db-url>' \
  --set secrets.betterAuthSecret='<auth-secret>' \
  --set secrets.openaiApiKey='<openai-key>' \
  --wait --timeout 10m
```

## Step 11: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n production

# Check services
kubectl get svc -n production

# Get the LoadBalancer IP
kubectl get svc -n ingress-nginx

# Test health endpoints
curl http://<LOAD_BALANCER_IP>/api/health
curl http://<LOAD_BALANCER_IP>/
```

## Troubleshooting

### Pods stuck in ImagePullBackOff

```bash
# Verify OCIR secret exists
kubectl get secret ocir-secret -n production

# Check image pull secret is correct
kubectl describe pod <pod-name> -n production

# Re-create OCIR secret if needed
kubectl delete secret ocir-secret -n production
kubectl create secret docker-registry ocir-secret ...
```

### ARM Compatibility Issues

OKE free tier uses ARM A1 nodes. Ensure all Docker images are built for `linux/arm64`:

```bash
docker buildx build --platform linux/arm64 -t <image> .
```

### OCI Load Balancer Not Provisioning

```bash
# Check OCI LB service events
kubectl describe svc ingress-nginx-controller -n ingress-nginx

# Verify you haven't exceeded the free tier LB limit (1)
# Check OCI Console > Networking > Load Balancers
```

### Dapr Sidecar Not Injecting

```bash
# Verify Dapr is installed
dapr status -k

# Check annotations on deployment
kubectl get deployment <name> -n production -o yaml | grep dapr

# Check Dapr component status
kubectl get components -n production
```

## Resource Budget

| Service | CPU Request | Memory Request | Replicas |
|---------|-----------|---------------|----------|
| Frontend | 50m | 128Mi | 1 |
| Backend | 100m | 256Mi | 1 |
| WebSocket | 50m | 128Mi | 1 |
| Recurring Task | 50m | 128Mi | 1 |
| Notification | 50m | 128Mi | 1 |
| Redis | 50m | 128Mi | 1 |
| **Total** | **350m** | **896Mi** | **6** |

Free tier: 4 OCPUs (4000m), 24GB RAM — well within limits.
