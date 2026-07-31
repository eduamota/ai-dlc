# Category 1 Research Implementation Plans

**Source:** `~/Projects/research/docs/arxiv-sdlc-category1-coding-agents-detailed.md`
**Target project:** AI-DLC Workflows v2 (`~/Projects/ai-dlc/`)
**Status:** TraceCoder provenance plugin ✅ complete (branch `feat/tracecoder-plugin`)

---

## Plan 1: Blind Resampling Retry Strategy

**Paper:** "Try Again, Don't Look Back" (arXiv 2607.26117)
**Finding:** For models ≤7B, blind resampling (fresh attempt without showing failure) beats self-repair by 6.1pp and uses 2.5-5.5x fewer tokens. Models anchor on their own failures 33-68% of the time.

### What to implement

Add a retry strategy rule that the developer agent follows when code generation fails sensor checks or tests.

### Files to create/modify

| File | Action | Content |
|------|--------|---------|
| `core/memory/org.md` | Append to `## Corrections` | Rule about retry strategy |
| `core/knowledge/aidlc-developer-agent/code-generation-guide.md` | Add new section `## Retry Strategy` | Detailed guidance with model-size branching |

### Implementation detail

**In `core/memory/org.md` under `## Corrections`:**
```markdown
- When code-generation fails and the subagent retries, do NOT include the full previously-failed
  code in the retry prompt. Include only the error message, the original plan step, and the
  constraint violated. Anchoring on previous failures causes reproduction of near-identical
  broken code 33-68% of the time. (source: arXiv 2607.26117, July 2026)
```

**In `core/knowledge/aidlc-developer-agent/code-generation-guide.md`, new section:**
```markdown
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
```

### Effort: Low
### Branch name: `feat/retry-strategy`

---

## Plan 2: Multi-Agent Topology Guide

**Paper:** "An Empirical Study of Coordination Mode in From-Scratch Multi-Agent Coding" (arXiv 2607.27877, MSEval)
**Finding:** Organizational topology rivals model capability — varying topology shifts scores by >30 points. Structured pipelines converge fastest with highest quality; heavy managerial oversight degrades performance.

### What to implement

AI-DLC v2 already supports 4 topologies (`mode: inline | subagent | pipeline | mob`). Add a knowledge file that documents when to choose which, grounded in the research.

### Files to create/modify

| File | Action | Content |
|------|--------|---------|
| `core/knowledge/aidlc-shared/topology-selection.md` | Create | When to use each communication mode |

### Implementation detail

```markdown
# Multi-Agent Topology Selection

## Research basis

MSEval (arXiv 2607.27877, July 2026) tested 10 collaboration topologies on full-stack
projects. Key findings:
- Topology choice shifts quality scores by >30 points (equal to model capability differences)
- Structured pipelines converge fastest with highest quality
- Heavy managerial oversight (a "supervisor" reviewing/directing every step) degrades output
- Periodic sync intervals outperform continuous oversight

## Topology-to-mode mapping

| AI-DLC mode | MSEval equivalent | When to use |
|-------------|-------------------|-------------|
| `pipeline` | Sequential chain | Multi-step construction where each step builds on the previous (data → logic → API → tests). Fastest convergence. |
| `mob` | Mesh with bounded rounds | Conflicting requirements, architectural trade-offs, or design decisions where multiple perspectives must be weighed. Human breaks ties. |
| `subagent` (hub-spoke) | Star | Independent verification tasks. Each spoke is mutually blind — prevents groupthink. Good for review/validation. |
| `inline` | Solo expert | Single-domain work where coordination overhead exceeds benefit. |

## Anti-patterns (from research)

1. **Over-orchestration** — Using `mob` mode for straightforward implementation
   tasks wastes tokens and degrades quality. Use `pipeline` or `inline` instead.
2. **Supervisor bottleneck** — A manager agent that reviews every intermediate
   step before allowing the next slows convergence. Let pipeline links hand off
   directly.
3. **Wrong mode for the task** — Using `inline` (single voice) for tasks that
   genuinely benefit from diverse perspectives (security review, UX decisions).

## Decision heuristic

Ask: "Does this stage need multiple independent perspectives?"
- No → `inline` or `pipeline`
- Yes, with clear ordering → `pipeline`
- Yes, independent → `subagent` (hub-spoke)
- Yes, conflicting → `mob` (mesh with human tiebreak)
```

