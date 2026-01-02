---
id: 005
title: Three Reusable Skills Created
stage: general
date: 2026-01-01
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: master
user: unknown
command: user-request
labels: ["skills", "validation", "api", "mcp", "codegen"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/skills/validation-logic-injector.md
  - .claude/skills/spec-to-api-sync.md
  - .claude/skills/mcp-tool-generator.md
tests:
  - null
---

## Prompt

User requested three reusable skills (not slash commands):

1. **Validation Logic Injector** - Read Acceptance Criteria from /specs and inject validation rules into FastAPI, frontend forms, and MCP tool inputs.

2. **Spec-to-API Sync** - Generate FastAPI routes and Pydantic models directly from specs/api/rest-endpoints.md.

3. **MCP Tool Generator** - Convert backend CRUD logic into stateless MCP tools compatible with OpenAI Agents SDK.

User clarified that skills should be created in `.claude/skills/` directory, not as slash commands.

## Response snapshot

Created 3 skills in `.claude/skills/`:

| Skill | File | Purpose |
|-------|------|---------|
| Validation Logic Injector | validation-logic-injector.md | Inject spec-based validation into backend/frontend/MCP |
| Spec-to-API Sync | spec-to-api-sync.md | Generate FastAPI routes from API specs |
| MCP Tool Generator | mcp-tool-generator.md | Generate stateless MCP tools from CRUD services |

Each skill includes:
- Description and trigger conditions
- Core rules (non-negotiable constraints)
- Multi-phase execution flow
- Code generation templates
- Verification steps
- Output format

Removed previously created slash commands (sp.validate.md, sp.api-sync.md, sp.mcp-tools.md).

## Outcome

- ✅ Impact: 3 reusable skills added to .claude/skills/ directory
- 🧪 Tests: N/A (skill definitions, not implementation code)
- 📁 Files: 3 files created, 3 files deleted
- 🔁 Next prompts: Invoke skills during feature implementation
- 🧠 Reflection: Skills differ from slash commands - they are reference documents for Claude to follow when triggered, not command prompts

## Evaluation notes (flywheel)

- Failure modes observed: Initially created slash commands instead of skills
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test skill invocation on first feature
