# Implementation Plan: Phase I – In-Memory Todo CLI Application

**Branch**: `001-in-memory-todo-cli` | **Date**: 2026-01-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-in-memory-todo-cli/spec.md`

## Summary

Build a single-user, command-line todo list application in Python 3.13 with in-memory storage. The application provides CRUD operations (add, view, update, delete) plus toggle completion, driven by typed command words. No persistence, no external dependencies beyond Python standard library, managed via `uv` package manager.

## Technical Context

**Language/Version**: Python 3.13 stable
**Primary Dependencies**: None (standard library only)
**Package Manager**: uv
**Storage**: In-memory (dict-based)
**Testing**: Manual acceptance testing against spec scenarios
**Target Platform**: Local CLI (Windows/Linux/macOS)
**Project Type**: Single CLI application
**Performance Goals**: N/A (interactive CLI, instant response)
**Constraints**: No persistence, no external APIs, single-user
**Scale/Scope**: Single user, single session, unbounded task count (memory-limited)

## Constitution Check

*GATE: Must pass before implementation. Phase I is a standalone CLI with no backend/frontend split.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Only | ✅ PASS | Implementation from spec.md, code via Claude Code |
| II. Clean Architecture | ✅ PASS (Adapted) | Single CLI app; separation via modules (models, services, cli) |
| III. Accuracy | ✅ PASS | All acceptance criteria mapped to test scenarios |
| IV. Reproducibility | ✅ PASS (Adapted) | Phase I is local-only; no containers required |

**Note**: Phase I intentionally deviates from full monorepo structure (no frontend/, backend/, charts/) as it is a standalone CLI proof-of-concept. Full architecture applies in later phases.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Layer (main.py)                     │
│  - Main loop: prompt → parse command → dispatch → display    │
│  - Command parsing (case-insensitive)                        │
│  - User input/output formatting                              │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer (task_service.py)            │
│  - add_task(title, description?) → Task                      │
│  - get_all_tasks() → list[Task]                              │
│  - get_task(id) → Task | None                                │
│  - update_task(id, title?, description?) → Task | None       │
│  - delete_task(id) → bool                                    │
│  - toggle_task(id) → Task | None                             │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Model Layer (task.py)                      │
│  - Task dataclass: id, title, description, completed         │
│  - TaskStore: dict[int, Task] + next_id counter              │
└─────────────────────────────────────────────────────────────┘
```

### Control Flow

```
┌──────────┐     ┌───────────┐     ┌──────────────┐     ┌─────────┐
│  Start   │────▶│ Show Menu │────▶│ Read Command │────▶│ Parse   │
└──────────┘     └───────────┘     └──────────────┘     └────┬────┘
                       ▲                                      │
                       │                                      ▼
                       │                              ┌───────────────┐
                       │                              │ Valid Command?│
                       │                              └───────┬───────┘
                       │                         yes ┌────────┴────────┐ no
                       │                             ▼                  ▼
                       │                      ┌───────────┐     ┌──────────────┐
                       │                      │ Execute   │     │ Show Error + │
                       │                      │ Handler   │     │ List Commands│
                       │                      └─────┬─────┘     └──────┬───────┘
                       │                            │                   │
                       │                            ▼                   │
                       │                     ┌────────────┐             │
                       │                     │ exit cmd?  │             │
                       │                     └──────┬─────┘             │
                       │                  no ┌──────┴──────┐ yes        │
                       │                     ▼             ▼            │
                       └─────────────────────┤        ┌────────┐        │
                                             │        │  End   │        │
                                             │        └────────┘        │
                                             └──────────────────────────┘
```

## Project Structure

### Documentation (this feature)

```text
specs/001-in-memory-todo-cli/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── checklists/
│   └── requirements.md  # Requirements checklist
└── tasks.md             # Task breakdown (created by /sp.tasks)
```

### Source Code (repository root)

```text
src/
├── __init__.py          # Package marker
├── main.py              # Entry point: CLI loop and command dispatch
├── models/
│   ├── __init__.py
│   └── task.py          # Task dataclass and TaskStore
├── services/
│   ├── __init__.py
│   └── task_service.py  # Business logic for CRUD operations
└── cli/
    ├── __init__.py
    ├── commands.py      # Command handlers (add, view, update, delete, toggle, exit)
    ├── parser.py        # Command parsing and validation
    └── display.py       # Output formatting (checkbox display, messages)

pyproject.toml           # uv project configuration
```

