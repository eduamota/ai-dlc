# Visual Artifact Processing Guide

## When Visual Artifacts Are Provided

Users may provide mockups, wireframes, screenshots, or design files as input
during requirements analysis or user stories stages.

## Research-Calibrated Approach (arXiv 2607.22902, July 2026)

Multimodal AI generates backlogs from visual artifacts with these accuracy ranges:
- **Epics**: F1 ~66% (reliable enough to use as starting point)
- **User Stories**: F1 ~52% (needs human curation and refinement)
- **Tasks**: Low accuracy (always defer task decomposition to human)

26% of AI-generated items that don't exactly match intended requirements are
still useful to the development team — present them as "additional considerations."

## Recommended Technique: Compositional Chain-of-Thought (CCoT)

Process visual artifacts in layers (CCoT achieves up to 35% higher precision than
zero-shot):

1. **Screens** — Identify and name each distinct screen/view in the mockup
2. **Flows** — Map user navigation between screens (entry points, transitions)
3. **Components** — List interactive elements per screen (forms, buttons, lists)
4. **Epics** — Group related screens/flows into epics (highest confidence tier)
5. **Stories** — Write user stories per flow/interaction (medium confidence)
6. **Do NOT generate tasks** — Leave task decomposition to the human/delivery agent

## Output Format

Mark all mockup-derived items with their confidence tier:

```markdown
### Epic: User Authentication (source: visual-artifact, confidence: high)
- Story: As a user, I can log in with email and password (confidence: medium)
- Story: As a user, I can reset my forgotten password (confidence: medium)
- Additional consideration: Social login buttons visible in mockup (confidence: low)
```

## Presentation Rules

1. Present epics and stories as "draft — requires validation" not as definitive
   requirements
2. Items below story level → present as "suggested considerations" not definitive
3. Always note which items came from visual analysis vs. textual requirements
4. When architectural context is available (tech stack docs, API specs), include it —
   research shows precision improves up to 35% with architectural context
5. Accept that some generated items won't match exact requirements — 26% of
   "mismatches" are still useful, so present them rather than filtering silently
6. Never claim more than medium confidence on stories derived purely from visuals

## Integration with AI-DLC Stages

### During Requirements Analysis
- If user provides mockups as the primary input, use CCoT to generate initial
  requirements structured as epics and stories
- Mark the source as `visual-artifact` in requirements traceability
- Apply the standard requirements depth rules (minimal/standard/comprehensive)
  to the generated content — don't skip validation just because it came from AI

### During User Stories
- Cross-reference mockup-derived stories with textual requirements
- Identify gaps: stories visible in mockups but not in written requirements
- Identify conflicts: written requirements that contradict the visual design
- Present both to the user for resolution (feed into Resolved Ambiguities)

Source: arXiv 2607.22902, "How Well Can AI Generate Backlogs from App Mockups?"
(AIRE Workshop at IEEE RE 2026)
