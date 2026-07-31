# Code Provenance Guide (TraceCoder Plugin)

## What Is Provenance?

Code provenance is the auditable record of *why* and *how* each line of generated
code came to be. It answers: "Who/what triggered this change? What was tried and
failed? What reasoning led to the final implementation?"

This plugin automatically captures snippet-level provenance via Kiro hooks.
Your role as the developer agent is to write code in a way that maximizes
provenance quality.

## How Provenance Is Captured

The hook system records 4 event types per session:

| Event | When | What's Recorded |
|-------|------|-----------------|
| `trigger` | User submits a prompt | Prompt text, classified type (bug, test_failure, instruction) |
| `edit` | Agent writes/modifies a file | File path, before/after snippets, scope (function/class), content hash |
| `test_result` | Agent runs tests | Command, pass/fail, specific failures |
| `explanation` | Agent turn ends | Agent's reasoning, attached to preceding edits |

## Best Practices for Provenance Quality

### 1. Write Focused Edits

Each file write should correspond to one logical change. Avoid large "dump
everything" writes when possible. Prefer:
- Write the model → write the service → write the handler
- NOT: write all three in one massive create

This gives each file its own provenance record with a clear scope.

### 2. Run Tests After Each Logical Step

When the code-generation plan has test steps, run them close to the code they
test. This creates `test_result` records that correlate to specific edits in
the causal chain.

Pattern: `code step → test step → next code step → test step`

### 3. Use Clear Commit-Style Reasoning

When the `stop` hook fires, your explanation is attached to all recent
unexplained edits. Write your turn-end reasoning as if it were a commit
message: what changed and why.

Good: "Added input validation to calculateShipping() because the NFR
requirements specify max weight of 150kg"

Bad: "Updated the file" or no explanation at all.

### 4. Scope Detection

The processor detects function/class scope from edited content. To maximize
scope accuracy:
- For Python: use `def` / `async def` / `class` at the start of lines
- For TypeScript/JavaScript: use `function`, `const name = () =>`, `class`
- Avoid writing anonymous/inline functions where named ones would be clearer

### 5. Repair Chain Documentation

When you retry a failed generation (test failed → re-edit):
- The causal chain captures this automatically (edit → test_fail → edit → test_pass)
- Your explanation should reference the previous failure: "Fixed by using async/await
  instead of callbacks — the previous approach caused a race condition in the test"

## Provenance and the Code Summary

When the code-generation stage produces `code-summary.md`, and the tracecoder
plugin is active, also produce `tracecoder-provenance-summary.md` documenting:

1. Which files have full provenance chains (trigger → edit → test → explanation)
2. Which files have repair cycles (multiple edit records)
3. Any gaps where files were written without provenance

## When Provenance Is Missing

If `.provenance/sessions/` is empty or doesn't exist:
- The TraceCoder hooks are not active for this session
- This is non-blocking — code generation continues normally
- Note the gap in the provenance summary if asked to produce one

## Research Basis

TraceCoder (arXiv 2607.26307, AGENTICS 2026) showed that ~30% of code snippets
carry traceable repair-event records in typical generation sessions. A complete
provenance chain enables:
- Audit compliance (who authorized each change, what was the trigger)
- Debugging regressions (trace back from a bug to the original reasoning)
- Trust calibration (files with repair chains had more scrutiny; single-pass
  files may need additional review)
