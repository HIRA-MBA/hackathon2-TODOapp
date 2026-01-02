---
id: 007
title: Auth Guard Sub-Agent Created
stage: general
date: 2026-01-01
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: master
user: unknown
command: user-request
labels: ["sub-agent", "security", "jwt", "authentication", "authorization"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/agents/auth-guard.md
tests:
  - null
---

## Prompt

Create a sub-agent called "Auth Guard".

Responsibility:
Enforce JWT-based user isolation across frontend, backend, and MCP tools.

Rules:
- Extract user_id only from verified JWT
- All database queries must be filtered by user_id
- Reject any endpoint or tool without authentication enforcement

## Response snapshot

Created Auth Guard sub-agent at `.claude/agents/auth-guard.md` with:

**Layer Enforcement:**
- Frontend: JWT in httpOnly cookie/header, API client interceptor
- Backend API: Bearer token validation, FastAPI dependency
- MCP Tools: Context-injected user_id, Tool dispatcher
- Database: Query scoping in service layer

**6-Phase Execution Protocol:**
1. Authentication Flow Verification - JWT creation/verification
2. Backend Dependency Enforcement - FastAPI get_current_user
3. Endpoint Audit - Scan all routes for auth dependency
4. Database Query Audit - Verify user_id filtering
5. MCP Tool Audit - Verify user_id injection
6. Frontend Auth Verification - Check JWT handling

**Forbidden Patterns:**
- User ID from request body (impersonation risk)
- Unscoped queries (data leakage)
- Missing auth dependency (unauthenticated access)
- IDOR vulnerabilities (accessing other users' data)

**Rejection Criteria:**
- No auth dependency on data-accessing endpoint
- user_id from untrusted source
- Unscoped database query
- MCP tool without user context

## Outcome

- ✅ Impact: Security enforcement sub-agent for JWT-based isolation
- 🧪 Tests: N/A (agent definition, not implementation code)
- 📁 Files: 1 file created (.claude/agents/auth-guard.md)
- 🔁 Next prompts: Invoke during endpoint/tool creation, pre-commit security gate
- 🧠 Reflection: Sub-agent enforces defense-in-depth; audits all layers; forbidden patterns document common vulnerabilities; rejection criteria prevent insecure code from being committed

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test on first protected endpoint implementation
