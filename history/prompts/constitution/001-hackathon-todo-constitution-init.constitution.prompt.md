---
id: 001
title: Hackathon Todo Constitution Init
stage: constitution
date: 2026-01-01
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: master
user: unknown
command: /sp.constitution
labels: ["constitution", "init", "hackathon", "sdd"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - null
---

## Prompt

Generate an sp.constitution file for the following project.

Project Name:
Hackathon II – Evolution of Todo (Phases I–V)

Mission:
Build a cloud-native, AI-powered Todo system using Spec-Driven Development, evolving from a console app to a Kubernetes-deployed distributed system.

Core Principles:
- Spec-Driven Only: No manual code writing. All code must be generated via Claude Code from Markdown specs.
- Clean Architecture: Strict separation of frontend (Next.js), backend (FastAPI), and AI agents (MCP).
- Accuracy: Implementations must exactly follow Acceptance Criteria in /specs.
- Reproducibility: System must be containerized and deployable with Helm.

Technology Standards:
- Backend: Python 3.13+, FastAPI, SQLModel
- Database: Neon Serverless PostgreSQL
- Frontend: Next.js 16+ with Tailwind CSS
- Auth: Better Auth with JWT
- AI: OpenAI Agents SDK + Official MCP SDK
- Infra: Docker, Minikube, Helm, Kubernetes

Operational Rules:
- All database queries must be scoped by user_id from JWT.
- Chatbot and MCP tools must be stateless; all state stored in the database.
- Use monorepo structure: /specs, /frontend, /backend.

Phase 1: CLI Todo App
Goal: Build the foundation using a command-line interface.
•	Todo app runs in the terminal
•	Add, list, update, and delete todos
•	Uses prompts/flags for user input
•	Local storage (file or memory-based)
•	Focus on logic, not UI
________________________________________
Phase 2: Web-based Todo App
Goal: Move from CLI to browser.
•	Frontend UI (HTML/CSS/TypeScript or React/Next.js)
•	Backend API for todo operations
•	Todos created and managed via web interface
•	Backend handles persistence (DB or file)
•	Clear separation of frontend & backend
👉 This phase introduces client–server architecture.
________________________________________
Phase 3: ChatKit Integration
Goal: Enable conversational task management.
•	Integrate OpenAI ChatKit into the app
•	Users create/manage todos via chat
•	Chat responses trigger todo actions
•	Structured data extraction (title, description, priority, etc.)
•	Backend processes ChatKit outputs
👉 This phase turns  app into a conversational agent.
________________________________________
Phase 4: Minikube & Kubernetes Deployment
Goal: Run the system in a local cloud-native environment.
•	Dockerize frontend and backend
•	Create Kubernetes manifests (Deployment, Service)
•	Run the app on Minikube
•	Expose services using NodePort / minikube service
•	Validate inter-service communication
👉 This phase introduces cloud-native fundamentals.
________________________________________
Phase 5: Production-Ready Architecture
Goal: Prepare for real-world usage.
•	Improve security and configs
•	Environment variables & secrets
•	Scalability considerations
•	Optional cloud deployment
•	Documentation & architecture clarity
👉 This phase completes the end-to-end journey.
________________________________________
Simple Flow
CLI → Web App → ChatKit → Minikube → Production


Success Criteria:
- All 5 hackathon phases completed
- 100% code generated via specs
- Phase V deployed on DigitalOcean Kubernetes (DOKS)

Output:
Produce a concise Markdown sp.constitution with clear sections and enforceable rules.

## Response snapshot

Created constitution v1.0.0 at `.specify/memory/constitution.md` with:
- 4 Core Principles: Spec-Driven Only, Clean Architecture, Accuracy, Reproducibility
- Technology Standards table covering full stack (Python 3.13+, FastAPI, SQLModel, Neon PostgreSQL, Next.js 16+, Tailwind, Better Auth, OpenAI Agents SDK, MCP SDK, Docker, Minikube, Helm, Kubernetes)
- Operational Rules for database security (user_id scoping), stateless AI, and monorepo structure
- Governance section with amendment process, semantic versioning policy, and compliance review

## Outcome

- ✅ Impact: Initial constitution ratified for Hackathon II project
- 🧪 Tests: N/A (constitution document, not code)
- 📁 Files: 1 file created/modified (.specify/memory/constitution.md)
- 🔁 Next prompts: Create feature specs for Phase I, run /sp.specify for first feature
- 🧠 Reflection: Constitution maps user requirements directly to enforceable rules; technology table provides clear reference for all implementations

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate constitution alignment during first /sp.plan execution
