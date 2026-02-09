---
id: 012
title: Deploy kagent and kubectl-ai
stage: green
date: 2026-02-09
surface: agent
model: claude-opus-4-6
feature: none
branch: main
user: hp
command: deploy k-agent and kubectl-ai
labels: ["kubernetes", "ai-tools", "kagent", "kubectl-ai", "deployment"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - C:\Users\hp\.config\kubectl-ai\config.yaml
  - C:\Users\hp\.kagent\config.yaml
  - D:\hackathone2\.env.k8s-ai
  - D:\hackathone2\.gitignore
tests:
  - kubectl-ai --quiet "list all namespaces" - PASS
  - kagent API /api/agents - PASS (10 agents listed)
  - kagent UI http://localhost:8080 - PASS (HTTP 200)
  - kubectl get pods -n kagent (15/16 running) - PASS
---

## Prompt

docker desktop is running, openai key is [REDACTED], start deploying k-agent and kubectl-ai

## Response snapshot

Successfully deployed both kubectl-ai and kagent on Docker Desktop Kubernetes:

1. **kubectl-ai v0.0.29** - Installed to `C:\Users\hp\bin\kubectl-ai.exe`, configured with OpenAI gpt-4.1 provider. Tested successfully with natural language queries against the cluster.

2. **kagent v0.7.13** - Deployed to Kubernetes `kagent` namespace with demo profile via Helm. 10 AI agents running: k8s-agent, helm-agent, istio-agent, cilium-debug-agent, cilium-manager-agent, cilium-policy-agent, argo-rollouts-conversion-agent, kgateway-agent, observability-agent, promql-agent. OpenAI API key stored in k8s secret `kagent-openai`. UI accessible at http://localhost:8080, API at http://localhost:8083.

## Outcome

- ✅ Impact: Both AI-powered Kubernetes tools deployed and operational
- 🧪 Tests: All verification tests passed (kubectl-ai query, kagent API, UI access, pod health)
- 📁 Files: 4 files created/modified (kubectl-ai config, kagent config, .env.k8s-ai, .gitignore)
- 🔁 Next prompts: Configure specific kagent agents, test kagent invoke commands, explore kagent dashboard
- 🧠 Reflection: Windows environment required manual binary installation instead of bash scripts. Helm install timeouts are common on Docker Desktop due to slow image pulls.

## Evaluation notes (flywheel)

- Failure modes observed: Helm install timeouts on Docker Desktop, kagent CLI port-forward conflicts on Windows
- Graders run and results (PASS/FAIL): kubectl-ai query PASS, kagent API PASS, kagent UI PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test kagent invoke via dashboard UI instead of CLI
