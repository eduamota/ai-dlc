# Multi-Agent Topology Selection

## Research Basis

MSEval (arXiv 2607.27877, July 2026) tested 10 collaboration topologies on 10 full-stack
projects across 10 domains with periodic sync intervals and native CI/CD pipelines.

Key findings:
- Topology choice shifts quality scores by >30 points (equal to model capability differences)
- Structured pipelines converge fastest with highest quality
- Heavy managerial oversight (a "supervisor" reviewing/directing every step) degrades output
- Periodic sync intervals outperform continuous oversight

## Topology-to-Mode Mapping

| AI-DLC mode | MSEval equivalent | When to use |
|-------------|-------------------|-------------|
| `pipeline` | Sequential chain | Multi-step construction where each step builds on the previous (data → logic → API → tests). Fastest convergence. |
| `mob` | Mesh with bounded rounds | Conflicting requirements, architectural trade-offs, or design decisions where multiple perspectives must be weighed. Human breaks ties. |
| `subagent` (hub-spoke) | Star topology | Independent verification tasks. Each spoke is mutually blind — prevents groupthink. Good for review/validation. |
| `inline` | Solo expert | Single-domain work where coordination overhead exceeds benefit. No communication cost. |

## When to Use Each Mode

### pipeline (fastest convergence, highest quality)

Use when:
- Work has clear sequential dependencies (models before logic, logic before API)
- Each step's output is the next step's input
- Quality matters more than parallelism
- You want the cheapest token cost for multi-agent work

Avoid when:
- Steps are genuinely independent (use parallel subagent instead)
- Conflicting trade-offs need human arbitration (use mob)

### mob (best for design disagreements)

Use when:
- Architectural decisions with legitimate trade-offs
- Security vs. usability conflicts
- Multiple valid approaches exist and human judgment is needed to select
- The stage explicitly declares `support_agents` with conflicting domains

Avoid when:
- The work is straightforward implementation (wastes tokens on unnecessary debate)
- One domain expert clearly owns the decision

### subagent / hub-spoke (best for verification)

Use when:
- Each reviewer should be blind to others' assessments (prevents anchoring)
- The work needs independent validation from different angles
- Post-generation review (architecture, security, quality perspectives)

Avoid when:
- Reviewers would benefit from seeing each other's findings (use mob instead)
- Only one perspective is needed (use inline)

### inline (simplest, no coordination cost)

Use when:
- Single-domain expert work (one agent has all needed knowledge)
- Simple tasks where multi-agent coordination overhead exceeds benefit
- Support agents are "voices" the conductor adopts, not real dispatches

Avoid when:
- The work genuinely benefits from multiple independent perspectives
- There's a risk of blind spots that a second viewpoint would catch

## Anti-Patterns (From Research)

1. **Over-orchestration** — Using `mob` mode for straightforward implementation
   tasks wastes tokens and degrades quality. Use `pipeline` or `inline` instead.
2. **Supervisor bottleneck** — A manager agent that reviews every intermediate
   step before allowing the next slows convergence 2-3x. Let pipeline links
   hand off directly.
3. **Wrong mode for the task** — Using `inline` (single voice) for tasks that
   genuinely benefit from diverse perspectives (security review, UX decisions).
4. **Continuous oversight** — Checking after every micro-step is worse than
   periodic sync. Let agents work in focused bursts then sync.

## Decision Heuristic

Ask: "Does this stage need multiple independent perspectives?"
- **No** → `inline` or `pipeline`
- **Yes, with clear ordering** → `pipeline` (each link builds on the previous)
- **Yes, independent** → `subagent` (hub-spoke, mutually blind)
- **Yes, conflicting** → `mob` (mesh with human tiebreak in bounded rounds)

Source: arXiv 2607.27877, "An Empirical Study of Coordination Mode" (MSEval, July 2026)
