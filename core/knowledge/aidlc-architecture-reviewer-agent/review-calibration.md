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

## Borderline Task Difficulty

Research also shows borderline task difficulty is model-specific (Spearman ρ=0.75).
A task that one model handles easily may consistently trip another. When the same
code pattern fails repeatedly across retries, the issue is likely at the boundary
of the model's capability — flag it for human implementation rather than requesting
more retries.

Source: arXiv 2607.25130, "Learning from 53.6K Real-World Developer Edits" (July 2026)
