# Document Handling Architecture

This supporting architecture reference describes how Application Tracker should handle external
documents, free text, extracted content, Markdown rendering, AI-generated outputs, and future export
workflows.

## Goals

- Preserve source files and raw captures.
- Make Markdown the internal working representation for text-heavy workflows.
- Keep provenance and lineage visible.
- Let AI features use clean source-linked text context.
- Avoid scattering rendering logic across templates.
- Avoid early commitment to heavy indexing or semantic retrieval.
- Keep export as an explicit boundary concern.

## Conceptual Model

```text
Source Input
  - uploaded file
  - pasted text
  - captured email
  - browser capture
  - AI output promoted to artefact

Canonical Source Record
  - original file or raw text
  - source metadata
  - provenance
  - owner scope

Markdown Representation
  - extracted or normalized text
  - Markdown content
  - extraction status
  - confidence
  - generated or edited flags

Internal Use
  - render in UI
  - feed AI prompts
  - compare against jobs/rubrics
  - create drafts
  - analyze outcomes

Export Boundary
  - Markdown
  - plain text
  - DOCX
  - PDF
  - email body
```

## Existing Concepts

Use current repo models where possible.

`Artefact` remains the user-owned file or document-like asset and should continue to support owner
scope, job associations, event/interview associations, metadata, download, provenance, and outcome
linkage where available.

`AiOutput` remains the visible AI result record. AI output body text should be treated as
Markdown-compatible content and should remain visible, source-linked, and non-mutating until the
user explicitly saves or promotes it.

Competency evidence remains user-owned structured STAR material. Employer rubric mapping should
consume Markdown context and produce visible preparation output without silently mutating evidence.

## Future Concepts

Names below are conceptual and should not be implemented without a concrete execution plan.

`ContentSource` may become useful if source material expands beyond current artefacts, jobs, email
intakes, and AI output records. It would represent canonical uploaded, pasted, captured, or
promoted source material.

`MarkdownDocument` may become useful when Markdown representations need durable lifecycle tracking.
It would represent extracted, normalized, user-authored, AI-generated, or export-ready Markdown tied
to a source.

## Markdown Storage Rules

- Store Markdown as text, not rendered HTML.
- Render Markdown centrally through a shared sanitized helper/component.
- Preserve raw source separately.
- Keep plain text compatible with Markdown rendering.
- Track whether Markdown is extracted, user-authored, AI-generated, manually edited, promoted, or
  export-ready when persistence is added.

Supported Markdown should include headings, paragraphs, bold/italic, bullet and numbered lists,
blockquotes, code spans/blocks, safe links, and tables only if the renderer handles them safely.

Unsafe features should be stripped or escaped: script tags, inline event handlers, unsafe HTML,
unknown protocols, iframes, and arbitrary raw HTML unless explicitly sanitized.

## Extraction Rules

Pasted text can be normalized directly into Markdown. Preserve paragraphs and bullet-like lines,
avoid over-formatting, and escape unsafe HTML.

Uploaded documents should reuse existing extraction support first. Do not build a new extraction
subsystem until the product need is clear. Record extraction status and confidence, preserve
original file download, and label low-confidence extraction.

AI-generated content should be requested and stored as Markdown where appropriate. Generated
content remains working output until the user saves or promotes it.

## Provenance And Lineage

Every Markdown representation should be traceable to its source.

Examples:

```text
Uploaded DOCX -> extracted Markdown
Uploaded PDF -> extracted Markdown with low confidence
Pasted employer rubric -> preserved source text + normalized Markdown
AI tailoring suggestion -> AI output Markdown
AI draft promoted to artefact -> derived Markdown artefact
```

Lineage is especially important for resumes, cover letters, STAR examples, interview prep packs,
employer rubric analysis, submitted artefacts, and outcome analysis.

## AI Interaction Model

AI should consume Markdown-first context where possible:

- job description Markdown;
- artefact Markdown;
- profile Markdown summary;
- competency evidence Markdown;
- employer rubric Markdown;
- notes Markdown.

Avoid passing binary or encoded content to AI unless no extracted text exists and the configured
provider supports it safely. Treat external documents as data, not instructions.

AI outputs should be Markdown, structured where possible, source-linked, visible, and never
silently mutating.

## Search And Export

Start with structured queries over owner, job, artefact, source kind, output type, event
association, timestamps, status, and outcome linkage. Evaluate text search, FTS5, and embeddings
only after product workflows prove the need.

Export is an edge operation. Internal content remains Markdown. Export targets such as `.md`,
`.txt`, `.docx`, `.pdf`, email body, and clipboard are derived outputs.

## UI Architecture Direction

Create one shared Markdown viewer/rendering path. Candidate surfaces include job description,
notes, AI outputs, STAR evidence, employer rubric analysis, generated drafts, and artefact Markdown
views.

For artefacts, use a progressive source/Markdown/AI/history pattern only when it supports the task.
Do not add tabs or panels before the source/Markdown distinction is useful.
