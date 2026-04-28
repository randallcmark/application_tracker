# Execution Plan: Artefact AI G4 Continuation

Status: Active

Owner: Agent

Created: 2026-04-28

Last Updated: 2026-04-28

## Goal

Continue the artefact-AI roadmap from the current G4 competency-evidence grounding milestone while preserving visible, non-mutating output and explicit provenance.

## Non-Goals

- hidden write-back into artefacts or competencies
- provider expansion beyond scoped AI work
- outcome-aware automation that bypasses user review

## Context

- `docs/ARTEFACT_AI_PLAN.md`
- `docs/COMPETENCY_EVIDENCE_PLAN.md`
- `docs/AI_READINESS.md`
- `docs/design/COMPETENCY_EVIDENCE_UX.md`
- `docs/product/user-journeys.md`

## Acceptance Criteria

- Competency evidence grounding remains opt-in and explicitly attributable.
- Any next slice stores resolved evidence references and output provenance visibly.
- Validation covers service behavior, routes, and fallback paths.

## Plan

1. Resume from the active G4 milestone rather than reopening completed phases.
2. Keep grounding, visible output, and save-back decisions separate and reviewable.
3. Extend tests and docs with each user-visible AI behavior change.
4. Record any model/provider constraints in docs alongside implementation.

## Progress Log

- 2026-04-28: Created active workstream from the artefact-AI and competency-evidence plans.

## Decisions

- Keep `docs/ARTEFACT_AI_PLAN.md` as the deep plan and use this file as the active resumable entry point.

## Validation

Commands to run before completion:

```sh
make test
```

## Risks

- AI-related workflow changes can blur visibility and provenance rules unless the non-mutation contract remains explicit in code and docs.