### Effort: Low
### Branch name: `feat/topology-guide`

---

## Plan 3: Harness > Model Principle

**Paper:** "The Scaffold Effect in Coding Agents" (arXiv 2607.22585)
**Finding:** The harness introduces up to 40x difference in tokens per task while model pass-rate varies only 0-8pp. Failure patterns are harness-level biases that replicate across models.

### What to implement

Add a framework principle and a practical implication for token budgeting.

### Files to create/modify

| File | Action | Content |
|------|--------|---------|
| `core/knowledge/aidlc-shared/ai-dlc-principles.md` | Append new principle | "Harness Over Model" |

### Implementation detail

**Append to `core/knowledge/aidlc-shared/ai-dlc-principles.md`:**

```markdown
## Principle: Harness Over Model

Research demonstrates that scaffold/harness design dominates model choice by up to 40x
in token efficiency, while model selection varies pass-rate by only 0-8 percentage points
(arXiv 2607.22585, July 2026). Failure patterns are harness-level biases that replicate
identically across different models.

### Implications for AI-DLC

1. **Architecture validates the approach** — AI-DLC's harness-neutral core (`core/`) +
   per-harness thin surfaces (`harness/`) is the correct architecture. The methodology
   (stages, agents, sensors, learnings) matters more than which model executes it.

2. **When a stage fails, check the harness first** — If code-generation consistently fails
   on a particular pattern, the fix is more likely in the stage protocol, knowledge files,
   or sensor configuration than in switching models.

3. **Token budgets are harness-determined** — Set token expectations per-stage based on
   harness behavior, not model capabilities. A 40x variance means "this task should take
   ~X tokens" is a harness property.

4. **Evaluate harness-model pairs** — Benchmarking a model alone is misleading. The
   relevant comparison is (harness + model) vs (harness + model) under the same token
   and latency budget.
```

### Effort: Low
### Branch name: `feat/harness-principle`

---

## Plan 4: Context ≠ Correctness Calibration

**Paper:** "Do Context Files Help Coding Agents?" (arXiv 2607.27250)
**Finding:** Context files (CLAUDE.md, AGENTS.md) don't measurably move correctness (bounded ≤10-15pp). Agents fail on implementation skill — feature design, pattern selection, exact wiring — not missing repository knowledge.

### What to implement

Add calibration guidance to the developer agent so it doesn't over-rely on context loading when code fails.

### Files to create/modify

| File | Action | Content |
|------|--------|---------|
| `core/knowledge/aidlc-developer-agent/code-generation-guide.md` | Add section `## Context Loading Expectations` | Calibration guidance |

### Implementation detail

```markdown
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
```

### Effort: Low
### Branch name: `feat/context-calibration`

---

## Plan 5: 31% Removal Rate Awareness

**Paper:** "Learning from 53.6K Real-World Developer Edits of AI-Generated Code" (arXiv 2607.25130, DECODE)
**Finding:** 31% of AI code completions get entirely removed by developers. Most edits occur within 15 minutes of acceptance.

### What to implement

Add awareness to the architecture reviewer agent and the code-generation completion message.

### Files to create/modify

| File | Action | Content |
|------|--------|---------|
| `core/knowledge/aidlc-architecture-reviewer-agent/review-calibration.md` | Create | Reviewer heuristics calibrated by the research |
| `core/aidlc-common/stages/construction/code-generation.md` | Modify Step 7 completion message comment | Add awareness note |

### Implementation detail

**New file `core/knowledge/aidlc-architecture-reviewer-agent/review-calibration.md`:**

```markdown
# Review Calibration

## AI-Generated Code Removal Rate

Research (arXiv 2607.25130, DECODE dataset, 53.6K real edits) shows:
- 31% of AI-generated code completions are entirely removed by developers
- Most edits occur within 15 minutes of initial acceptance
- Acceptance at generation time does NOT equal correctness

## Heightened Scrutiny Areas

When reviewing generated code, apply extra attention to:

1. **Template-like output** — Code that exactly matches common patterns without
   domain-specific adaptation. May be "generic correct" but wrong for this context.
2. **Boundary code** — API handlers, middleware, integration points where wiring
   errors are most common (request/response mapping, error handling at edges).
3. **Functions with no test coverage in the plan** — If a function wasn't tested,
   it hasn't been validated. Flag for the approval gate.
4. **Configuration and environment code** — Connection strings, feature flags,
   env-specific behavior. High removal rate in practice.
5. **Code the developer agent marked as "uncertain"** in the code summary — If
   the generating agent hedged, the reviewer should investigate.

## Review Posture

Do NOT rubber-stamp. The 31% removal rate means roughly 1 in 3 generated
artifacts needs meaningful human modification. The reviewer's job is to catch
the subset that is structurally wrong (not just stylistically different) before
it reaches the human approval gate.
```

