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
- renderer implementation
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
- The first implementation task is the free-text Markdown rendering audit.
- Employer rubric mapping is routed as a future competency-evidence slice, not a current top-level
  workstream.
- Search and export remain deferred until explicit decision docs exist.

## Plan

1. Import strategy, architecture, and task-map docs as supporting references.
2. Add ADR for Markdown-first internal representation and source preservation.
3. Update roadmap sequencing and task-map ordering.
4. Add the free-text Markdown rendering audit execution plan.
5. Update competency evidence planning with employer rubric mapping as a dependent future slice.
6. Run documentation validation and stale-reference checks.

## Progress Log

- 2026-05-02: Created plan and routed the document-handling foundation into the roadmap.

## Decisions

- Foundation-first sequencing: document handling comes after provider expansion and before
  scheduler/worker.
- Source remains canonical; Markdown is the internal working representation.
- Employer rubric mapping waits for shared Markdown rendering and AI-output Markdown display.

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
