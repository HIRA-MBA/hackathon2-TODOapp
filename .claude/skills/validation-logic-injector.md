# Skill: Validation Logic Injector

## Description

Read Acceptance Criteria from /specs and inject validation rules into FastAPI request/response models, frontend form validation, and MCP tool inputs.

## Trigger

Invoke this skill when:
- Implementing validation for a feature
- User asks to "add validation" or "inject validation rules"
- After spec is created and before implementation
- When syncing validation across backend/frontend/MCP layers

## Core Rules (Non-Negotiable)

1. **Specs are the single source of truth** - All validation logic MUST trace back to an Acceptance Criterion in `/specs/<feature>/spec.md`
2. **No validation without spec reference** - Never add validation rules that are not explicitly defined in a spec
3. **Reject violations** - Halt and report any implementation that violates Acceptance Criteria

---

## Execution Flow

### Phase 1: Load Specification Context

1. **Identify target feature**:
   - Detect from current branch name or user input
   - Feature directory: `/specs/<feature-name>/`

2. **Load specification files**:
   - **REQUIRED**: Read `spec.md` for Acceptance Criteria
   - **OPTIONAL**: Read `data-model.md` for entity constraints
   - **OPTIONAL**: Read `contracts/` for API schemas

3. **Extract Acceptance Criteria**:
   Parse all scenarios matching:
   ```
   **Given** [precondition], **When** [action], **Then** [expected outcome]
   ```

   Also extract from:
   - **FR-XXX** functional requirements with MUST/SHOULD language
   - **Edge Cases** section for boundary conditions
   - **Key Entities** section for data constraints

### Phase 2: Build Validation Rules Registry

Create a structured registry:

```yaml
validation_rules:
  - id: VAL-001
    source: "spec.md#User Story 1 - Acceptance Scenario 1"
    field: "<field_name>"
    type: "<string|integer|email|date|enum|custom>"
    constraints:
      required: true|false
      min_length: <number>
      max_length: <number>
      min_value: <number>
      max_value: <number>
      pattern: "<regex>"
      enum_values: ["val1", "val2"]
    error_message: "<user-friendly message>"
    applies_to:
      backend: "<model.field>"
      frontend: "<form.field>"
      mcp: "<tool.parameter>"
```

### Phase 3: Inject Validation - FastAPI Backend

For each validation rule, inject into `backend/src/schemas/<resource>.py`:

```python
from pydantic import BaseModel, Field, field_validator

class TodoCreate(BaseModel):
    """Validation source: specs/<feature>/spec.md#FR-001"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Todo title - required, 1-200 chars"
    )
    # Source: spec.md#User Story 1 - Scenario 2

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Source: spec.md#FR-002"""
        if not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()
```

### Phase 4: Inject Validation - Frontend Forms

For each validation rule, inject into Next.js using Zod:

```typescript
import { z } from 'zod';

/**
 * Validation source: specs/<feature>/spec.md
 */
export const todoSchema = z.object({
  // Source: spec.md#FR-001 - title requirements
  title: z.string()
    .min(1, 'Title is required')
    .max(200, 'Title must be 200 characters or less')
    .transform(val => val.trim()),

  // Source: spec.md#Edge Cases - priority bounds
  priority: z.number()
    .int('Priority must be a whole number')
    .min(1, 'Priority must be at least 1')
    .max(5, 'Priority cannot exceed 5'),
});
```

### Phase 5: Inject Validation - MCP Tool Inputs

For each validation rule applicable to MCP tools:

```python
from pydantic import BaseModel, Field

class CreateTodoParams(BaseModel):
    """
    MCP Tool: create_todo
    Validation source: specs/<feature>/spec.md
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Todo title (required, 1-200 chars)"
    )
```

### Phase 6: Cross-Layer Consistency Check

Verify all three layers have identical validation:

| Rule ID | Field | Backend | Frontend | MCP | Status |
|---------|-------|---------|----------|-----|--------|
| VAL-001 | title.required | ✓ | ✓ | ✓ | PASS |
| VAL-002 | title.max_length | ✓ | ✓ | ✓ | PASS |

### Phase 7: Violation Detection

Scan for violations:

1. **Unauthorized validation** - Rules without spec references → REJECT
2. **Missing validation** - Spec criteria without implementation → WARN and generate
3. **Mismatches** - Different rules across layers → WARN

---

## Output

After execution, produce:
1. Validation Rules Registry (YAML)
2. Files Modified with line numbers
3. Cross-Layer Matrix
4. Violation Report (if any)
5. Spec Coverage Summary
