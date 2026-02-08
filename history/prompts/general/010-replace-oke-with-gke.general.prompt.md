---
id: 010
title: Replace Oracle Cloud OKE with Google Cloud GKE
stage: general
date: 2026-02-07
surface: agent
model: claude-opus-4-6
feature: none
branch: main
user: human
command: implement plan
labels: ["gke", "oke", "cloud-migration", "helm", "github-actions"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - helm/values-gke.yaml
  - .github/workflows/deploy-gke.yaml
  - helm/values-oke.yaml (deleted)
  - .github/workflows/deploy-oke.yaml (deleted)
tests:
  - helm lint ./helm/todo-chatbot -f helm/values-gke.yaml (PASS)
  - helm template todo-chatbot ./helm/todo-chatbot -f helm/values-gke.yaml (PASS)
---

## Prompt

Implement the following plan:

# Plan: Replace Oracle Cloud OKE with Google Cloud GKE

## Context
The project currently has Oracle Cloud OKE deployment files (`deploy-oke.yaml` workflow + `values-oke.yaml`). The user uses Google Cloud instead of Oracle Cloud, so we need to replace OKE with GKE across the board.

## Files to Modify/Replace

### 1. Delete `helm/values-oke.yaml` → Create `helm/values-gke.yaml`
Key changes from OKE → GKE:
- `global.registry`: `REGION-docker.pkg.dev/PROJECT_ID/REPO_NAME` (Google Artifact Registry)
- `global.imagePullSecrets`: `gar-secret` (instead of `ocir-secret`)
- `redis.persistence.storageClass`: `standard-rwo` (GKE default, replaces `oci-bv`)
- Keep same replica counts, resource limits, Dapr config, ingress pattern
- All else remains identical to OKE values structure

### 2. Delete `.github/workflows/deploy-oke.yaml` → Create `.github/workflows/deploy-gke.yaml`
Key changes:
- **Auth**: Use `google-github-actions/auth@v2` with Workload Identity Federation
- **CLI**: Use `google-github-actions/setup-gcloud@v2` for gcloud
- **Kubeconfig**: Use `google-github-actions/get-gke-credentials@v2`
- **Registry**: Login to Google Artifact Registry via `gcloud auth configure-docker`
- **Build**: `linux/amd64` platform (no ARM/QEMU needed unlike OKE A1)
- **Image tags**: `GAR_LOCATION-docker.pkg.dev/GCP_PROJECT_ID/REPO_NAME/image:tag`
- **Secrets**: Replace OCI_* secrets with GCP_* secrets
- **Deploy**: Same Helm upgrade pattern with `values-gke.yaml`

## Response snapshot

Created `helm/values-gke.yaml` with GKE-adapted values (Artifact Registry, gar-secret, standard-rwo storageClass). Created `.github/workflows/deploy-gke.yaml` with full GCP auth pipeline using google-github-actions, amd64 builds, and Artifact Registry. Deleted both OKE files. Verified with helm lint (0 failures) and helm template (all GKE values render correctly).

## Outcome

- ✅ Impact: Migrated cloud deployment target from Oracle Cloud OKE to Google Cloud GKE
- 🧪 Tests: helm lint PASS, helm template PASS — all GKE-specific values render correctly
- 📁 Files: 2 created (values-gke.yaml, deploy-gke.yaml), 2 deleted (values-oke.yaml, deploy-oke.yaml)
- 🔁 Next prompts: Configure GitHub secrets (GCP_PROJECT_ID, GCP_SA_KEY, GKE_CLUSTER_NAME, GKE_CLUSTER_ZONE, GAR_LOCATION), test full CI/CD pipeline
- 🧠 Reflection: Straightforward 1:1 replacement. Key differences are auth mechanism (SA key vs OCI API key), registry format (docker.pkg.dev vs ocir.io), platform (amd64 vs arm64), and storage class (standard-rwo vs oci-bv).

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): helm lint PASS, helm template PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
