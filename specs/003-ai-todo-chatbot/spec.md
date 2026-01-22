# Feature Specification: AI-Powered Todo Chatbot (Phase 3)

**Feature Branch**: `003-ai-todo-chatbot`
**Created**: 2026-01-04
**Status**: Draft
**Input**: User description: "Phase 3: AI-Powered Todo Chatbot with RAG and MCP integration for natural language task management"

## Scope Boundaries

**Phase Isolation Rule**: This specification applies ONLY to Phase 3. Phase 1 (In-Memory CLI) and Phase 2 (Fullstack Web) specifications are immutable and must not be modified.

### In Scope

- Single chat endpoint for natural language task management
- Natural language to task operation translation
- Persistent conversations and message history
- Context-aware responses using user's tasks and chat history
- Stateless request handling (no server-side session state)
- JWT-based authentication (reusing Phase 2 infrastructure)

### Out of Scope

- Deployment, containerization, orchestration (Phase 4)
- Event-driven architecture, message queues (Phase 5)
- Voice input/output
- Multi-language support
- UI redesign or frontend overhaul

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Task via Natural Language (Priority: P1)

A user wants to add a new task by simply describing it in natural language, without navigating through forms or buttons.

**Why this priority**: This is the core value proposition - enabling task creation through conversation. Without this, the chatbot provides no unique value over the existing UI.

**Independent Test**: Can be fully tested by sending a chat message like "Add buy groceries to my list" and verifying the task appears in the user's task list.

**Acceptance Scenarios**:

1. **Given** an authenticated user with an active conversation, **When** they send "Add buy groceries", **Then** the system creates a new task with title "buy groceries" and confirms the action in the response.

2. **Given** an authenticated user, **When** they send "Remind me to call mom tomorrow", **Then** the system creates a task with title "call mom" and due date set to tomorrow, and acknowledges with the task details including the due date.

3. **Given** an authenticated user, **When** they send an ambiguous message like "groceries", **Then** the system asks for clarification before creating a task.

---

### User Story 2 - Query Tasks via Natural Language (Priority: P1)

A user wants to ask about their tasks and receive a relevant, context-aware response based on their actual task data.

**Why this priority**: Querying is equally essential - users need to retrieve information about their tasks through conversation.

**Independent Test**: Can be tested by asking "What tasks do I have pending?" and verifying the response accurately reflects the user's actual task list.

**Acceptance Scenarios**:

1. **Given** a user with 3 pending tasks, **When** they ask "What's on my list?", **Then** the system retrieves and displays all 3 tasks.

2. **Given** a user with completed and pending tasks, **When** they ask "Show me completed tasks", **Then** only completed tasks are shown.

3. **Given** a user with no tasks, **When** they ask "What are my tasks?", **Then** the system responds that they have no tasks and offers to help create one.

---

### User Story 3 - Update Task Status (Priority: P2)

A user wants to mark tasks as complete or update task details through conversation.

**Why this priority**: Completing tasks is a frequent operation, but users can still use the existing UI as a fallback.

**Independent Test**: Can be tested by saying "Mark task 3 done" and verifying the task status changes to completed.

**Acceptance Scenarios**:

1. **Given** a user with a task titled "buy groceries", **When** they say "Mark buy groceries as done", **Then** the task is marked complete and confirmed.

2. **Given** a user with task ID 5, **When** they say "Complete task 5", **Then** task 5 is marked complete.

3. **Given** a user referencing a non-existent task, **When** they say "Complete task 999", **Then** the system responds that the task was not found.

---

### User Story 4 - Delete Task via Chat (Priority: P2)

A user wants to remove tasks from their list through conversation.

**Why this priority**: Deletion is less frequent than creation/completion but still valuable for chat-based management.

**Independent Test**: Can be tested by saying "Delete the groceries task" and verifying the task is removed.

**Acceptance Scenarios**:

1. **Given** a user with a task "buy milk", **When** they say "Delete buy milk task", **Then** the task is deleted and the system confirms.

2. **Given** a user requests deletion of a task, **When** the task title is ambiguous (multiple matches), **Then** the system asks for clarification.

---

### User Story 5 - Conversation Continuity (Priority: P3)

A user expects the chatbot to remember the context of their conversation within a session and across sessions.

**Why this priority**: Continuity improves user experience but the core task operations work without it.

**Independent Test**: Can be tested by starting a conversation, closing the browser, returning, and verifying previous messages are visible and context is maintained.

**Acceptance Scenarios**:

1. **Given** a user with previous chat history, **When** they start a new session, **Then** their conversation history is loaded and displayed.

