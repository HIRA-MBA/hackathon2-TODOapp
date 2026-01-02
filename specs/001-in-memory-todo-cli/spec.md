# Feature Specification: Phase I – In-Memory Todo CLI Application

**Feature Branch**: `001-in-memory-todo-cli`
**Created**: 2026-01-01
**Status**: Draft
**Input**: User description: "Build a Python command-line application for single-user todo list management with in-memory storage"

## Clarifications

### Session 2026-01-02

- Q: What Python version and package manager should be used? → A: Python 3.13 stable with uv package manager
- Q: How should users select menu options? → A: Command words (add, view, update, delete, toggle, exit)
- Q: How should completed tasks be visually distinguished? → A: Checkbox indicator (`[ ]` incomplete, `[x]` complete)
- Q: How should the system handle unrecognized commands? → A: Display error message + list available commands
- Q: Should commands be case-sensitive? → A: Case-insensitive (ADD, Add, add all work)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add a New Task (Priority: P1)

As a user, I want to add a new task to my todo list so that I can track items I need to complete.

**Why this priority**: Adding tasks is the fundamental operation - without it, no other features have value. This is the core capability that makes the application useful.

**Independent Test**: Can be fully tested by launching the application, selecting "Add Task", entering a title, and verifying the task appears in the list.

**Acceptance Scenarios**:

1. **Given** the application is running and showing the main menu, **When** I select "Add Task" and enter a title "Buy groceries", **Then** a new task is created with that title, an auto-generated unique ID, status "incomplete", and I see a confirmation message.

2. **Given** I am adding a new task, **When** I enter a title "Call doctor" and an optional description "Schedule annual checkup", **Then** the task is created with both title and description stored.

3. **Given** I am adding a new task, **When** I enter an empty title or only whitespace, **Then** the system displays an error message and prompts me to enter a valid title.

---

### User Story 2 - View All Tasks (Priority: P1)

As a user, I want to view all my tasks so that I can see what I need to do and what I have completed.

**Why this priority**: Viewing tasks is essential for the user to understand their todo list state. Without this, added tasks would be invisible.

**Independent Test**: Can be fully tested by adding several tasks, then selecting "View Tasks" to see them all displayed with their details.

**Acceptance Scenarios**:

1. **Given** I have added tasks to my list, **When** I select "View Tasks", **Then** I see all tasks displayed with their ID, title, and completion status (complete/incomplete).

2. **Given** I have no tasks in my list, **When** I select "View Tasks", **Then** I see a message indicating the list is empty.

3. **Given** I have tasks with different completion statuses, **When** I view the task list, **Then** completed tasks display `[x]` and incomplete tasks display `[ ]` checkbox indicators.

---

### User Story 3 - Toggle Task Completion (Priority: P2)

As a user, I want to mark tasks as complete or incomplete so that I can track my progress.

**Why this priority**: Tracking completion is the primary purpose of a todo list after adding and viewing tasks.

**Independent Test**: Can be fully tested by adding a task, toggling its status, and verifying the status changes in the task list.

**Acceptance Scenarios**:

1. **Given** I have an incomplete task with ID 1, **When** I select "Toggle Completion" and enter ID 1, **Then** the task status changes to "complete" and I see a confirmation.

2. **Given** I have a complete task with ID 2, **When** I select "Toggle Completion" and enter ID 2, **Then** the task status changes to "incomplete" and I see a confirmation.

3. **Given** I enter a task ID that does not exist, **When** I try to toggle completion, **Then** I see an error message indicating the task was not found.

---

### User Story 4 - Update Task Details (Priority: P2)

As a user, I want to update task title and description so that I can correct mistakes or add more details.

**Why this priority**: Updating tasks allows users to refine their list without deleting and recreating tasks.

**Independent Test**: Can be fully tested by adding a task, updating its title or description, and verifying the changes are reflected.

**Acceptance Scenarios**:

1. **Given** I have a task with ID 1 titled "Buy groceries", **When** I select "Update Task", enter ID 1, and provide a new title "Buy organic groceries", **Then** the task title is updated and I see a confirmation.

2. **Given** I have a task with ID 1, **When** I select "Update Task", enter ID 1, and provide a new description "Get milk and eggs", **Then** the task description is updated.

3. **Given** I am updating a task, **When** I leave a field empty, **Then** that field retains its previous value (partial updates allowed).

4. **Given** I enter a task ID that does not exist, **When** I try to update, **Then** I see an error message indicating the task was not found.

---

### User Story 5 - Delete a Task (Priority: P2)

