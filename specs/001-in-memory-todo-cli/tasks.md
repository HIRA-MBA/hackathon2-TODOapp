# Tasks: Phase I – In-Memory Todo CLI Application

**Input**: Design documents from `/specs/001-in-memory-todo-cli/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Manual acceptance testing only (no automated tests requested in spec)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/` at repository root
- Paths based on plan.md structure

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Initialize Python project with uv and create directory structure

- [x] T001 Initialize Python project with uv: run `uv init` and configure pyproject.toml for Python 3.13
- [x] T002 Create source directory structure: src/, src/models/, src/services/, src/cli/
- [x] T003 [P] Create package markers: src/__init__.py, src/models/__init__.py, src/services/__init__.py, src/cli/__init__.py

---

## Phase 2: Foundational (Core Data Structures)

**Purpose**: Task model and storage that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create Task dataclass in src/models/task.py with fields: id (int), title (str), description (str | None), completed (bool)
- [x] T005 Create TaskStore class in src/models/task.py with dict[int, Task] storage and next_id counter
- [x] T006 Implement TaskStore.add() method returning new Task with auto-generated ID
- [x] T007 Implement TaskStore.get_all() method returning list[Task]
- [x] T008 Implement TaskStore.get_by_id() method returning Task | None
- [x] T009 Implement TaskStore.update() method for partial updates
- [x] T010 Implement TaskStore.delete() method returning bool
- [x] T011 Implement TaskStore.toggle() method returning Task | None

**Checkpoint**: TaskStore ready with full CRUD - user story implementation can begin

---

## Phase 3: User Story 1 - Add a New Task (Priority: P1)

**Goal**: Users can add tasks with title and optional description

**Independent Test**: Launch app → type "add" → enter title → verify confirmation and task appears in view

### Implementation for User Story 1

- [x] T012 [US1] Create TaskService class in src/services/task_service.py with TaskStore instance
- [x] T013 [US1] Implement TaskService.add_task(title, description) with title validation (non-empty)
- [x] T014 [P] [US1] Create display module in src/cli/display.py with format_task() and format_task_list() functions
- [x] T015 [P] [US1] Create parser module in src/cli/parser.py with parse_command() function (case-insensitive)
- [x] T016 [US1] Create commands module in src/cli/commands.py with handle_add() function
- [x] T017 [US1] Implement add command flow: prompt for title → validate → prompt for description (optional) → call service → show confirmation

**Checkpoint**: User Story 1 complete - can add tasks via CLI

---

## Phase 4: User Story 2 - View All Tasks (Priority: P1)

**Goal**: Users can see all tasks with ID, title, and checkbox status

**Independent Test**: Add tasks → type "view" → verify all tasks shown with [x]/[ ] indicators

### Implementation for User Story 2

- [x] T018 [US2] Implement TaskService.get_all_tasks() returning list[Task]
- [x] T019 [US2] Implement display.format_task() with checkbox indicators: [x] for complete, [ ] for incomplete
- [x] T020 [US2] Implement display.format_task_list() showing ID, checkbox, title, and description if present
- [x] T021 [US2] Implement display.show_empty_list_message() for when no tasks exist
- [x] T022 [US2] Create handle_view() function in src/cli/commands.py

**Checkpoint**: User Stories 1 AND 2 complete - can add and view tasks

---

## Phase 5: User Story 3 - Toggle Task Completion (Priority: P2)

**Goal**: Users can mark tasks complete/incomplete by ID

**Independent Test**: Add task → toggle by ID → view to verify status changed

### Implementation for User Story 3

- [x] T023 [US3] Implement TaskService.toggle_task(id) returning Task | None
- [x] T024 [US3] Create handle_toggle() function in src/cli/commands.py
- [x] T025 [US3] Implement toggle flow: prompt for ID → validate → call service → show confirmation or error

**Checkpoint**: User Story 3 complete - can toggle task completion

---

## Phase 6: User Story 4 - Update Task Details (Priority: P2)

**Goal**: Users can update task title and/or description by ID

**Independent Test**: Add task → update title → view to verify change

### Implementation for User Story 4

- [x] T026 [US4] Implement TaskService.update_task(id, title, description) with partial update support
- [x] T027 [US4] Create handle_update() function in src/cli/commands.py
- [x] T028 [US4] Implement update flow: prompt for ID → validate → prompt for new title (Enter to keep) → prompt for new description → call service → show confirmation

**Checkpoint**: User Story 4 complete - can update task details

---

## Phase 7: User Story 5 - Delete a Task (Priority: P2)

**Goal**: Users can delete tasks by ID

**Independent Test**: Add task → delete by ID → view to verify gone

### Implementation for User Story 5