2. **Given** a user discussing a specific task, **When** they say "mark it done" (referring to previously mentioned task), **Then** the system uses conversation context to identify the task.

---

### Edge Cases

- What happens when a user sends an empty message? System responds asking for input.
- What happens when the AI service is unavailable? System persists the user's message, returns a friendly error, and allows retry without re-typing (message is saved in conversation history).
- How does the system handle very long messages? Messages are truncated at a reasonable limit (2000 characters) with notification.
- What happens when a user tries to access another user's tasks? JWT validation prevents cross-user access; request is rejected with authentication error.
- What happens when conversation history is very large? Only recent relevant messages are retrieved for context (last 20 messages).
- What happens when a user sends too many messages too quickly? System enforces rate limit of 20 requests/minute per user and returns friendly "Please slow down" message.
- What happens when the AI service times out? After 30 seconds, system returns timeout error; no automatic retry; user must manually resend their message.

## Requirements *(mandatory)*

### Functional Requirements

#### Chat Flow

- **FR-001**: System MUST provide a single chat endpoint that accepts natural language messages from authenticated users.
- **FR-002**: System MUST load existing conversation from database when user initiates chat.
- **FR-003**: System MUST retrieve relevant tasks and recent messages to provide context for response generation.
- **FR-004**: System MUST execute appropriate task operations based on interpreted user intent.
- **FR-005**: System MUST persist all assistant responses to the conversation history.

#### Natural Language Processing

- **FR-006**: System MUST translate natural language intents into appropriate task operations (add, list, update, complete, delete).
- **FR-007**: System MUST respond with clarification requests when user intent is unclear, rather than making assumptions.
- **FR-028**: System MUST parse due date expressions from natural language (e.g., "tomorrow", "next Friday", "in 3 days") and set the task due date accordingly. Priority is not parsed; users set priority via UI.
- **FR-030**: System MUST handle multi-intent messages by executing all recognized intents in sequence and returning a combined response (e.g., "Add groceries and show my list" → creates task, then lists tasks).

#### Conversation Management

- **FR-008**: System MUST persist all conversations with unique identifiers per user.
- **FR-009**: System MUST persist all messages (user and assistant) with timestamps and conversation references.
- **FR-010**: System MUST maintain stateless request handling - no in-memory session state between requests.
- **FR-029**: System MUST provide a "Clear history" function that deletes all messages from the user's conversation while preserving the conversation container.

#### Security

- **FR-011**: System MUST require valid JWT authentication for all chat requests.
- **FR-012**: System MUST scope all task operations to the authenticated user (no cross-user data access).
- **FR-026**: System MUST enforce rate limiting of 20 requests per minute per authenticated user, returning a friendly "Please slow down" message when exceeded.
- **FR-027**: System MUST apply a 30-second timeout for AI service requests with no automatic retry; user must manually resend message on timeout.

#### Observability

- **FR-024**: System MUST generate structured logs with unique request IDs for each chat interaction.
- **FR-025**: System MUST capture key metrics including: request latency, AI service response time, and tool call counts.

#### Response Metadata

- **FR-013**: System MUST return tool execution metadata in response including: tool name, success/failure status, and result summary (e.g., "add_task: success - created task 'buy groceries'").

### MCP Tool Requirements

- **FR-014**: System MUST expose an `add_task` tool that creates a new task for the authenticated user.
- **FR-015**: System MUST expose a `list_tasks` tool that retrieves tasks with optional filtering (status, search terms).
- **FR-016**: System MUST expose an `update_task` tool that modifies task properties (title, description).
- **FR-017**: System MUST expose a `complete_task` tool that marks a task as completed.
- **FR-018**: System MUST expose a `delete_task` tool that removes a task.
- **FR-019**: All MCP tools MUST operate through the service layer - no direct database access by the AI orchestration layer.

### RAG Requirements

