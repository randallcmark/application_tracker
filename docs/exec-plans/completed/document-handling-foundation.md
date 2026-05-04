# Execution Plan: Document Handling Foundation

Status: Completed

Owner: Agent

Created: 2026-05-02

Last Updated: 2026-05-03

## Goal

Close out the source-preserving, Markdown-first document-handling foundation so later MCP,
document-heavy AI, search, export, or background automation work can build on one settled boundary.

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

- Document handling is visible as the current top-priority roadmap workstream before MCP.
- Supporting docs and ADR are linked from architecture and agent indexes.
- The free-text Markdown rendering audit is complete and preserved in
  `docs/exec-plans/completed/free-text-markdown-rendering-audit.md`.
- A shared safe Markdown renderer covers AI outputs and Job Workspace descriptions through one
  sanitized helper.
- A no-schema artefact detail view now covers source-first Markdown/text previews plus derived
  extracted-text previews for supported documents.
- The no-schema artefact phase now has a formal Markdown access contract, so later features can
  depend on one service boundary before persistence exists.
- The remaining foundation work is explicit enough to either finish one last foundation slice or
  intentionally defer later work without leaving the representation decision ambiguous.
- Employer rubric mapping now has a first pasted-text slice in the competency library and continues
  to depend on the Markdown foundation for later source expansion.
- Search and export remain deferred until explicit decision docs exist.
  Search and retrieval and export decisions are now both documented.

## Plan

1. Keep the source-canonical, Markdown-first boundary as the non-negotiable foundation.
2. Route remaining artefact/document feature work through the Markdown access contract rather than
   direct extraction helpers.
3. Decide whether one additional foundation slice is required before this plan can move to
   completed.
4. Keep uploaded rubric documents, persisted Markdown records, search, and export deferred behind
   explicit later triggers or decision work.
5. Run documentation validation and stale-reference checks when the close-out decision lands.

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
- 2026-05-03: Roadmap priority is updated so document handling is now the next close-out track
  before MCP planning moves toward implementation. Broad UI cleanup is archived separately as
  UI/UX technical debt, leaving document handling and section workbenches as the main unfinished
  cross-cutting tracks.
- 2026-05-03: Added `docs/SEARCH_AND_RETRIEVAL_DECISION.md`. The foundation now has an explicit
  structured-retrieval-first decision grounded in current workflows and self-hosted runtime
  constraints. Export strategy remains the last named document-handling decision gap.
- 2026-05-03: Added `docs/EXPORT_STRATEGY.md`. Export is now defined as a user-triggered derived
  boundary with Markdown export as the first target, which closes the last named document-handling
  decision gap.
- 2026-05-03: The document-handling foundation is complete. Later search, export, rubric-source,
  persisted-Markdown, or MCP-dependent document work should build on the settled
  source/Markdown/provenance boundary rather than reopen representation choices.

## Decisions

- Foundation-first sequencing: document handling now closes before MCP runtime planning moves
  further and still remains ahead of scheduler/worker.
- Source remains canonical; Markdown is the internal working representation.
- Later rubric source expansion waits for shared Markdown rendering, AI-output Markdown display, and
  intentional source-handling reuse for uploaded documents.
- Centralize existing AI output rendering before expanding Markdown rendering to notes, artefacts,
  profile fields, employer rubrics, search, or export.
- Search now stays explicitly structured-first until a later workflow proves that narrow text
  search, FTS5, or embeddings are necessary.
- Export now stays explicitly derived, lineage-preserving, and Markdown-first until a later
  workflow justifies templated DOCX or PDF generation.
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