### Effort: Low
### Branch name: `feat/review-calibration`

---

## Plan 6: Personalized Ambiguity Resolution

**Paper:** "Fewer Clarifications, Better Code" (arXiv 2607.26611, CAPA)
**Finding:** Using a developer's past resolved sessions to resolve recurring ambiguities eliminates clarification cycles.

### What to implement

AI-DLC v2 already has the learnings ritual (§13) which writes resolved decisions to `project.md`/`team.md`. Strengthen by adding a `## Resolved Ambiguities` section to the memory template so the pattern is explicit.

### Files to create/modify

| File | Action | Content |
|------|--------|---------|
| `core/memory/templates/memory-template.md` | Add section | `## Resolved Ambiguities` with format guidance |
| `core/knowledge/aidlc-shared/ai-dlc-principles.md` | Append | Principle about checking resolved ambiguities before asking |

### Implementation detail

**Add to the memory template (project.md pattern):**

```markdown
## Resolved Ambiguities

<!-- When a recurring ambiguity is resolved through Socratic Discovery or stage questions,
     record it here. Format:
     - "<ambiguity pattern>" → "<chosen resolution>" (resolved YYYY-MM-DD)
     
     The conductor checks this section BEFORE presenting a clarification question.
     If a matching pattern exists, apply the resolution silently rather than re-asking.
     
     Research (arXiv 2607.26611, CAPA) shows this eliminates 40-60% of repeated
     clarification cycles across sessions. -->
```

**Append to principles:**

```markdown
## Principle: Resolve Once, Apply Everywhere

When an ambiguity is resolved through user interaction, record it as a durable
resolution in the project memory. On subsequent encounters of the same pattern,
apply the resolution without re-asking. (arXiv 2607.26611, CAPA, July 2026)

The conductor MUST check `## Resolved Ambiguities` in the active space's
project.md before presenting any clarification question. If the ambiguity
matches a recorded pattern, apply the resolution and note "(applied from
resolved ambiguity YYYY-MM-DD)" in the audit.
```

### Effort: Low
### Branch name: `feat/ambiguity-resolution`

---

## Plan 7: NFI/Refactoring Special Handling

**Paper:** "SWE-NFI: Studying and Benchmarking Coding Agents for Non-Functional Improvements" (arXiv 2607.27409)
**Finding:** Agents achieve 70% functional correctness but score 0.0-1.3 on structural code improvements. NFI work (refactoring, performance, quality) is where agents are weakest.

### What to implement

Add refactoring-specific rules to the `aidlc-refactor.md` scope file.

### Files to create/modify

| File | Action | Content |
|------|--------|---------|
| `core/scopes/aidlc-refactor.md` | Append section | NFI-specific constraints |

### Implementation detail

**Append to `core/scopes/aidlc-refactor.md`:**

```markdown
## Non-Functional Improvement Constraints

Research (arXiv 2607.27409, SWE-NFI, July 2026) shows AI agents score near-zero
on structural code improvements while achieving 70% on functional correctness.
Refactoring is the hardest task class for current AI agents.

### Mandatory rules for refactor scope:

1. **Diff-first review** — Present ALL structural changes as unified diffs for
   human review BEFORE applying. Never batch-apply refactoring changes.
2. **Atomic steps** — Decompose into the smallest independently verifiable
   refactoring steps. One rename, one extract, one move per step.
3. **Test after every step** — Run the full test suite after EACH atomic step.
   Do not batch multiple refactorings then test. A failure in step 5 of 10 is
   impossible to diagnose if steps 1-4 weren't individually verified.
4. **Never combine with behavior changes** — A refactoring step that also changes
   behavior is not a refactoring. Split into: (a) refactor with same behavior,
   (b) behavior change in clean code.
