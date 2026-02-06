---
id: 006
title: Oracle Cloud OKE Infrastructure Setup Implementation
stage: green
date: 2026-02-06
surface: agent
model: claude-opus-4-6
feature: 005-cloud-native-doks
branch: 005-cloud-native-doks
user: human
command: implement
labels: ["oke", "oracle-cloud", "infrastructure", "helm", "ci-cd", "redpanda", "redis"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - docs/operations/oke-setup.md
  - helm/todo-chatbot/templates/redis-deployment.yaml
  - helm/todo-chatbot/templates/redis-service.yaml
  - helm/todo-chatbot/templates/dapr/statestore.yaml
  - helm/todo-chatbot/values.yaml
  - helm/values-oke.yaml
  - .github/workflows/deploy-oke.yaml
tests:
  - helm template todo-chatbot ./helm/todo-chatbot -f helm/values-oke.yaml (validates OKE templates render)
  - helm template todo-chatbot ./helm/todo-chatbot (validates default values still work, no Redis rendered)
  - helm template todo-chatbot ./helm/todo-chatbot -f helm/values-doks.yaml (validates DOKS backward compatibility)
---

## Prompt

Implement the following plan:

# Plan: Oracle Cloud OKE + Redpanda Serverless Infrastructure Setup

The project currently targets DigitalOcean DOKS for production Kubernetes. The user wants to use Oracle Cloud OKE (Always Free tier) and Redpanda Serverless (free tier) to avoid any costs. The Helm templates are already cloud-agnostic; only the CI/CD workflow and values file need OKE-specific versions.

Stack (all free): Oracle Cloud OKE (4 ARM A1 nodes, 24GB RAM, 4 OCPUs), Redpanda Serverless, Neon PostgreSQL, Oracle OCIR, Self-hosted Redis on OKE.

Files to create: deploy-oke.yaml workflow, values-oke.yaml, redis-deployment.yaml, redis-service.yaml, oke-setup.md.
Files to modify: values.yaml (add Redis config), statestore.yaml (support inCluster Redis).

## Response snapshot

Implemented all 7 files as planned:

1. **docs/operations/oke-setup.md** - Comprehensive 11-step setup guide covering OCI account creation, OKE cluster provisioning, OCIR setup, Redpanda Serverless configuration, Dapr/NGINX/cert-manager installation, Kubernetes secrets, GitHub secrets, deployment, and troubleshooting.

2. **helm/todo-chatbot/templates/redis-deployment.yaml** - In-cluster Redis 7 Alpine deployment with health probes, optional PVC for data persistence (uses OCI Block Volume), and conditional rendering via `redis.enabled`.

3. **helm/todo-chatbot/templates/redis-service.yaml** - ClusterIP service for in-cluster Redis, conditionally rendered.

4. **helm/todo-chatbot/templates/dapr/statestore.yaml** - Updated to support `inCluster` mode that auto-resolves Redis host from Helm release name, skipping password and TLS config for in-cluster Redis. Backward compatible with external Redis (DOKS).

5. **helm/todo-chatbot/values.yaml** - Added `redis` configuration block (disabled by default) and `inCluster` flag to statestore config.

6. **helm/values-oke.yaml** - OKE-specific production values with ARM-optimized resource limits (all services at 1 replica), in-cluster Redis enabled with OCI Block Volume persistence, Redpanda Serverless SASL_SSL pubsub, and NGINX ingress.

7. **.github/workflows/deploy-oke.yaml** - CI/CD workflow using oracle-actions for OCI CLI, QEMU for ARM64 cross-compilation, OCIR login, multi-platform image builds, Helm deployment with values-oke.yaml.

All templates verified: OKE renders correctly, default values unchanged, DOKS backward compatible.

## Outcome

- Impact: Full Oracle Cloud OKE deployment infrastructure added alongside existing DOKS support
- Tests: 3 helm template validations passed (OKE, default, DOKS backward compatibility)
- Files: 5 created, 2 modified
- Next prompts: Configure actual OCI secrets, test end-to-end deployment, add TLS with cert-manager
- Reflection: The inCluster Redis approach keeps the statestore template clean with a simple boolean flag while remaining fully backward compatible with external Redis configurations

## Evaluation notes (flywheel)

- Failure modes observed: None - clean implementation
- Graders run and results (PASS/FAIL): helm template validation PASS for all 3 configurations
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add ARM64-specific node affinity/tolerations if OKE cluster has mixed architectures
