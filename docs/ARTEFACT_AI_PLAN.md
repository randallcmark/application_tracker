# Artefact AI Plan

This is the resumable continuity reference for AI-assisted artefact analysis, selection,
tailoring, generation, and competency-evidence grounding.

## Current Direction

Artefact AI is analysis-first. Suggestions, tailoring, and drafts should be grounded in what the
system can inspect about the job, artefact, user profile, selected competency evidence, and visible
prior AI outputs.

Non-negotiables:

- AI is optional.
- AI output is visible and inspectable.
- AI does not silently mutate jobs, artefacts, profile data, competency evidence, notes, or
  workflow state.
- Historical outcomes are supporting context only, not proof of artefact quality.
- The app remains useful when no provider is configured.

## Completed Baseline

### Artefact Foundation

- Artefact library, metadata editing, reuse/linking, owner-scoped download, and saved-draft
  provenance are implemented.
- The document context ladder is implemented:
  - verified extracted text where available;
  - DOCX and best-effort host-backed Word/RTF/PDF extraction;
  - Gemini `provider_document` handoff for supported binary artefacts;
  - metadata-only fallback when no content can be inspected.

### Artefact AI

- Phase A is complete: visible `artefact_analysis`, hidden analysis reuse, job-text requirement
  inference, structured index signals, evidence phrasing, document-role guidance, and
  submission-pack coordination are implemented.
- Phase B is complete: job-scoped `artefact_suggestion`, deterministic shortlist, no-artefact
  fallback, and visible shortlisted links are implemented.
- Phase C is complete: per-artefact `tailoring_guidance`, selected artefact ownership checks,
  sparse fallback, extracted text support, and draft handoff metadata are implemented.
- Phase D is complete for current scope: visible `draft` outputs for resume, cover letter,
  supporting statement, and attestation are implemented, with explicit save-as-artefact promotion
  and no baseline overwrite.
- Phase E groundwork is implemented: conservative outcome-signal summaries exist as secondary
  supporting context.
- Phase G1-G2 are complete: artefact-local `Tailor` and `Draft ...` actions support an optional
  structured generation brief, and generated outputs keep that brief inspectable in metadata and
  saved-draft provenance.

### Competency Evidence

- S1 is complete: user-owned `CompetencyEvidence` schema, relationships, and owner-scoped service
  helpers are implemented.
- S2 is complete: compact `/competencies` library UI is implemented.
- S3 is complete: direct-library guided STAR create/refine prompts are implemented.
- S4 is complete: visible non-mutating `competency_star_shaping` AI output is implemented and
  linked by `source_context["competency_evidence_uuid"]`.

## Current Contracts

Existing visible AI output types:

- `artefact_analysis`
- `artefact_suggestion`
- `tailoring_guidance`
- `draft`
- `competency_star_shaping`

Current prompt contracts:

- `artefact_analysis_v1`
- `artefact_suggestion_v1`
- `artefact_tailoring_v1`
- `artefact_draft_v1`
- `competency_star_shaping_v1`

Current G4 source-context contract for generated artefact outputs:

```json
{
  "selected_competency_evidence_uuids": ["..."],
  "competency_evidence_contract": "competency_evidence_generation_context_v1"
}
```

No schema migration is required for first-pass competency evidence reuse.

## Active Next Milestone: G4 Evidence Reuse In Generation

Goal: allow the user to opt selected competency evidence into artefact-local `Tailor` and
`Draft ...` actions.

Implemented in first G4 slice:

- the existing generation brief modal includes a compact competency evidence selector for
  generative actions only;
- no evidence is selected by default, preserving previous behavior;
- selected evidence is resolved owner-scoped inside AI services;
- selected evidence summaries and latest `competency_star_shaping` output are included in
  tailoring/draft prompts where available;
- generated `tailoring_guidance` and `draft` outputs persist resolved evidence UUIDs in
  `source_context`;
- no competency evidence, artefact, job, or workflow state is mutated by generation.

Prompt rules:

- selected competency evidence is user-owned accomplishment context, not verified selected-artefact
  content;
- use it only where it helps ground examples;
- do not invent metrics, tools, dates, employers, or outcomes beyond saved evidence;
- do not imply the selected baseline artefact already contains the selected evidence unless the
  baseline content also supports it.

## Forward Plan

1. Small hooks to create competency evidence from job/artefact context are implemented. They open
   the manual evidence form with owner-scoped source context and require explicit save.
2. Add an explicit user action to save an AI-shaped STAR response back into competency evidence.
3. Consider richer evidence-link history only after source-context UUIDs prove insufficient.
4. Return to outcome-aware refinement only after competency evidence reuse has real usage.

## Regression Expectations

- Existing artefact suggestion, analysis, tailoring, draft, save-draft, competency library, and
  competency STAR shaping tests should remain green.
- `alembic check` should remain clean unless a later slice explicitly introduces schema.
- All AI work must preserve owner scoping and visible/non-mutating behavior.
