# Code Generation Guide

## Context Loading Expectations

Context files (knowledge, memory, prior artifacts) aid consistency and traceability but
do NOT substitute for implementation skill. Research (arXiv 2607.27250, July 2026) shows
context strategy moves correctness by at most 10-15pp. The bottleneck is pattern
selection and exact wiring.

### When code generation fails, diagnose in this order:

1. **Implementation approach** — Was the right pattern selected? (repository, service,
   factory, adapter) Check code-generation-patterns.md
2. **Wiring** — Are dependencies connected correctly? (imports, DI, interface contracts)
3. **Framework API** — Was the framework/library API used correctly? (check docs)
4. **Context gap** — Only THEN consider whether missing information caused the failure

### What context IS good for:

- Consistency: naming conventions, file structure, import style
- Traceability: linking code to requirements and design decisions
- Guardrails: rules in memory/project.md preventing known mistakes
- Coordination: ensuring the unit implements the right stories

### What context is NOT good for:

- Fixing incorrect pattern selection (no amount of context fixes a wrong approach)
- Compensating for framework unfamiliarity (the agent either knows the API or doesn't)
- Overcoming model skill limitations (the model's training determines capability)

Source: arXiv 2607.27250, "Do Context Files Help Coding Agents?" (July 2026)

## Implementation Pattern Selection

Choose patterns based on the problem domain:

| Pattern | When to Use | Avoid When |
|---------|-------------|------------|
| **Repository** | Abstracting data access, multiple storage backends | Single database, simple CRUD only |
| **Service Layer** | Coordinating business logic across multiple repositories | Logic fits in a single model method |
| **Factory** | Complex object creation, conditional construction logic | Simple constructor suffices |
| **Strategy** | Runtime behavior variation (e.g., payment processing, notifications) | Only one algorithm exists |
| **Observer/Event** | Decoupling side effects from core logic (email, logging, cache invalidation) | Synchronous response required from all handlers |
| **Middleware/Pipeline** | Cross-cutting concerns (auth, logging, validation, rate limiting) | Single-purpose request handling |
| **Adapter** | Wrapping external APIs/SDKs behind a stable internal interface | Internal-only code with no external dependencies |

## Framework-Specific Generation Strategies

### General Principles (All Frameworks)
1. Scan existing code for conventions before generating new code
2. Match the project's import style (named vs. default, absolute vs. relative)
3. Follow the project's directory structure conventions
4. Use the project's established error handling pattern
5. Match existing naming conventions (camelCase, snake_case, PascalCase)

### Web API Implementation Checklist
For each endpoint, generate:
- [ ] Route definition with HTTP method and path
- [ ] Request validation (path params, query params, body schema)
- [ ] Authentication/authorization middleware
- [ ] Service call with error handling
- [ ] Response serialization with correct status code
- [ ] Error response formatting (consistent error envelope)

### Database Model Checklist
For each entity, generate:
- [ ] Model/schema definition with field types and constraints
- [ ] Indexes for queried fields and foreign keys
- [ ] Timestamps (created_at, updated_at) where appropriate
- [ ] Soft delete support if specified in requirements
- [ ] Migration file for schema changes
- [ ] Seed data for development/testing if applicable

## Retry Strategy

When a code generation step fails (sensor violation, test failure, type error):

### Strategy by model capability

| Model tier | On failure | Rationale |
|-----------|-----------|-----------|
| ≤7B params | Fresh regeneration WITHOUT showing failed output | Anchoring bias (33-68% reproduce identical failures) |
| >7B params | Include error message + plan step only (NOT failed code) | Larger models benefit from error context but anchor on full code |
| Any model, 3rd failure | Escalate to human | Structural problem beyond retry |

### What to include in a retry prompt

✅ Include:
- The original plan step text
- The error/failure message (exact text)
- The constraint that was violated (sensor rule, type, test assertion)
- Project conventions from memory layers

❌ Do NOT include:
- The full previously-generated code
- The full file contents that failed
- Multiple previous failed attempts stacked

### Token efficiency

Blind resampling (fresh attempt) uses 2.5-5.5x fewer tokens than repair-with-feedback
loops. When cost is a concern, prefer fresh generation over iterative fix cycles.

### Maximum retries

- 3 attempts maximum per plan step before escalating
- Track retry count in the code-generation-plan.md checkboxes (note attempt number)
- If the same step fails 3 times, present the failures to the user as a structured
  question with options: simplify the step, split into sub-steps, or skip with a TODO

Source: arXiv 2607.26117, "Try Again, Don't Look Back" (July 2026)

## Brownfield Modification Best Practices

When modifying existing codebases (most common scenario):

### Before Writing Code
1. **Map the change surface**: Identify all files that will be touched
2. **Trace the call chain**: Follow the execution path from entry point to persistence
3. **Check for tests**: Find existing tests that cover the area being modified
4. **Identify conventions**: Note patterns used in surrounding code

### Modification Rules
- Match the surrounding code's style exactly, even if you prefer another style
- Do not refactor unrelated code in the same change
- Preserve existing function signatures when adding optional parameters
- Add backward-compatible defaults for new configuration
- Update existing tests to cover the changed behavior
- Add new tests for new behavior

### Common Pitfalls
- Breaking existing imports by renaming or moving files
- Changing a function's return type without updating all callers
- Adding required parameters to public APIs
- Modifying shared utility functions without checking all consumers
- Forgetting to update database migrations for schema changes

## Testing Patterns

### Unit Test Structure
Follow the Arrange-Act-Assert (AAA) pattern:
```
// Arrange: Set up preconditions and inputs
// Act: Execute the unit under test
// Assert: Verify the expected outcome
```

### What to Test per Unit

| Unit Type | Test Focus |
|-----------|------------|
| Service/Use Case | Business logic correctness, edge cases, error handling |
| Controller/Handler | Request parsing, response format, status codes, auth checks |
| Repository/DAO | Query correctness (use in-memory DB or test containers) |
| Utility/Helper | Input/output mapping, boundary values, null/undefined handling |
| Middleware | Pass-through behavior, rejection conditions, header manipulation |

### Test Data Strategy
- Use factories/builders for complex objects (avoid raw JSON literals)
- Isolate test data per test (no shared mutable fixtures)
- Use meaningful test data that reflects real scenarios
- Name test variables to express their purpose (`expiredToken`, `adminUser`, `emptyCart`)

## Code Quality Standards

### Function Design
- Maximum 30 lines per function (excluding tests)
- Single responsibility: one function does one thing
- Maximum 3 parameters; use an options object for more
- Return early to avoid deep nesting (guard clauses)
- Pure functions where possible (no side effects)

### Error Handling
- Fail fast: validate inputs at function entry
- Use typed/custom errors for domain-specific failures
- Never swallow exceptions silently (at minimum, log them)
- Propagate errors with context (wrap, do not replace)
- Distinguish between recoverable errors (retry) and fatal errors (abort)

### Naming Conventions
- Functions: verb + noun (`createUser`, `validateInput`, `calculateTotal`)
- Booleans: `is`/`has`/`should` prefix (`isActive`, `hasPermission`)
- Collections: plural nouns (`users`, `orderItems`)
- Constants: UPPER_SNAKE_CASE for true constants
- Avoid abbreviations unless universally understood (`id`, `url`, `api`)

### File Organization
- One primary export per file (class, function, or component)
- Group related files by feature/domain, not by technical layer
- Keep test files adjacent to source files (or in a mirrored `__tests__` directory)
- Index files only for public API re-exports, never for internal organization

## Automation-Friendly Code Rules

### data-testid Attributes
Add `data-testid` attributes to all interactive elements to support automated testing (E2E, integration, accessibility audits):

- **Required on**: buttons, inputs, links, form elements, modals, dropdowns, tabs, and other interactive containers
- **Naming convention**: `{component}-{element-role}` (e.g., `login-form-submit-button`, `user-profile-edit-link`, `settings-modal-close`)
- **Rules**:
  - Use lowercase kebab-case
  - Keep `data-testid` values stable across code changes — do not tie them to dynamic state or auto-generated IDs
  - Avoid dynamic or auto-generated IDs (e.g., `button-${index}`) — use semantic names instead
  - Group related elements under a container `data-testid` (e.g., `user-table` wrapping `user-table-row-{id}`)
  - Apply to both visible and programmatically interactive elements (e.g., hidden file inputs triggered by a button)
