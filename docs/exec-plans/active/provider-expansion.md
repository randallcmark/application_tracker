# Execution Plan: AI Provider Expansion

Status: Active

Owner: Agent

Created: 2026-04-28

Last Updated: 2026-04-28

## Goal

Extend provider execution beyond the current OpenAI-compatible and Gemini paths, with Anthropic and related provider-mode follow-on work treated as explicit slices.

## Non-Goals

- changing the visible-output contract
- mandatory AI configuration
- unrelated artefact or workspace redesign

## Context

- `docs/DELIVERY_PLAN.md`
- `project_tracker/PUBLIC_SELF_HOSTED_ROADMAP.md`
- `docs/AI_READINESS.md`
- `docs/agent/ai-feature-rules.md`

## Acceptance Criteria

- Provider additions are documented, validated, and owner-scoped.
- Error handling, disabled-provider behavior, and configuration docs remain explicit.
- Tests cover parsing, settings, and fallback behavior.

## Plan

1. Confirm next provider priorities from the roadmap.
2. Add one provider/mode slice at a time with validation and docs.
3. Preserve shared visibility, provenance, and failure-mode conventions.
4. Update routing docs if validation or risk posture changes.

## Progress Log

- 2026-04-28: Created active provider-expansion workstream.

## Decisions

- Treat provider expansion as separate from artefact-AI feature sequencing.

## Validation

Commands to run before completion:

```sh
make test
```

## Risks

- Provider-specific branching can make the AI surface harder to verify unless contracts stay centralized.
