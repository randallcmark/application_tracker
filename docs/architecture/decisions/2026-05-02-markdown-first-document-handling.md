# ADR 2026-05-02: Markdown-First Document Handling

## Status

Accepted

## Decision

Application Tracker preserves original uploaded, pasted, captured, or generated source material as
canonical input and uses Markdown as the internal working representation for text-heavy content.

Rendered Markdown must go through a shared sanitized rendering path. Export formats are generated at
the boundary. Search starts with structured metadata and should not move to FTS or embeddings until
a documented product need exists.

## Rationale

- Job-search source material includes resumes, cover letters, job descriptions, recruiter emails,
  employer rubrics, notes, and AI outputs. Source fidelity matters, so original material must not
  be overwritten by extraction or normalization.
- Markdown is human-readable, diffable, portable, and efficient for AI context and generated
  content.
- Centralized safe rendering reduces the risk of unsafe HTML, scripts, event handlers, unsafe
  links, and prompt-injection-adjacent source material leaking into UI or AI behavior.
- Export requirements vary by destination and should not complicate the internal working model
  prematurely.
- Structured metadata retrieval is enough until user workflows prove the need for text indexing or
  semantic retrieval.

## Consequences

- New document-heavy features should preserve source material separately from Markdown working
  representations.
- AI prompts should treat external content as data, not instructions.
- AI outputs should be Markdown-compatible and visibly attributable.
- Search, FTS, embeddings, DOCX export, and PDF export require separate decision or execution
  plans before implementation.