**Structure Decision**: Single project structure selected. Separation of concerns achieved via three layers:
- `models/` — Data structures only, no logic
- `services/` — Business logic, storage operations
- `cli/` — User interaction, I/O formatting

## Architectural Decisions

### ADR-001: Task Storage — Dictionary vs List

**Decision**: Use `dict[int, Task]` for task storage.

**Context**: Need to store tasks with unique integer IDs and support O(1) lookup by ID for update, delete, and toggle operations.

**Options Considered**:
| Option | Lookup | Insert | Delete | Pros | Cons |
|--------|--------|--------|--------|------|------|
| `list[Task]` | O(n) | O(1) | O(n) | Simple iteration | Slow ID lookup |
| `dict[int, Task]` | O(1) | O(1) | O(1) | Fast all operations | Slightly more memory |

**Rationale**: Dictionary provides O(1) operations for all required actions. ID-based access is the primary pattern (update, delete, toggle all require ID lookup).

### ADR-002: ID Generation Strategy

**Decision**: Simple incrementing counter starting at 1, never reused.

**Context**: Need unique, human-readable task IDs.

**Options Considered**:
| Option | Pros | Cons |
|--------|------|------|
| Incrementing int | Simple, predictable, human-friendly | IDs not reused after delete |
| UUID | Globally unique | Long, hard to type |
| Reused IDs | Memory efficient | Confusing if user deletes task 3, adds new one as 3 |

**Rationale**: Incrementing integers are easiest for CLI input. ID reuse rejected to avoid user confusion ("I deleted task 3, why is there a new task 3?"). Memory overhead negligible for in-memory app.

### ADR-003: Command Parsing Approach

**Decision**: Simple string matching with `.lower().strip()`.

**Context**: Commands are single words (add, view, update, delete, toggle, exit), case-insensitive.

**Options Considered**:
| Option | Pros | Cons |
|--------|------|------|
| argparse | Built-in, feature-rich | Overkill for 6 commands |
| click library | Nice UX | External dependency |
| Simple string match | No dependencies, minimal code | Manual help text |

**Rationale**: Six fixed commands don't warrant a parsing library. Simple `match` statement in Python 3.13 provides clean dispatch. Avoid external dependencies per spec constraints.

### ADR-004: Separation of Concerns

**Decision**: Three-layer architecture (models → services → cli).

**Context**: Need clean separation for testability and future extensibility (Phase II will add persistence).

**Layer Responsibilities**:
| Layer | Responsibility | Dependencies |
|-------|---------------|--------------|
| `models/` | Data structures (Task, TaskStore) | None |
| `services/` | Business logic (validation, CRUD) | models |
| `cli/` | User I/O, command dispatch | services |

**Rationale**: This structure allows Phase II to swap `TaskStore` for a database without changing `cli/` or service interfaces.

## Implementation Approach

### Phase Mapping to User Stories

| Implementation Step | User Story | Priority |
|--------------------|------------|----------|
| 1. Project setup (uv, pyproject.toml) | — | Setup |
| 2. Task model and TaskStore | All | Foundation |
| 3. TaskService with add() | US-1 Add Task | P1 |
| 4. TaskService with get_all() | US-2 View Tasks | P1 |
| 5. CLI loop and view command | US-2 View Tasks | P1 |
| 6. CLI add command | US-1 Add Task | P1 |
| 7. TaskService toggle() | US-3 Toggle | P2 |
| 8. CLI toggle command | US-3 Toggle | P2 |
| 9. TaskService update() | US-4 Update | P2 |
| 10. CLI update command | US-4 Update | P2 |
| 11. TaskService delete() | US-5 Delete | P2 |
| 12. CLI delete command | US-5 Delete | P2 |
| 13. Exit command | US-6 Exit | P3 |
| 14. Error handling & edge cases | All | Polish |

### Input Validation Rules

| Input | Validation | Error Message |
|-------|-----------|---------------|
| Command | Case-insensitive match against known commands | "Unknown command. Available: add, view, update, delete, toggle, exit" |
| Task title | Non-empty after strip() | "Error: Title cannot be empty" |
| Task ID | Positive integer, exists in store | "Error: Invalid ID" / "Error: Task not found" |
| Description | Any string (optional, empty = no change) | — |

### Output Formatting

**Task Display Format**:
```
[x] 1: Buy groceries
    Description: Get milk and eggs
[ ] 2: Call doctor
```

