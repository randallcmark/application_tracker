# Execution Plan: Artefact AI G4 Continuation

Status: Active

Owner: Agent

Created: 2026-04-28

Last Updated: 2026-05-02

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
5. Store richer evidence-link history alongside compact source-context provenance so future
   cross-job reporting, audit, and outcome-aware refinement can use structured data.

## Next Slice: Employer Competency Rubric Mapping

Goal: help the user compare pasted employer competencies, values, or assessment criteria against
their existing competency evidence without mutating evidence records.

Initial scope:

- pasted rubric text only;
- new visible `AiOutput` type: `employer_competency_mapping`;
- route and UI live in the competency library surface;
- output is Markdown-rendered and explicitly source-linked;
- low-confidence rubric input is labelled instead of overclaimed;
- no automatic evidence creation, mutation, or save-back.

Acceptance criteria:

- rubric text is treated as source data, not prompt instructions;
- users without an enabled AI provider get the existing visible error pattern;
- generated mapping is owner-scoped and visible in the competency library;
- sparse or vague rubric input is marked low confidence;
- missing evidence is reported as a gap instead of fabricated.

## Completed Slice: Richer Evidence-Link History

Goal: make competency evidence use queryable across jobs, artefact AI outputs, generated drafts, and
future review/outcome workflows without parsing JSON `source_context`.

Implementation shape:

- Add an `ai_output_competency_evidence_links` model/table.
- Include owner scoping, `ai_output_id`, `competency_evidence_id`, optional `job_id`, optional
  `artefact_id`, output type, draft kind, use intent, user-selected flag, and created timestamp.
- Store immutable snapshot fields from generation time: evidence UUID, title, competency, strength,
  result/action snippet, and latest STAR-shaping output id when used.
- Keep `source_context` compact refs for backwards-compatible display, but treat the link table as
  the query source once implemented.
- Add service helpers to create links only after owner-scoped evidence resolution.
- Add UI only where it helps later: evidence-card reuse history and AI-output provenance details.

Acceptance criteria:

- No hidden mutation of evidence, artefacts, jobs, notes, or workflow state.
- Foreign evidence cannot create a link for another user.
- Existing generated outputs without link rows continue to render using compact `source_context`.
- Tests cover migration/model relationships, owner boundaries, tailoring/draft generation links,
  and fallback rendering. Evidence-card reuse history remains future UI work.

Validation:

```sh
.venv/bin/alembic check
PYTHONPATH=. .venv/bin/pytest tests/test_ai_service.py tests/test_competency_routes.py tests/test_job_detail_routes.py
make test
```

## Progress Log

- 2026-04-28: Created active workstream from the artefact-AI and competency-evidence plans.
- 2026-05-01: Added explicit save-back for visible `competency_star_shaping` output. Generation
  remains non-mutating; the user must save shaped STAR fields back to the evidence record through a
  dedicated owner-scoped action.
- 2026-05-01: Added resolved competency evidence provenance for artefact-local tailoring and draft
  outputs. Generated outputs now keep compact `selected_competency_evidence_refs` metadata alongside
  the resolved UUID list, and the Job Workspace AI metadata panel renders the selected evidence
  titles/competencies/strengths visibly.
- 2026-05-01: Added model-backed `ai_output_competency_evidence_links` provenance. Tailoring and
  draft generation now create owner-scoped link rows with generation-time evidence snapshots while
  preserving the compact `source_context` display contract.
- 2026-05-02: Document handling prerequisites for employer rubric mapping are now in place:
  shared safe Markdown rendering is live, AI-output Markdown display is live, and artefact
  Markdown access has a formal no-schema service boundary.
- 2026-05-02: Implemented the first employer rubric mapping slice in the competency library.
  Pasted rubric text now generates visible `employer_competency_mapping` output against saved
  competency evidence, preserves pasted source text in output context, labels sparse input as low
  confidence, and leaves evidence non-mutating.

## Decisions

- Keep `docs/ARTEFACT_AI_PLAN.md` as the deep plan and use this file as the active resumable entry point.
- Keep compact `source_context` provenance for backwards-compatible display, but store the richer
  evidence-link table from the start because it is useful for audit and later reuse history.
- Keep the first employer rubric slice pasted-text only. Do not route uploaded rubric documents
  through this feature until document/source handling for those files is intentionally reused.

## Next Slices

1. Keep outcome-aware refinement deferred until evidence reuse has real usage.
2. Keep uploaded rubric documents deferred until artefact/document handling reuse is explicit.
3. Revisit employer rubric mapping only when real use shows gaps in preparation output, evidence
   selection, or source handling.

## Validation

Commands to run before completion:

```sh
make test
```

Latest focused validation:

```sh
.venv/bin/ruff check app/services/ai.py app/api/routes/job_detail.py tests/test_ai_service.py tests/test_job_detail_routes.py
PYTHONPATH=. .venv/bin/pytest tests/test_ai_service.py
PYTHONPATH=. .venv/bin/pytest tests/test_competency_routes.py
PYTHONPATH=. .venv/bin/pytest tests/test_ai_service.py::test_generate_job_artefact_tailoring_guidance_uses_selected_competency_evidence tests/test_ai_service.py::test_generate_job_artefact_draft_uses_selected_competency_evidence tests/test_job_detail_routes.py::test_job_detail_tailoring_guidance_accepts_generation_brief
```

## Risks

- AI-related workflow changes can blur visibility and provenance rules unless the non-mutation contract remains explicit in code and docs.
