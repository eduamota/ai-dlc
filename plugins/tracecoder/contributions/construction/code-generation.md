---
target: code-generation
plugin: tracecoder
adds:
  produces:
    - tracecoder-provenance-summary
  sensors:
    - provenance
fragments:
  - anchor: after-step:5
    order: 100
  - anchor: in:Sensors
    order: 100
---

## fragment: after-step:5

### Step 5a (tracecoder): Provenance summary enrichment

After generating the code summary, enrich it with provenance metadata from
`.provenance/sessions/`. Create `tracecoder-provenance-summary.md` documenting:

1. **Edit count per file** — how many provenance records each generated file has
   (multiple records indicate repair cycles)
2. **Causal chain completeness** — for each edit record, whether it has:
   - A preceding `trigger` record (what drove the edit)
   - A following `test_result` record (whether tests validated it)
   - An attached `explanation` (the agent's reasoning)
3. **Scope coverage** — which functions/classes have provenance vs. which were
   generated without traceable scope detection
4. **Repair cycles** — files with >1 edit record (indicates the agent
   self-corrected; document the before/after chain)

Format:
```markdown
# Provenance Summary — {unit-name}

## Files with Full Provenance
| File | Edits | Triggers | Tests | Explanations |
|------|-------|----------|-------|--------------|
| src/service.ts | 2 | 1 | 2 | 2 |

## Repair Chains
- `src/service.ts`: 2 edits (initial generation → test failure → fix)

## Gaps
- (none, or list files without provenance records)
```

If `.provenance/sessions/` does not exist or is empty (hooks not active),
note this in the summary and skip — do not fail the stage.

## fragment: in:Sensors

The tracecoder plugin wires one ADVISORY sensor onto this stage:
`provenance` (reads `.provenance/sessions/*.jsonl`). It REPORTS whether
generated source files have corresponding provenance records — it does not
block code generation. A failing check means the TraceCoder hooks are not
active or a file was written outside the instrumented hook chain.
