# AI DevOps Tools Guide

This guide covers AI-assisted Kubernetes operations using kubectl-ai and kagent.

## Overview

AI DevOps tools allow you to interact with your Kubernetes cluster using natural language instead of memorizing kubectl commands.

| Tool | Purpose | Installation |
|------|---------|--------------|
| kubectl-ai | Natural language kubectl commands | Go-based CLI |
| kagent | Cluster analysis and diagnostics | (Platform-specific) |
| Docker Gordon | Docker/container assistance | Built into Docker Desktop |

## kubectl-ai

### Installation

```powershell
# Requires Go 1.21+
go install github.com/sozercan/kubectl-ai@latest
```

### Configuration

Set your OpenAI API key:

```powershell
# PowerShell (current session)
$env:OPENAI_API_KEY = "sk-your-key-here"

# PowerShell (permanent)
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-your-key-here", "User")
```

### Usage Examples

#### Cluster Queries

```powershell
# Show all pods
kubectl-ai "show all running pods"

# Get detailed pod info
kubectl-ai "describe the backend pod"

# Check service endpoints
kubectl-ai "what services are exposing port 8000?"

# View resource usage
kubectl-ai "show CPU and memory usage for all pods"
```

#### Deployment Operations

```powershell
# Scale deployments
kubectl-ai "scale the backend deployment to 2 replicas"

# Restart pods
kubectl-ai "restart all pods in the frontend deployment"

# Check rollout status
kubectl-ai "show rollout status for backend"
```

#### Debugging

```powershell
# Diagnose failures
kubectl-ai "why is the backend pod in CrashLoopBackOff?"

# View recent logs
kubectl-ai "show me the last 50 log lines from the backend"

# Check connectivity
kubectl-ai "can the frontend pod reach the backend service?"

# Analyze events
kubectl-ai "show recent warning events in the cluster"
```

#### Configuration

```powershell
# View environment variables
kubectl-ai "show environment variables for the backend pod"

# Check secrets (keys only)
kubectl-ai "what secrets are mounted in the frontend pod?"

# Compare configs
kubectl-ai "compare config between frontend and backend deployments"
```

### Advanced Queries

```powershell
# Resource optimization
kubectl-ai "which pods are using more than 80% of their memory limit?"

# Network debugging
kubectl-ai "trace the network path from frontend to backend"

# Performance analysis
kubectl-ai "show slow API responses in backend logs"
```

## kagent (if available)

### Installation

Check if kagent is available for Windows:

```powershell
# Installation varies by platform
# Visit: https://github.com/kagent-ai/kagent
```

### Usage Examples

```powershell
# Cluster health check
kagent health check

# Analyze cluster state
kagent analyze cluster

# Diagnose specific pod
kagent diagnose pod todo-todo-chatbot-backend-xxx

# Get optimization suggestions
kagent suggest optimizations

# Explain errors
kagent explain error "ImagePullBackOff"
```

## Docker Desktop Gordon (AI)

If Docker Desktop's AI agent is enabled:

```powershell
# Dockerfile help
docker ai "create a Dockerfile for a Next.js app with pnpm"

# Optimize images
docker ai "how can I make my todo-backend image smaller?"

# Debug containers
docker ai "why is my container failing to start?"

# Best practices
docker ai "review my Dockerfile for security issues"
```

## Common AI DevOps Workflows

### 1. Initial Deployment Verification

```powershell
# After helm install
kubectl-ai "show status of all pods and their readiness"
kubectl-ai "are there any pods with errors or warnings?"
kubectl-ai "check if backend can connect to the database"
```

### 2. Troubleshooting Failed Deployments

```powershell
# Find the problem
kubectl-ai "why is the deployment failing?"
kubectl-ai "show recent events with errors"

# Get more details
kubectl-ai "show logs from the crashing container"
kubectl-ai "what resources is the pod requesting vs available?"

# Fix common issues
kubectl-ai "how do I fix an ImagePullBackOff error?"
```

### 3. Performance Monitoring

```powershell
# Current state
kubectl-ai "show resource usage trends for the last hour"
kubectl-ai "which pod is consuming the most CPU?"

# Recommendations
kubectl-ai "should I increase resource limits for backend?"
```

### 4. Scaling Decisions

```powershell
# Analyze load
kubectl-ai "show request rate to the frontend service"
kubectl-ai "are there any pods being throttled?"

# Make changes
kubectl-ai "scale backend based on current load"
```

## Tips and Best Practices

### 1. Be Specific

```powershell
# Less effective
kubectl-ai "check pods"

# More effective
kubectl-ai "show all pods in default namespace with their status and restart counts"
```

### 2. Context Matters

```powershell
# Provide context for better answers
kubectl-ai "the backend is slow - what could be causing this?"
```

### 3. Verify Before Executing

kubectl-ai often generates kubectl commands. Review them before running destructive operations:

```powershell
# kubectl-ai may suggest:
kubectl delete pod backend-xxx

# Always verify the command makes sense before executing
```

### 4. Use for Learning

```powershell
# Learn kubectl commands
kubectl-ai "how would I manually do what you just suggested?"
```

## Limitations

- AI suggestions should be verified before execution
- Complex multi-step operations may require manual refinement
- Real-time metrics require proper observability setup
- Some operations require cluster admin privileges

## Troubleshooting AI Tools

### kubectl-ai Not Working

```powershell
# Check API key
echo $env:OPENAI_API_KEY

# Verify installation
kubectl-ai version

# Test connectivity
kubectl-ai "list namespaces"
```

### Incorrect Suggestions

If kubectl-ai provides incorrect commands:

1. Rephrase your query with more specifics
2. Verify the current cluster context: `kubectl config current-context`
3. Check if the resources exist: `kubectl get all`

## See Also

- [Kubernetes Local Deployment](./kubernetes-local-deployment.md)
- [Troubleshooting Guide](./kubernetes-troubleshooting.md)
