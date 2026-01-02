---
id: 003
title: Spec-to-API Sync Skill Created
stage: general
date: 2026-01-01
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: master
user: unknown
command: user-request
labels: ["skill", "api", "fastapi", "pydantic", "codegen"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/commands/sp.api-sync.md
tests:
  - null
---

## Prompt

Create a reusable skill called "Spec-to-API Sync".

Role:
Generate FastAPI routes and Pydantic models directly from
@specs/api/rest-endpoints.md.

Rules:
- Do not invent endpoints
- Route paths, methods, and schemas must exactly match specs
- Update code only when specs change

## Response snapshot

Created `/sp.api-sync` command at `.claude/commands/sp.api-sync.md` implementing the Spec-to-API Sync skill with:

**6-Phase Execution Flow:**
1. Load API Specification - parse specs/api/rest-endpoints.md
2. Generate Pydantic Models - request/response schemas with type mapping
3. Generate FastAPI Routes - handlers with auth dependencies and error responses
4. Register Routes - update main router registry
5. Diff Detection & Sync - hash comparison, change detection, safe sync rules
6. Validation - schema validation, route loading, OpenAPI generation

**Core Rules Enforced:**
- Do not invent endpoints (only spec-defined routes)
- Exact match required (paths, methods, schemas)
- Sync on spec change only (hash-based detection)
- Generated files marked "DO NOT EDIT MANUALLY"

**Type Mapping:** string, integer, uuid, datetime, array[T], email, url → Python/Pydantic equivalents

## Outcome

- ✅ Impact: New API code generation skill added to project
- 🧪 Tests: N/A (command template, not implementation code)
- 📁 Files: 1 file created (.claude/commands/sp.api-sync.md)
- 🔁 Next prompts: Create specs/api/rest-endpoints.md, then run /sp.api-sync
- 🧠 Reflection: Skill enables spec-first API development; diff detection prevents unnecessary regeneration; integrates with /sp.validate for field-level validation

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test on first API spec to validate generated code quality
