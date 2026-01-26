# Hackathon II - Evolution of Todo Constitution

## Mission

Build a cloud-native, AI-powered Todo system using Spec-Driven Development, evolving from a console app to a Kubernetes-deployed distributed system.

## Core Principles

### I. Spec-Driven Only (NON-NEGOTIABLE)
No manual code writing. All code MUST be generated via Claude Code from Markdown specs. Every implementation starts with a specification in `/specs`.

### II. Clean Architecture
Strict separation of concerns:
- Frontend: Next.js (UI layer)
- Backend: FastAPI (API layer)
- AI Agents: MCP (intelligence layer)
- Database: PostgreSQL (persistence layer)

### III. Accuracy
Implementations MUST exactly follow Acceptance Criteria defined in `/specs`. No deviations without spec amendment.

### IV. Reproducibility
System MUST be containerized and deployable with Helm. Any developer should be able to reproduce the environment from scratch.

## Technology Standards

| Layer | Technology | Version |
|-------|------------|---------|
| Backend Runtime | Python | 3.13+ |
| Backend Framework | FastAPI | 0.115+ |
| ORM | SQLModel | Latest |
| Database | Neon Serverless PostgreSQL | - |
| Frontend Framework | Next.js | 15+ |
| Frontend Styling | Tailwind CSS | Latest |
| Authentication | Better Auth | JWT-based |
| AI SDK | OpenAI Agents SDK | Latest |
| MCP | Official MCP SDK (FastMCP) | 2.0+ |
| Containerization | Docker | Latest |
| Local Orchestration | Minikube | Latest |
| Package Manager | Helm | Latest |
| Production Orchestration | Kubernetes | Latest |

## Operational Rules

1. **Database Security**: All database queries MUST be scoped by `user_id` from JWT. No cross-user data access.
2. **Stateless AI**: Chatbot and MCP tools MUST be stateless. All state stored in the database.
3. **Monorepo Structure**: Use `/specs`, `/frontend`, `/backend` directory structure.
4. **Secret Management**: No hardcoded secrets. Use environment variables and K8s secrets.

## Project Phases

### Phase I: CLI Todo App
- Todo app runs in terminal
- Add, list, update, delete todos
- Local storage (file or memory-based)
- Focus on logic, not UI

### Phase II: Web-based Todo App
- Frontend UI with Next.js
- Backend API for todo operations
- Clear separation of frontend & backend
- Database persistence

### Phase III: ChatKit Integration
- Integrate OpenAI ChatKit
- Users manage todos via chat
- Structured data extraction
- Conversational agent capabilities

### Phase IV: Minikube & Kubernetes Deployment
- Dockerize frontend and backend
- Create Kubernetes manifests
- Run on Minikube locally
- Validate inter-service communication

### Phase V: Production-Ready Architecture
- Security hardening
- Environment variables & secrets
- Scalability considerations
- Cloud deployment (DigitalOcean Kubernetes)

## Success Criteria

- All 5 hackathon phases completed
- 100% code generated via specs
- Phase V deployed on production Kubernetes

## Governance

- Constitution supersedes all other practices
- Amendments require documentation and approval
- All PRs must verify compliance with these principles
- Use semantic versioning for constitution changes

**Version**: 1.0.0 | **Ratified**: 2026-01-01 | **Last Amended**: 2026-01-23
