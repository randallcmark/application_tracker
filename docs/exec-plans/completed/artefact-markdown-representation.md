# Execution Plan: Artefact Markdown Representation

Status: Complete

Owner: Agent

Created: 2026-05-02

Last Updated: 2026-05-02

## Goal

Define and implement the first artefact-local source/Markdown representation slice so artefacts can
gain a safe internal text view without weakening source preservation, owner scoping, or visible
provenance.

## Non-Goals

- replacing the original artefact file as the canonical source
- introducing search, export, embeddings, or background extraction
- broad document-editor work
- changing AI provider behavior
- schema changes unless the plan proves a no-schema slice is insufficient

## Context

- `docs/DOCUMENT_HANDLING_STRATEGY.md`
- `docs/DOCUMENT_HANDLING_ARCHITECTURE.md`
- `docs/DOCUMENT_HANDLING_TASK_MAP.md`
- `docs/exec-plans/active/document-handling-foundation.md`
- `docs/ARTEFACTS.md`
- `docs/ARTEFACT_AI_PLAN.md`
- `app/db/models/artefact.py`
- `app/services/artefacts.py`
- `app/api/routes/artefacts.py`

## Acceptance Criteria

- The first implementation slice has an explicit schema or no-schema decision.
- Source/download remains the canonical artefact path.
- UI states distinguish source file availability, Markdown availability, extraction status,
  confidence, and provenance/lineage.
- The implementation identifies which artefact types are supported first and which remain
  source-download only.
- Validation covers owner scoping, rendering safety, and fallback behavior.

## Current State At Completion

- `Artefact` still stores source metadata, storage key, content type, checksum, notes, and
  owner/job links, with no durable Markdown representation model yet.
- The artefact library now links to an owner-scoped artefact detail view instead of being
  download-only.
- The artefact detail view keeps source/download canonical and adds a safe Markdown preview for
  supported source or extracted text.
- Existing helpers still power text extraction for AI context and now also support the preview
  surface.

## First-Slice Decision

Use a **no-schema first slice**.

Rationale:

- the repo already had enough source metadata plus extraction helpers to provide a read-only
  Markdown view for supported artefacts;
- the document-handling foundation explicitly favored a narrow first slice before adding new
  persistence;
- a no-schema implementation proved the product/UI value and fallback behavior before committing to
  a durable `MarkdownDocument`-style model;
- saved AI drafts already arrived as Markdown source files, so the first slice could show useful
  value without any migration.

## Implemented Slice

1. Added an owner-scoped artefact detail/view surface that keeps download/source actions primary.
2. Added these first-slice states:
   - source Markdown for `.md` and Markdown content types;
   - source text for `.txt` and `text/plain`;
   - derived text preview for supported office/PDF extraction paths;
   - explicit unavailable-preview fallback for unsupported binary sources.
3. Reused the shared safe Markdown helper for rendered preview output.
4. Kept provenance and source/download visible in the artefact detail view.

## Supported First-Slice Artefact Types

- Direct Markdown render:
  - `text/markdown`
  - `text/x-markdown`
  - `application/markdown`
  - `.md`
  - `.markdown`
- Safe plain-text render through Markdown path:
  - `text/plain`
  - `.txt`
- Derived Markdown preview from extracted text:
  - `.docx`
  - `.doc`
  - `.rtf`
  - `.odt`
  - `.pdf`

## Deferred Items

- Durable Markdown storage or edit history.
- Rich source/Markdown diffing.
- In-browser DOCX/PDF layout rendering.
- Search/export integration.
- Employer rubric/document upload flows that depend on later artefact representation work.

## Progress Log

- 2026-05-02: Created the execution plan with a no-schema first-slice decision.
- 2026-05-02: Implemented `load_artefact_markdown_preview` and an artefact detail route that keeps
  source/download canonical while rendering supported previews through the shared Markdown helper.
- 2026-05-02: Added artefact route and service tests for source Markdown preview, unavailable
  binary fallback, derived PDF preview metadata, and owner scoping.
- 2026-05-02: Formalized `get_artefact_markdown_access(...)` as the service-layer contract for
  computed artefact Markdown access before persistence. Artefact preview and AI call sites now
  depend on that boundary instead of reaching directly for ad hoc extraction helpers.

## Validation

Commands run for completion:

```sh
PYTHONPATH=. .venv/bin/pytest tests/test_artefact_service.py tests/test_artefact_routes.py
git diff --check
```

## Risks

- Extraction quality varies by file type, so the UI must avoid implying perfect fidelity.
- A document-like artefact view can sprawl into editor/export/search work unless later slices stay
  provenance-first.
- If richer representation is needed later, add explicit fields or a separate model instead of
  overloading notes.