**Confirmation Messages**:
- Add: `Task added: [1] "Buy groceries"`
- Update: `Task updated: [1] "Buy organic groceries"`
- Delete: `Task deleted: [1]`
- Toggle: `Task [1] marked as complete` / `Task [1] marked as incomplete`

**Empty List**: `No tasks yet. Use 'add' to create one.`

**Menu Prompt**: `> ` (simple prompt, commands listed on unknown input)

## Testing Strategy

### Manual Acceptance Testing

Each acceptance scenario from spec.md will be tested manually in sequence:

**US-1 Add Task (3 scenarios)**:
- [ ] Add task with title only → verify ID, status, confirmation
- [ ] Add task with title + description → verify both stored
- [ ] Add empty/whitespace title → verify error, re-prompt

**US-2 View Tasks (3 scenarios)**:
- [ ] View after adding tasks → verify ID, title, checkbox status
- [ ] View with empty list → verify empty message
- [ ] View mixed complete/incomplete → verify `[x]` vs `[ ]`

**US-3 Toggle Completion (3 scenarios)**:
- [ ] Toggle incomplete → complete → verify `[x]` and confirmation
- [ ] Toggle complete → incomplete → verify `[ ]` and confirmation
- [ ] Toggle non-existent ID → verify error message

**US-4 Update Task (4 scenarios)**:
- [ ] Update title → verify new title in view
- [ ] Update description → verify new description
- [ ] Update with empty field → verify original retained
- [ ] Update non-existent ID → verify error message

**US-5 Delete Task (3 scenarios)**:
- [ ] Delete existing task → verify confirmation
- [ ] Delete non-existent ID → verify error message
- [ ] View after delete → verify task gone

**US-6 Exit (2 scenarios)**:
- [ ] Exit from main menu → verify goodbye, clean termination
- [ ] Exit after operations → verify no errors

### Edge Case Testing

- [ ] Non-numeric task ID input → error + re-prompt
- [ ] Negative task ID → error message
- [ ] Empty command (just Enter) → re-prompt
- [ ] Unknown command → error + list available commands
- [ ] Very long title → accepted (no explicit limit)
- [ ] Special characters in title/description → accepted

### Validation Checklist

| Requirement | Test Method | Pass Criteria |
|-------------|-------------|---------------|
| FR-001 Add with title/desc | Manual | Task created with both fields |
| FR-002 Auto-generate ID | Manual | ID is unique integer, increments |
| FR-003 Initial status | Manual | New tasks show `[ ]` incomplete |
| FR-004 Display format | Manual | Shows ID, title, checkbox |
| FR-005 Update by ID | Manual | Title/desc can be changed |
| FR-006 Delete by ID | Manual | Task removed from list |
| FR-007 Toggle status | Manual | Status flips on toggle |
| FR-008 Validate title | Manual | Empty title rejected |
| FR-009 Error messages | Manual | Clear messages for invalid ops |
| FR-010 Command interface | Manual | Commands work case-insensitive |
| FR-011 Exit option | Manual | Exit terminates cleanly |
| FR-012 In-memory only | Verify | No files created during operation |
| FR-013 Unknown command | Manual | Shows error + available commands |

## Quality Validation Steps

1. **Pre-Implementation**
   - [ ] Spec complete with all clarifications integrated
   - [ ] Plan reviewed and approved
   - [ ] Project structure created with uv

2. **During Implementation**
   - [ ] Each module created follows layer separation
   - [ ] No external dependencies added
   - [ ] Code matches spec exactly (no extras)

3. **Post-Implementation**
   - [ ] All 18 acceptance scenarios pass
   - [ ] All 6 edge cases handled correctly
   - [ ] All 13 functional requirements verified
   - [ ] Application runs without crashes on valid input
   - [ ] Application handles invalid input gracefully

4. **Delivery Checklist**
   - [ ] `uv run python -m src.main` starts application
   - [ ] All commands work as specified
   - [ ] No files created during runtime (in-memory verified)
   - [ ] Clean exit with goodbye message

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep (adding features) | Medium | Strict adherence to spec; no "improvements" |
| Inconsistent state after errors | Low | Service layer validates before mutating |
| User confusion on IDs after delete | Low | IDs never reused; documented behavior |

## Next Steps

1. Run `/sp.tasks` to generate task breakdown
2. Implement in order: setup → models → services → cli
3. Test each user story as completed
4. Final validation against all acceptance criteria