- **FR-020**: AI responses MUST be grounded in retrieved data (user's actual tasks and conversation history).
- **FR-021**: System MUST NOT hallucinate task information - if data is missing, respond with clarification request.
- **FR-022**: Context retrieval MUST include semantically relevant tasks based on the user's query.
- **FR-023**: Context retrieval MUST include recent conversation messages for continuity.

### Key Entities

- **Conversation**: Represents a single persistent chat session for a user. Contains a unique identifier, user reference, creation timestamp, and last activity timestamp. Each user has exactly one conversation that persists indefinitely (never auto-expires).

- **Message**: Represents a single message within a conversation. Contains role (user, assistant, or tool), content text, timestamp, and optional metadata. The "tool" role captures tool execution results separately from assistant responses. Messages are ordered chronologically within a conversation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a task via chat in under 5 seconds from message send to confirmation.
  - *Measurement*: Manual testing with stopwatch; verify task appears in database.

- **SC-002**: Users can query their task list and receive accurate results in under 3 seconds.
  - *Measurement*: Manual testing with stopwatch; verify response matches database state.

- **SC-003**: Task-related queries return responses grounded in actual user data (no hallucinated tasks).
  - *Measurement*: Manual review of 20 sample interactions verifying all referenced tasks exist in user's database. MCP tools ensure responses use real data.

- **SC-004**: Conversation history is preserved and accessible after browser/session restart.
  - *Measurement*: Manual test - send messages, close browser, reopen, verify history visible.

- **SC-005**: System handles 100 concurrent chat sessions without degradation.
  - *Measurement*: Deferred to Phase 4 load testing. Architecture supports via stateless MCP server design.

- **SC-006**: All 5 task operations (add, list, update, complete, delete) are accessible via natural language commands.
  - *Measurement*: Integration tests verify each tool is callable and executes correctly.

- **SC-007**: Tool execution metadata is included in 100% of responses that involve task operations.
  - *Measurement*: ChatKit UI displays tool calls; verify visually during testing.

- **SC-008**: Zero cross-user data leakage - users can only access their own tasks and conversations.
  - *Measurement*: Integration tests verify user_id scoping; code review of MCP auth middleware.

## Assumptions

1. Phase 2 authentication infrastructure (Better Auth with JWT) is fully functional and reusable.
2. The existing task data model from Phase 2 is sufficient for chatbot operations.
3. Users will primarily interact in English.
4. A single active conversation per user is sufficient for MVP (multiple conversations can be added later).
5. Task relevance for RAG context is determined by recency and keyword matching (MVP). Semantic/embedding-based search is a future enhancement.
6. Message history retrieval defaults to the 20 most recent messages for context.
7. Task operations follow the same business rules as the Phase 2 web interface.

## Dependencies

- **Phase 2 Authentication**: JWT validation and user identification
- **Phase 2 Task Model**: Existing task persistence and CRUD operations
- **External AI Service**: For natural language understanding and response generation
- **Database**: PostgreSQL (Neon) for conversation and message persistence

## Risks

1. **AI Response Quality**: Natural language understanding may misinterpret user intent. Mitigation: Require clarification for ambiguous requests.
2. **Latency**: AI service calls add response time. Mitigation: Set performance budgets and optimize context retrieval.
3. **Context Window Limits**: Large conversation histories may exceed AI context limits. Mitigation: Limit retrieved messages and summarize older context.

## Clarifications

### Session 2026-01-19

- Q: How should the system handle excessive chat message submissions from a single user? → A: Rate limit of 20 requests/minute per user, return friendly "Please slow down" message when exceeded
- Q: What timeout threshold and retry behavior should apply when the AI service is slow? → A: 30-second timeout, no automatic retry, user must manually resend message
- Q: Should the chatbot parse priority and due date from natural language input? → A: Parse due dates only (e.g., "tomorrow", "next Friday"); priority set via UI
- Q: Should users be able to clear/reset their conversation history? → A: Yes, single "Clear history" button removes all messages from current conversation
- Q: How should the system handle messages with multiple intents? → A: Execute all intents in sequence, return combined response

### Session 2026-01-04

- Q: When should the system create a new conversation vs. continue an existing one? → A: Single persistent conversation per user (never auto-expires)
- Q: When the AI service is unavailable, what happens to the user's message? → A: Persist message, return error, user can retry (message saved)
- Q: What level of detail should tool execution metadata include? → A: Standard: tool name + success/failure status + result summary
- Q: What level of observability should be built into the system? → A: Standard: structured logs with request IDs + key metrics (latency, tool calls)
- Q: What message role types should the Message entity support? → A: Three roles: user, assistant, tool (for tool execution results)

## Acceptance Signals

The following natural language commands should produce the expected tool executions:

| User Message | Expected Tool | Expected Behavior |
|--------------|---------------|-------------------|
| "Add buy groceries" | `add_task` | Creates task, confirms creation |
| "What's pending?" | `list_tasks` | Lists pending tasks |
| "Mark task 3 done" | `complete_task` | Marks task complete |
| "Delete groceries task" | `delete_task` | Removes task, confirms deletion |
| "Update task 2 title to 'Buy organic milk'" | `update_task` | Updates task title |

Chat should resume seamlessly after browser restart with full conversation history preserved.
