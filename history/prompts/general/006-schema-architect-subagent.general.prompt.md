---
id: 006
title: Schema Architect Sub-Agent Created
stage: general
date: 2026-01-01
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: master
user: unknown
command: user-request
labels: ["sub-agent", "schema", "synchronization", "sqlmodel", "pydantic"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/agents/schema-architect.md
tests:
  - null
---

## Prompt

Create a sub-agent called "Schema Architect".

Responsibility:
Keep SQLModel schemas, database tables, API models, and MCP tool
parameters fully synchronized.

Rules:
- Any schema change must update all layers
- No field may exist in one layer only
- Reject inconsistent or partial updates

## Response snapshot

Created Schema Architect sub-agent at `.claude/agents/schema-architect.md` with:

**5 Layers Managed:**
- Database (SQLModel) - Source of truth
- API Request (Pydantic) - Input validation
- API Response (Pydantic) - Output serialization
- MCP Tools (Pydantic) - AI agent parameters
- Frontend (Zod/TypeScript) - Client-side validation

**5-Phase Execution Protocol:**
1. Schema Discovery - Scan all layers, build YAML representation
2. Drift Detection - Compare layers, identify inconsistencies
3. Synchronization Plan - Generate update plan
4. Apply Synchronization - Execute atomic updates
5. Validation - Verify all layers synchronized

**Field Classification:**
- User Input: All layers
- Read-Only: DB, Response, Frontend
- Internal: DB only
- Computed: Response, Frontend only

**Rejection Criteria:**
- Type mismatches that cannot be reconciled
- Missing source of truth (DB)
- Constraint conflicts
- Breaking changes without migration

## Outcome

- ✅ Impact: Sub-agent for cross-layer schema synchronization created
- 🧪 Tests: N/A (agent definition, not implementation code)
- 📁 Files: 1 file created (.claude/agents/schema-architect.md)
- 🔁 Next prompts: Invoke during schema changes or when drift detected
- 🧠 Reflection: Sub-agent enforces database as source of truth; field classification handles different visibility requirements; rejection criteria prevent data integrity issues

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test on first entity creation to validate synchronization workflow