- [x] T029 [US5] Implement TaskService.delete_task(id) returning bool
- [x] T030 [US5] Create handle_delete() function in src/cli/commands.py
- [x] T031 [US5] Implement delete flow: prompt for ID → validate → call service → show confirmation or error

**Checkpoint**: User Story 5 complete - can delete tasks

---

## Phase 8: User Story 6 - Exit Application (Priority: P3)

**Goal**: Users can exit gracefully with goodbye message

**Independent Test**: Type "exit" → verify goodbye message and clean termination

### Implementation for User Story 6

- [x] T032 [US6] Create handle_exit() function in src/cli/commands.py returning exit signal
- [x] T033 [US6] Implement goodbye message display

**Checkpoint**: User Story 6 complete - clean exit works

---

## Phase 9: CLI Main Loop & Integration

**Purpose**: Wire everything together in main entry point

- [x] T034 Create main.py entry point in src/main.py
- [x] T035 Implement main loop: display prompt → read input → parse command → dispatch to handler → repeat
- [x] T036 Implement command dispatch using match statement for: add, view, toggle, update, delete, exit
- [x] T037 Implement unknown command handler: show error + list available commands
- [x] T038 Add welcome message on application start

**Checkpoint**: Full CLI application functional

---

## Phase 10: Polish & Edge Cases

**Purpose**: Handle all edge cases from spec

- [x] T039 [P] Validate non-numeric task ID input with error message in src/cli/commands.py
- [x] T040 [P] Validate negative task ID with error message
- [x] T041 [P] Handle empty input (just Enter) at command prompt - re-prompt
- [x] T042 [P] Handle whitespace-only title with error message
- [x] T043 Verify all error messages match spec requirements
- [x] T044 Manual acceptance testing: run all 18 scenarios from spec.md
- [x] T045 Manual edge case testing: run all 6 edge cases from spec.md

**Checkpoint**: All acceptance criteria verified

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on Foundational (can parallel with US1 for service, needs US1 display module)
- **User Stories 3-6 (Phases 5-8)**: Depend on Foundational, can proceed after US1+US2 for full CLI context
- **Main Loop (Phase 9)**: Depends on all user story handlers being complete
- **Polish (Phase 10)**: Depends on Main Loop complete

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US1 (Add) | Foundational | US2 (partially) |
| US2 (View) | Foundational, US1 display module | - |
| US3 (Toggle) | Foundational | US4, US5 |
| US4 (Update) | Foundational | US3, US5 |
| US5 (Delete) | Foundational | US3, US4 |
| US6 (Exit) | Foundational | US3, US4, US5 |

### Within Each User Story

1. Service method first
2. CLI handler second
3. Flow/integration third

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003 package markers can run parallel

**Phase 3 (US1)**:
- T014 (display) and T015 (parser) can run parallel

**Phase 10 (Polish)**:
- T039, T040, T041, T042 can all run parallel (different validation cases)

---

## Parallel Example: User Story 1

```bash
# These can run in parallel (different files):
Task T014: "Create display module in src/cli/display.py"
Task T015: "Create parser module in src/cli/parser.py"

# Then sequential:
Task T016: "Create commands module" (depends on display, parser)
Task T017: "Implement add flow" (depends on T016)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Add)
4. Complete Phase 4: User Story 2 (View)
5. **STOP and VALIDATE**: Can add and view tasks
6. Continue with remaining stories

### Recommended Order

1. Setup (T001-T003)
2. Foundational (T004-T011)
3. US1 Add (T012-T017)
4. US2 View (T018-T022)
5. Main Loop skeleton (T034-T038) - minimal version
6. US3-US6 (T023-T033)
7. Polish (T039-T045)

### Single Developer Timeline

| Phase | Tasks | Est. Effort |
|-------|-------|-------------|
| Setup | 3 | Quick |
| Foundational | 8 | Core work |
| US1 + US2 | 11 | MVP |
| US3-US6 | 11 | Features |
| Main Loop | 5 | Integration |
| Polish | 7 | Validation |
| **Total** | **45** | - |

---

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 45 |
| Phase 1 (Setup) | 3 |
| Phase 2 (Foundational) | 8 |
| US1 (Add) | 6 |
| US2 (View) | 5 |
| US3 (Toggle) | 3 |
| US4 (Update) | 3 |
| US5 (Delete) | 3 |
| US6 (Exit) | 2 |
| Main Loop | 5 |
| Polish | 7 |
| Parallel opportunities | 10 tasks marked [P] |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete work
- [Story] label maps task to specific user story for traceability
- Manual testing only - no automated tests per spec
- Each checkpoint allows validation before proceeding
- Commit after each task or logical group
