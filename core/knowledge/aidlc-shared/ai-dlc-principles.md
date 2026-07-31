# AI-DLC Methodology Principles

## Design Principle: Small Mob, Broad Agents

AI-DLC is built on the mob model — a small cross-functional group moving fast together. The agents mirror that. Rather than dozens of narrow specialists (which recreates waterfall handoff chains), we define **11 broadly capable agents** that each participate across multiple stages and phases, just as a real architect or developer would in a mob session.

Each agent carries context across stages because they are present throughout. This eliminates handoffs, reduces coordination overhead, and keeps the process agile.

## Core Principles

1. **User decides, AI executes** — Every material decision goes through an approval gate where the user reviews, revises, or overrides.
2. **Adaptive depth** — Simple projects skip heavyweight stages. Complex projects get full coverage. The workflow adapts to project needs.
3. **Traceable artifacts** — Every stage produces versioned markdown documents in `aidlc-docs/`, creating a complete decision record.
4. **Multi-role expertise** — Each stage is guided by domain-expert agent personas to ensure appropriate depth.
5. **No emergent behavior** — Agents follow prescribed protocols. Approval menus, completion messages, and state transitions are standardized.
6. **Questions before assumptions** — When in doubt, ask. Incomplete answers lead to poor designs.
7. **Contradiction detection** — Cross-check all answers for scope mismatches, risk mismatches, and technology conflicts.

## Five-Phase Structure

| Phase | Purpose | Key Outcome |
|-------|---------|-------------|
| **INITIALIZATION** | Bootstrap — state files, directory scaffold, workspace scan, routing | Configured workspace ready for workflow |
| **IDEATION** | Validate the initiative — intent, market, feasibility, scope, team | Approved initiative brief |
| **INCEPTION** | Elaborate — requirements, stories, design, architecture, units, delivery plan | Detailed execution plan |
| **CONSTRUCTION** | Build — functional design, NFRs, infrastructure, code, tests, CI | Working tested code |
| **OPERATION** | Deploy & operate — pipelines, environments, observability, incidents, feedback | Production system with monitoring |

## Scope System

Not every task requires every stage. Scopes (see the compiled scope grid or run `/aidlc --doctor` for the enabled set) determine which stages execute and at what depth.

## Self-Learning Guardrails

When a human corrects agent behavior, the correction becomes a permanent guardrail so the mistake never repeats. Guardrails are classified as organization-level (all projects) or project-level (this repo only).

## Principle: Resolve Once, Apply Everywhere

When an ambiguity is resolved through user interaction (Socratic Discovery, stage
questions, or clarification), record it as a durable resolution in the project memory
under `## Resolved Ambiguities`. On subsequent encounters of the same pattern, apply
the resolution without re-asking.

The conductor MUST check `## Resolved Ambiguities` in the active space's project.md
before presenting any clarification question. If the ambiguity matches a recorded
pattern, apply the resolution and note "(applied from resolved ambiguity YYYY-MM-DD)"
in the audit.

Source: arXiv 2607.26611, "Fewer Clarifications, Better Code" (CAPA, July 2026)

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

Source: arXiv 2607.22585, "The Scaffold Effect in Coding Agents" (July 2026)
