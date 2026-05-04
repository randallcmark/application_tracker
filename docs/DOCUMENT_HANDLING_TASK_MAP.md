# Document Handling Task Map

This supporting task map breaks the Markdown-first document handling strategy into implementation
tasks. The canonical roadmap entry remains `docs/roadmap/task-map.md`.

## Task 1: Architecture Docs And ADR

Goal: document the source-preserving, Markdown-first model.

Deliverables:

- `docs/DOCUMENT_HANDLING_STRATEGY.md`
- `docs/DOCUMENT_HANDLING_ARCHITECTURE.md`
- `docs/DOCUMENT_HANDLING_TASK_MAP.md`
- `docs/architecture/decisions/2026-05-02-markdown-first-document-handling.md`
- routing updates in architecture and agent indexes

Acceptance criteria:

- source preservation is documented;
- Markdown as internal working representation is documented;
- AI output and export principles are documented;
- search/indexing position is explicitly deferred.

## Task 2: Free-Text Markdown Rendering Audit

Goal: identify every free-text field and page that renders user-authored, extracted, captured, or
AI-generated text.

Deliverable:

- `docs/exec-plans/completed/free-text-markdown-rendering-audit.md`

Audit table should cover field, source model, storage field, current rendering, risk, and
recommended handling.

Candidate areas:

- job descriptions;
- notes and journal entries;
- interview notes and application notes;
- follow-up content;
- STAR evidence;
- employer rubric text;
- artefact analysis;
- AI outputs and generated drafts;
- email capture text.

Acceptance criteria:

- no code changes unless a read-only audit helper is explicitly needed;
- audit identifies the first implementation slice;
- unsafe rendering risks are visible.

Status: complete. This audit led directly to the shared safe Markdown renderer for AI outputs and
Job Workspace descriptions.

## Task 3: Shared Safe Markdown Renderer

Goal: create or standardize one safe Markdown rendering path.

Requirements:

- render Markdown consistently;
- sanitize unsafe HTML, scripts, event handlers, iframes, and unsafe links;
- allow common Markdown features;
- keep existing plain text readable.

Candidate first surfaces:

- AI outputs;
- one low-risk plain text surface identified by the audit.

Acceptance criteria:

- existing plain text still renders acceptably;
- unsafe content is escaped or removed;
- tests cover Markdown basics and unsafe content.

Status: complete. `app/services/markdown.py` now provides the shared sanitized renderer used by AI
output surfaces and Job Workspace descriptions.

## Task 4: AI Output Markdown Standardization

Goal: ensure AI-generated content is treated as Markdown and rendered through the shared viewer.

Requirements:

- do not change provider abstraction unless needed;
- do not mutate workflow state;
- preserve source context and provenance;
- keep AI output visible and collapsible where appropriate.

Acceptance criteria:

- AI outputs render Markdown consistently;
- long AI outputs do not appear as raw unformatted text;
- existing output types continue to work.

Status: complete. Focus, Inbox, Job Workspace, and competency-library AI outputs now render through
the shared Markdown helper.

## Task 5: Artefact Markdown Representation Design

Goal: plan how artefacts get internal Markdown representations while preserving source.

Deliverables:

- execution plan for artefact Markdown representation;
- first-slice schema/no-schema decision;
- source/Markdown/provenance UI notes.

Acceptance criteria:

- original artefacts remain downloadable;
- existing source data is not overwritten;
- extraction status/confidence and lineage are defined;
- fallback behavior for unsupported extraction is clear.

Status: complete. The first slice stays no-schema, and the repo now has a formal Markdown access
contract plus a completed execution plan in
`docs/exec-plans/completed/artefact-markdown-representation.md`.

## Task 6: Artefact Markdown First Implementation Slice

Goal: implement the smallest useful artefact Markdown representation.

Possible scope:

- support pasted/plain-text artefacts first;
- support already available extracted text;
- store Markdown representation if a schema is approved;
- or compute/display a Markdown view if no schema is chosen.

Acceptance criteria:

- original artefact remains downloadable;
- Markdown view is available for supported artefacts;
- unsupported artefacts show clear status;
- no source data is overwritten.

Status: complete for the first slice. A source-first artefact detail view now renders supported
Markdown/text and derived extracted-text previews through the shared safe renderer.

## Task 7: Employer Rubric And Competency Evidence Integration

Goal: use Markdown-first handling to support employer competency rubric intake.

Dependencies:

- shared Markdown renderer;
- AI output Markdown rendering;
- competency evidence builder;
- employer rubric mapping task.

Acceptance criteria:

- pasted employer rubric is normalized as Markdown;
- AI mapping consumes Markdown context;
- mapping output renders as Markdown or structured cards;
- source material remains visible.

Status: implemented for the first pasted-text slice in the competency library. Uploaded rubric
documents remain deferred until artefact/document handling reuse is explicit.

## Task 8: Search And Retrieval Decision

Goal: decide whether structured metadata search is enough or whether text indexing is needed.

Future deliverable:

- `docs/SEARCH_AND_RETRIEVAL_DECISION.md`

Acceptance criteria:

- no search implementation until the decision is documented;
- recommendation is grounded in product workflows;
- Docker/QNAP runtime compatibility is considered before FTS.

Status: complete. `docs/SEARCH_AND_RETRIEVAL_DECISION.md` now keeps the current phase on
owner-scoped structured retrieval first, defers broad text indexing, and documents the triggers
required before SQLite FTS5 or embeddings are reconsidered.

## Task 9: Export Boundary Design

Goal: define how Markdown content becomes external output formats.

Future deliverable:

- `docs/EXPORT_STRATEGY.md`

Acceptance criteria:

- export is defined as derived output;
- source lineage is preserved;
- no pixel-perfect roundtrip promise is made;
- first export target is identified.

Status: complete. `docs/EXPORT_STRATEGY.md` now defines export as a user-triggered derived
boundary, preserves lineage, rejects pixel-perfect roundtrip promises, and identifies Markdown
export as the first target.