As a user, I want to delete a task so that I can remove items that are no longer needed.

**Why this priority**: Deletion allows users to clean up their list and remove irrelevant tasks.

**Independent Test**: Can be fully tested by adding a task, deleting it, and verifying it no longer appears in the list.

**Acceptance Scenarios**:

1. **Given** I have a task with ID 1, **When** I select "Delete Task" and enter ID 1, **Then** the task is removed from the list and I see a confirmation.

2. **Given** I enter a task ID that does not exist, **When** I try to delete, **Then** I see an error message indicating the task was not found.

3. **Given** I delete a task, **When** I view the task list, **Then** the deleted task no longer appears.

---

### User Story 6 - Exit Application (Priority: P3)

As a user, I want to exit the application gracefully so that I can end my session.

**Why this priority**: A clean exit option is necessary for good user experience, but not core functionality.

**Independent Test**: Can be fully tested by selecting the exit option and verifying the application terminates cleanly.

**Acceptance Scenarios**:

1. **Given** the main menu is displayed, **When** I select "Exit", **Then** the application terminates with a goodbye message.

2. **Given** I am in any menu, **When** the exit option is available and selected, **Then** the application exits without errors.

---

### Edge Cases

- What happens when the user enters a non-numeric value for task ID? System displays an error and prompts for valid input.
- What happens when the user enters a negative task ID? System displays an error indicating invalid ID.
- How does the system handle very long task titles? System accepts titles up to reasonable length (no explicit limit specified - accepts standard input).
- What happens when the user presses Enter without input at a required prompt? System prompts again for valid input.
- How does the system handle special characters in title/description? System accepts and stores all printable characters.
- What happens when the user enters an unrecognized command? System displays an error message and lists all available commands (add, view, update, delete, toggle, exit).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to add a new task with a required title and optional description.
- **FR-002**: System MUST auto-generate a unique ID for each new task.
- **FR-003**: System MUST initialize new tasks with "incomplete" status.
- **FR-004**: System MUST display all tasks showing ID, title, and completion status.
- **FR-005**: System MUST allow users to update task title and/or description by task ID.
- **FR-006**: System MUST allow users to delete a task by task ID.
- **FR-007**: System MUST allow users to toggle task completion status between complete and incomplete.
- **FR-008**: System MUST validate that task titles are non-empty.
- **FR-009**: System MUST display appropriate error messages for invalid operations (task not found, invalid input).
- **FR-010**: System MUST provide a command-driven interface using typed command words (add, view, update, delete, toggle, exit) that repeats after each action. Commands MUST be case-insensitive.
- **FR-011**: System MUST provide an explicit exit option in the menu.
- **FR-012**: System MUST store all tasks in memory only (no file or database persistence).
- **FR-013**: System MUST display an error message and list all available commands when an unrecognized command is entered.

### Key Entities

- **Task**: Represents a todo item with the following attributes:
  - **id**: Unique identifier, auto-generated integer starting from 1
  - **title**: Required non-empty string describing the task
  - **description**: Optional string with additional details
  - **status**: Completion state, either "complete" or "incomplete"

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can add a task with title in under 10 seconds from menu selection.
- **SC-002**: Users can view all tasks and identify each task's status at a glance.
- **SC-003**: All CRUD operations (add, view, update, delete) complete without errors when valid input is provided.
- **SC-004**: Invalid inputs (empty title, non-existent ID) result in clear error messages without application crash.
- **SC-005**: Application returns to main menu after every operation, allowing continuous use.
- **SC-006**: Application exits cleanly when user selects the exit option.
- **SC-007**: 100% of acceptance scenarios pass when tested manually.

## Technical Constraints

- **TC-001**: Application MUST use Python 3.13 stable version.
- **TC-002**: Project MUST use `uv` as the package manager for dependency management and virtual environment.

## Assumptions

- Single user operates the application; no concurrent access concerns.
- Tasks are stored in memory and will be lost when application exits (this is expected behavior for Phase I).
- Task IDs are simple incrementing integers (no UUID or complex ID generation needed).
- No data validation beyond basic input validation (non-empty title, valid ID format).
- No undo/redo functionality required.
- No sorting or filtering of tasks required beyond basic display.

## Out of Scope

- Database or file persistence
- Authentication or user accounts
- Web UI or REST APIs
- AI agents, MCP tools, or cloud deployment
- Advanced error handling beyond basic input validation
- Task priorities, due dates, or categories
- Search or filter functionality
- Multiple users or concurrent access
