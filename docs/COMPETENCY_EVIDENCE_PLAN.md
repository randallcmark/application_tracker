# Competency Evidence Plan

This document is the resumable implementation reference for the user-owned competency evidence
library and guided STAR workflow.

## Product Intent

Competency evidence is a reusable user asset. It captures accomplishments and examples that can
support interviews, cover letters, supporting statements, attestations, and later artefact drafting.

It is not owned by a job. A job, artefact, or AI output can inspire an entry, but the entry belongs
to the user and can be reused across future applications.

## Guardrails

- Keep entries user-owned and owner-scoped.
- Keep STAR structure inspectable: situation, task, action, result.
- Support partial entries; many examples start as seeds.
- Do not silently create or update entries from AI output.
- Keep historical outcomes as secondary context, not proof that an example is good.
- Keep UI compact: cards, focused modals, and small hooks from existing surfaces.

## Roadmap

### S1: User-Owned Evidence Foundation

Goal: add the data and service foundation for a competency evidence library.

Implementation targets:

- add a `competency_evidence` table;
- add a SQLAlchemy model and owner relationship;
- support fields for title, competency, STAR sections, notes, strength, tags, source pointers, and
  last-used timestamp;
- add owner-scoped service helpers for create, list, get, and update;
- add focused tests for owner boundaries and update semantics.

Status: implemented for the model, migration, owner-scoped service helpers, and service tests. UI
and AI workflows begin in later slices.

### S2: Compact Library UI

Goal: expose a calm user-owned evidence library.

Implementation targets:

- add a compact library surface;
- render cards with title, competency, strength, result snippet, tags, and source signal;
- allow basic create/edit without AI;
- avoid long narrative walls by segmenting STAR fields.

Status: implemented. The protected `/competencies` surface now renders a compact owner-scoped
library, create panel, editable evidence cards, source signals, result snippets, tags, and
expandable STAR detail. It is linked from the protected user menu rather than primary navigation so
the library stays available without making the main workflow heavier.

### S3: Guided Creation And Refinement

Goal: help the user build or improve one entry through short prompts.

Trigger sources:

- direct library action;
- Job Workspace role context;
- artefact context;
- AI draft or tailoring context.

Question pattern:

1. What competency or theme does this example demonstrate?
2. What was the situation?
3. What were you responsible for?
4. What did you do?
5. What changed as a result?
6. What makes this credible?
7. Where is this most useful?

Status: implemented for direct library action. The create panel and each existing entry's
refinement form now use grouped prompts for theme, STAR evidence, credibility, and reuse. This is
still manual and explicit: no AI output creates or mutates evidence.

### S4: AI-Assisted STAR Shaping

Goal: turn partial evidence into concise, truthful STAR responses.

Outputs remain visible and non-mutating unless the user explicitly saves edits.

Status: implemented for direct library action. Each evidence card exposes `Shape with AI`, which
creates a visible `competency_star_shaping` `AiOutput` linked by `source_context` using
`competency_evidence_uuid` and prompt contract `competency_star_shaping_v1`. The saved evidence
record is not edited by generation. A separate explicit `Save shaped STAR to evidence` action can
copy the visible AI-shaped STAR fields back into the evidence record after owner and source-context
checks.

### S5: Opt-In Reuse In Artefact Generation

Goal: let the user select relevant competency evidence when generating or tailoring artefacts.

Use cases:

- cover letter: one or two concise examples;
- supporting statement: fuller criteria-led evidence;
- attestation: factual evidence only;
- interview prep: concise STAR answers.

Status: implemented for first-pass generation reuse and source hooks. Artefact-local `Tailor` and
`Draft ...` flows can opt selected evidence into generation without schema changes, generated AI
outputs keep visible resolved evidence provenance in metadata, generated output/evidence links are
stored as queryable generation-time snapshots, and Job Workspace now links to a prefilled manual
evidence form from role or artefact context. Evidence is only created after explicit user save.

### S6: Employer Competency Rubric Mapping

Goal: help the user prepare honestly for a specific interview by mapping employer-provided
competencies, rubrics, values, behaviours, or assessment criteria against existing competency
evidence.

Dependencies:

- shared safe Markdown rendering;
- AI-output Markdown display;
- document handling foundation;
- existing competency evidence library and evidence-link provenance.

Initial scope:

- pasted employer rubric or interview brief text only;
- AI output type: `employer_competency_mapping`;
- structured preparation output with competency name, employer wording, expected behaviours, best
  evidence, match strength, gaps, suggested sources, and recommended next action;
- visible source-linked output, not automatic evidence creation or mutation;
- uploaded rubric documents only after artefact Markdown representation or existing extraction
  paths can be reused safely.

Acceptance criteria:

- employer material is treated as source data, not prompt instructions;
- sparse or vague rubric input is labelled as low confidence;
- missing evidence is reported as a gap instead of fabricated;
- user-owned evidence and artefacts remain owner-scoped;
- suggested next actions are preparation-oriented and explicit.

Status: implemented for the first pasted-text slice. The competency library now supports visible
`employer_competency_mapping` output from pasted employer rubric text, labels sparse input as
low confidence, renders the mapping through the shared Markdown viewer, keeps evidence
non-mutating, and now places the mapping beside a full-width creation workspace rather than in a
narrow sidebar. Uploaded rubric documents remain deferred until artefact/document handling for
those sources is intentionally reused.

## Data Model, S1

`CompetencyEvidence`

- `uuid`
- `owner_user_id`
- `title`
- `competency`
- `situation`
- `task`
- `action`
- `result`
- `evidence_notes`
- `strength`: `seed`, `working`, or `strong`
- `tags`: stored as simple text in S1, structured later if needed
- `source_kind`
- `source_job_id`
- `source_artefact_id`
- `source_ai_output_id`
- `last_used_at`
- timestamps

S1 deliberately avoids many-to-many link tables. Later slices can add richer link history once the
library behaviour is proven.

## UX Notes

- Entry cards should be compact by default.
- Full STAR fields should be segmented and expandable.
- Creation/refinement should use a modal or focused work panel, not a long dashboard form.
  The current library now uses a full-width work panel with the saved library rendered below it.
- Existing surfaces should add small hooks only:
  - `Create evidence from this role`
  - `Create evidence from this artefact`
  - `Use evidence in draft`

## Resume Protocol

When resuming:

1. Start here and confirm the active S-slice.
2. Preserve user ownership and visible/non-mutating AI behaviour.
3. Treat S1 service/model work and S2 manual UI as landed foundations.
4. Update this document, `docs/ARTEFACT_AI_PLAN.md`, `docs/DELIVERY_PLAN.md`, and the public
   roadmap when a slice lands.
