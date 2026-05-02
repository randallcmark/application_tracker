# Execution Plan: Document Handling Foundation

Status: Active planning

Owner: Agent

Created: 2026-05-02

Last Updated: 2026-05-02

## Goal

Establish source-preserving, Markdown-first document handling before adding more document-heavy AI,
artefact, rubric, search, export, or background automation workflows.

## Non-Goals

- schema changes
- broad renderer or editor expansion beyond the first shared safe Markdown slice
- AI prompt or provider changes
- document extraction subsystem changes
- search, FTS, embeddings, or export implementation
- changes to upload/download behavior

## Context

- `docs/DOCUMENT_HANDLING_STRATEGY.md`
- `docs/DOCUMENT_HANDLING_ARCHITECTURE.md`
- `docs/DOCUMENT_HANDLING_TASK_MAP.md`
- `docs/architecture/decisions/2026-05-02-markdown-first-document-handling.md`
- `docs/roadmap/task-map.md`
- `docs/agent/ai-feature-rules.md`
- `docs/agent/security-rules.md`

## Acceptance Criteria

- Document handling is visible as roadmap item 6 after AI provider expansion.
- Supporting docs and ADR are linked from architecture and agent indexes.
- The free-text Markdown rendering audit is complete and preserved in
  `docs/exec-plans/completed/free-text-markdown-rendering-audit.md`.
- A shared safe Markdown renderer covers AI outputs and Job Workspace descriptions through one
  sanitized helper.
- A no-schema artefact detail view now covers source-first Markdown/text previews plus derived
  extracted-text previews for supported documents.
- The no-schema artefact phase now has a formal Markdown access contract, so later features can
  depend on one service boundary before persistence exists.
- The next implementation task can build on that contract instead of extending ad hoc previews.
- Employer rubric mapping now has a first pasted-text slice in the competency library and continues
  to depend on the Markdown foundation for later source expansion.
- Search and export remain deferred until explicit decision docs exist.

## Plan

1. Import strategy, architecture, and task-map docs as supporting references.
2. Add ADR for Markdown-first internal representation and source preservation.
3. Update roadmap sequencing and task-map ordering.
4. Add the free-text Markdown rendering audit execution plan.
5. Move the completed audit to `docs/exec-plans/completed/`.
6. Implement the shared safe Markdown renderer as the first code slice.
7. Update competency evidence planning with employer rubric mapping as a dependent follow-on slice.
8. Plan the artefact Markdown representation slice.
9. Run documentation validation and stale-reference checks.

## Progress Log

- 2026-05-02: Created plan and routed the document-handling foundation into the roadmap.
- 2026-05-02: Completed the free-text Markdown rendering audit. The audit found duplicated
  route-local Markdown-like helpers for AI output and job descriptions, with notes/provenance and
  metadata still rendered as escaped plain text.
- 2026-05-02: Added `app/services/markdown.py` as the shared sanitized renderer for AI outputs and
  Job Workspace descriptions. Focus, Inbox, Job Workspace, and competency-library AI output now
  render through the same helper with regression coverage for escaping and basic Markdown support.
- 2026-05-02: Started artefact Markdown representation planning in
  `docs/exec-plans/completed/artefact-markdown-representation.md`, with a no-schema first-slice
  decision and a source/download-first view model for supported text and extracted artefacts.
- 2026-05-02: Implemented the first no-schema artefact view. Supported artefacts now have an
  owner-scoped detail page that keeps download/source canonical while rendering Markdown/text or
  derived extracted-text previews through the shared safe renderer.
- 2026-05-02: Added ADR
  `docs/architecture/decisions/2026-05-02-artefact-markdown-access-contract.md` and centralized
  artefact Markdown access behind `get_artefact_markdown_access(...)`. Current behaviour remains
  computed/no-schema, but future rubric/search/export work can now depend on that boundary.
- 2026-05-02: Employer rubric mapping is implemented for the first pasted-text slice on top of the
  shared Markdown renderer and visible AI-output contract. Uploaded rubric documents remain
  deferred to later document-handling reuse work.

## Decisions

- Foundation-first sequencing: document handling comes after provider expansion and before
  scheduler/worker.
- Source remains canonical; Markdown is the internal working representation.
- Later rubric source expansion waits for shared Markdown rendering, AI-output Markdown display, and
  intentional source-handling reuse for uploaded documents.
- Centralize existing AI output rendering before expanding Markdown rendering to notes, artefacts,
  profile fields, employer rubrics, search, or export.
- Job Workspace descriptions can move onto the shared helper in the same slice when they reuse the
  same sanitized rendering path and do not expand Markdown support.

## Validation

Commands to run before completion:

```sh
bash scripts/validate-harness.sh
git diff --check
rg -n "Document Handling Foundation|DOCUMENT_HANDLING|employer competency|Markdown-first|SEARCH_AND_RETRIEVAL_DECISION|EXPORT_STRATEGY" docs
```

## Risks

- Document handling can become a broad refactor. Keep the first implementation slice to an audit
  and one shared safe rendering path before schema or extraction work.
