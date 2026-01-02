---
id: 002
title: Validation Logic Injector Skill Created
stage: general
date: 2026-01-01
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: master
user: unknown
command: user-request
labels: ["skill", "validation", "fastapi", "frontend", "mcp"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/commands/sp.validate.md
tests:
  - null
---

## Prompt

Create a reusable skill called "Validation Logic Injector".

Role:
Read Acceptance Criteria from /specs and inject validation rules into:
- FastAPI request/response models
- Frontend form validation
- MCP tool inputs

Rules:
- Specs are the single source of truth
- No validation logic without a spec reference
- Reject any implementation that violates Acceptance Criteria

## Response snapshot

Created `/sp.validate` command at `.claude/commands/sp.validate.md` implementing the Validation Logic Injector skill with:

**7-Phase Execution Flow:**
1. Load Specification Context - parse spec.md for Acceptance Criteria
2. Build Validation Rules Registry - structured YAML format with spec traceability
3. Inject Validation - FastAPI Backend (Pydantic validators with Field constraints)
4. Inject Validation - Frontend Forms (Zod schemas mirroring backend)
5. Inject Validation - MCP Tool Inputs (parameter validation with descriptions)
6. Cross-Layer Consistency Check - matrix verification across all 3 layers
7. Violation Detection & Rejection - halt on unauthorized/missing validation

**Core Rules Enforced:**
- Specs are single source of truth
- No validation without spec reference (comments required)
- Reject implementations violating Acceptance Criteria
- Cross-layer parity required (backend = frontend = MCP)

## Outcome

- ✅ Impact: New reusable skill added to project command library
- 🧪 Tests: N/A (command template, not implementation code)
- 📁 Files: 1 file created (.claude/commands/sp.validate.md)
- 🔁 Next prompts: Use /sp.validate <feature> after creating specs, integrate with /sp.implement workflow
- 🧠 Reflection: Skill enforces spec-first validation discipline; cross-layer matrix prevents drift between backend/frontend/MCP

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test skill on first feature implementation to validate workflow