5. **Prefer sensor-verifiable refactorings** — Choose refactorings the linter or
   type-checker can verify (extract function, rename, change type signature)
   over those requiring human judgment ("improve readability").
6. **Per-file human confirmation for judgment calls** — For refactorings that
   sensors cannot verify (rewrite for clarity, restructure for cohesion),
   present each file change individually and require explicit approval.
7. **Conservative default** — When uncertain whether a refactoring improves
   quality, do not apply it. The research shows agents' structural judgment
   is unreliable; err toward preserving existing structure.
```

### Effort: Low
### Branch name: `feat/nfi-constraints`

---

## Plan 8: Backlog from Visual Artifacts

**Paper:** "How Well Can AI Generate Backlogs from App Mockups?" (arXiv 2607.22902)
**Finding:** GPT-4o generates epics/stories from mockups at F1 52-66%. Tasks are hardest. 26% of "false positives" are still useful.

### What to implement

Add knowledge for the product agent about processing visual artifacts during requirements/stories.

### Files to create/modify

| File | Action | Content |
|------|--------|---------|
| `core/knowledge/aidlc-product-agent/visual-artifact-processing.md` | Create | Guide for mockup → backlog generation |

### Implementation detail

```markdown
# Visual Artifact Processing Guide

## When visual artifacts are provided

Users may provide mockups, wireframes, screenshots, or design files as input
during requirements analysis or user stories stages.

## Research-calibrated approach (arXiv 2607.22902, July 2026)

Multimodal AI generates backlogs from visual artifacts with these accuracy ranges:
- **Epics**: F1 ~66% (reliable enough to use as starting point)
- **User Stories**: F1 ~52% (needs human curation and refinement)
- **Tasks**: Low accuracy (always defer task decomposition to human)

26% of AI-generated items that don't exactly match intended requirements are
still useful to the development team — present them as "additional considerations."

## Recommended technique: Compositional Chain-of-Thought (CCoT)

Process visual artifacts in layers (CCoT achieves 35% higher precision than zero-shot):

1. **Screens** — Identify and name each distinct screen/view in the mockup
2. **Flows** — Map user navigation between screens (entry points, transitions)
3. **Components** — List interactive elements per screen (forms, buttons, lists)
4. **Epics** — Group related screens/flows into epics (highest confidence tier)
5. **Stories** — Write user stories per flow/interaction (medium confidence)
6. **Do NOT generate tasks** — Leave task decomposition to the human/delivery agent

## Output format

Mark all mockup-derived items with their confidence tier:

```markdown
### Epic: User Authentication (source: visual-artifact, confidence: high)
- Story: As a user, I can log in with email and password (confidence: medium)
- Story: As a user, I can reset my forgotten password (confidence: medium)
- Additional consideration: Social login buttons visible in mockup (confidence: low)
```

## Presentation rules

1. Present epics and stories as "draft — requires validation"
2. Items below story level → present as "suggested considerations" not definitive
3. Always note which items came from visual analysis vs. textual requirements
4. When precision context is available (architectural docs, tech stack), include
   it — research shows precision improves up to 35% with architectural context
5. Accept that some generated items won't match exact requirements — 26% of
   "mismatches" are still useful, so present them rather than filtering silently
```

### Effort: Low
### Branch name: `feat/visual-backlog`

---

## Summary & Execution Order

| # | Plan | Branch | Dependencies | Priority |
|---|------|--------|--------------|----------|
| 1 | Retry Strategy | `feat/retry-strategy` | None | High (cost + quality) |
| 2 | Topology Guide | `feat/topology-guide` | None | Medium (informational) |
| 3 | Harness > Model | `feat/harness-principle` | None | Low (principle) |
| 4 | Context ≠ Correctness | `feat/context-calibration` | None | Medium (behavior change) |
| 5 | 31% Removal Awareness | `feat/review-calibration` | None | Medium (reviewer quality) |
| 6 | Ambiguity Resolution | `feat/ambiguity-resolution` | None | Medium (UX improvement) |
| 7 | NFI Constraints | `feat/nfi-constraints` | None | High (prevents bad output) |
| 8 | Visual Backlog | `feat/visual-backlog` | None | Low (new capability) |

**Recommended batch:** Plans 1 + 7 first (highest impact on code quality), then 4 + 5 + 6 (behavioral improvements), then 2 + 3 + 8 (informational/new capabilities).

All plans are independent — no ordering constraints between them.
