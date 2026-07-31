---
name: refactor
depth: Minimal
keywords:
  - refactor
  - clean up
  - simplify
description: Clean up existing code
skeleton: off
---

# refactor scope

Minimal depth for cleaning up existing code without changing behaviour.
Like `bugfix` it skips ideation and operations, but it adds back
functional-design — a refactor reshapes structure, so the design of the
behaviour being preserved matters.

## Why these stages, why skip those

Refactoring is structure-preserving change on a known codebase. It runs
reverse-engineering (understand what exists), requirements-analysis
(pin down the behaviour to preserve), functional-design (the target
shape), then code-generation and build-and-test (apply and verify the
existing suite stays green). It skips the discovery and operation phases
for the same reason `bugfix` does — there is no new product and no new
deployment surface. One of the three incremental scopes that skip the
walking-skeleton ceremony.

## Membership

Keyword triggers: `refactor`, `clean up`, `simplify`. Initialization,
reverse-engineering, requirements-analysis, functional-design,
code-generation, and build-and-test execute; the rest is SKIP.

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
