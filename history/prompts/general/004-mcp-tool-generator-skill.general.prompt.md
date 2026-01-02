---
id: 004
title: MCP Tool Generator Skill Created
stage: general
date: 2026-01-01
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: master
user: unknown
command: user-request
labels: ["skill", "mcp", "openai-agents", "codegen", "stateless"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .claude/commands/sp.mcp-tools.md
tests:
  - null
---

## Prompt

Create a reusable skill called "MCP Tool Generator".

Role:
Convert backend CRUD logic into MCP tools compatible with
OpenAI Agents SDK.

Rules:
- Tool parameters must match database schema and specs
- Tools must be stateless
- Persist all state to the database

## Response snapshot

Created `/sp.mcp-tools` command at `.claude/commands/sp.mcp-tools.md` implementing the MCP Tool Generator skill with:

**7-Phase Execution Flow:**
1. Load Source Context - parse services, data-model.md, specs
2. Build Tool Registry - YAML structure with CRUD operations
3. Generate MCP Tool Definitions - Pydantic schemas + Tool objects
4. Generate MCP Server Registration - dispatcher and OpenAI SDK export
5. Statelessness Verification - static analysis for forbidden patterns
6. User Scoping Verification - ensure all ops filtered by user_id
7. Schema Validation - match tool params to database schema

**Core Rules Enforced:**
- Parameter schema match (tool params = DB schema = specs)
- Stateless tools (no class-level state, no globals, no mutable closures)
- Database persistence (session per request, commit on write)
- User scoping (all queries include user_id filter)

**Generated Artifacts:**
- backend/src/mcp/tools/<resource>.py (tool definitions + handlers)
- backend/src/mcp/server.py (registration + OpenAI SDK export)

## Outcome

- ✅ Impact: New MCP tool generation skill added to project
- 🧪 Tests: N/A (command template, not implementation code)
- 📁 Files: 1 file created (.claude/commands/sp.mcp-tools.md)
- 🔁 Next prompts: Create data-model.md and services, then run /sp.mcp-tools <resource>
- 🧠 Reflection: Skill enforces stateless-first design; verification phases catch violations before deployment; OpenAI SDK export enables direct agent integration

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test on first service to validate generated tool quality
