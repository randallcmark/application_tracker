# Execution Plan: Free-Text Markdown Rendering Audit

Status: Active planning

Owner: Agent

Created: 2026-05-02

Last Updated: 2026-05-02

## Goal

Identify every free-text field and page that renders user-authored, extracted, captured, or
AI-generated text so the first shared Markdown renderer slice can be implemented safely.

## Non-Goals

- renderer implementation
- schema changes
- UI redesign
- prompt or provider changes
- search, extraction, or export implementation

## Context

- `docs/DOCUMENT_HANDLING_STRATEGY.md`
- `docs/DOCUMENT_HANDLING_ARCHITECTURE.md`
- `docs/DOCUMENT_HANDLING_TASK_MAP.md`
- `docs/exec-plans/active/document-handling-foundation.md`
- `docs/agent/security-rules.md`
- `docs/agent/ai-feature-rules.md`

## Acceptance Criteria

- Audit covers job descriptions, notes, interview notes, application notes, follow-up content,
  competency evidence, AI outputs, generated drafts, artefact summaries, email capture text, and
  employer rubric text.
- Each audited item records source model, storage field, current rendering path, risk, and
  recommended handling.
- Audit identifies the first low-risk surfaces for shared Markdown rendering.
- No product behavior changes are made during the audit.

## Plan

1. Inspect models for free-text fields.
2. Inspect route/template rendering for those fields.
3. Classify content source as user-authored, captured, extracted, or AI-generated.
4. Record rendering safety risks and recommended Markdown handling.
5. Choose first renderer implementation surfaces, likely AI outputs plus one low-risk text surface.

## Audit Table Template

| Surface | Source model | Storage field | Source type | Current rendering | Risk | Recommended handling |
| --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Progress Log

- 2026-05-02: Created plan as the first implementation task for Document Handling Foundation.

## Decisions

- The audit precedes renderer implementation.
- Existing plain text should remain readable when rendered as Markdown.

## Validation

Commands to run before completion:

```sh
bash scripts/validate-harness.sh
git diff --check
```

## Risks

- Some text may already contain HTML fragments. Treat all rendered content as untrusted until the
  audit proves otherwise.
