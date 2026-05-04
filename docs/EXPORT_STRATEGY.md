# Export Strategy

Status: Accepted for the current foundation phase

Last Updated: 2026-05-03

## Purpose

Define how Application Tracker turns internal Markdown content into external output formats without
confusing derived export files with canonical source material.

This decision closes the current ambiguity around document export so later implementation can reuse
the source/Markdown/provenance boundary that document handling has already established.

## Decision

Export is a **user-triggered boundary operation**.

Inside the app:

- source material remains canonical;
- Markdown remains the internal working representation;
- rendered HTML is only a view, not a durable content format.

At the boundary:

- the user may derive an external format from Markdown or Markdown-backed content;
- the export must preserve lineage to its internal source context;
- the export must not overwrite or silently replace canonical source files.

## First Export Target

The first export target should be **Markdown (`.md`)**.

This is the right first step because:

1. it matches the internal working representation directly;
2. it preserves the most content with the least transformation risk;
3. it avoids premature layout/template decisions;
4. it keeps local-first implementation simple for self-hosted deployments;
5. it gives later DOCX, PDF, email, or clipboard flows one stable source format to build from.

Plain text (`.txt`) is a near-term follow-on, not the first priority. DOCX and PDF remain later
derived outputs with higher formatting and template complexity.

## Export Order

When export work is implemented, it should escalate in this order:

1. Markdown (`.md`)
2. plain text (`.txt`)
3. email body / clipboard-oriented text
4. DOCX using explicit templates
5. PDF derived from a defined export path, not from original uploaded layout

Do not skip directly to DOCX or PDF just because users upload DOCX or PDF source files.

## What Export Means

Export should mean taking a visible, attributable internal content record and deriving a portable
external representation for use outside the app.

Valid export sources may later include:

- AI outputs;
- generated drafts;
- Markdown-backed artefact views;
- job-preparation packs or notes;
- employer rubric interpretation output;
- other user-authored or system-derived Markdown surfaces that already have clear provenance.

Export should not require that every source document become editable or round-trippable.

## Lineage Rules

Every exported file should remain traceable to the content that produced it.

At minimum, later implementation should preserve:

- owner scope;
- source content record or originating surface;
- export format;
- export timestamp;
- user action that triggered export;
- where applicable, the source artefact or AI output lineage already recorded in the app.

If an exported file is later saved back into the app as an artefact, that saved artefact should be
treated as a new derived asset, not as proof that the original source file changed.

## Non-Goals

This strategy does not commit the app to:

- pixel-perfect roundtripping to uploaded DOCX or PDF files;
- recreating original typography, layout, comments, or tracked changes from uploaded documents;
- in-browser WYSIWYG document editing;
- automatic background export generation;
- silent promotion of AI output into downloadable artefacts;
- hidden mutation of jobs, notes, artefacts, profiles, or evidence during export.

## Why This Boundary Fits The Product

Application Tracker is a job-search workspace, not a document-layout suite. The product needs
portable outputs, but its core value is deciding, preparing, reusing, and learning inside a
private local-first workflow.

That means export should serve workflow moments such as:

- taking a prepared draft outside the app;
- copying tailored content into an application flow;
- keeping a Markdown copy of visible AI output;
- producing a later templated document from reviewed internal content.

It should not force the document model to mimic Word or PDF layout systems prematurely.

## Format-Specific Guidance

### Markdown

- Treat as the reference export format.
- Preserve headings, lists, emphasis, links, and other supported safe Markdown features.
- Prefer the same Markdown content the app already renders or stores conceptually.

### Plain text

- Use as a downgraded portability target.
- Accept that formatting becomes simpler and some structure is flattened.

### Email body / clipboard

- Treat as convenience exports, not primary archival formats.
- Keep them derived from the same reviewed Markdown source used by other exports.

### DOCX

- Add only when there is a concrete workflow and template requirement.
- Generate from reviewed Markdown content plus explicit template choices.
- Do not promise reconstruction of uploaded DOCX layout or styling.

### PDF

- Treat as a late-stage presentation or sharing format.
- Generate from a defined export pipeline, not from best-effort reverse engineering of uploaded
  PDFs.

## Implementation Guardrails

- Keep export owner-scoped and user-triggered.
- Export from Markdown or Markdown-backed content, not from rendered HTML fragments as the durable
  source of truth.
- Preserve visible provenance and attribution for exported AI-derived content.
- Do not make export depend on provider availability.
- Do not let export requirements force early persisted Markdown records unless the triggers in
  `docs/architecture/decisions/2026-05-02-artefact-markdown-access-contract.md` are met.
- Keep uploaded source downloads separate from derived export actions in the UI.

## Triggers For Reconsideration

Reopen this strategy when one or more of these become true:

1. users repeatedly need polished external documents from the same internal Markdown content;
2. specific job-search workflows need consistent document templates;
3. export needs durable review, approval, or version tracking beyond current provenance;
4. later search, MCP, or background workflows require a more formal export lifecycle;
5. implementation proves that computed Markdown access is insufficient for reliable export reuse.

## Consequences

- The document-handling foundation now has an explicit export boundary to pair with the search and
  retrieval decision.
- Later export implementation should start with Markdown export rather than DOCX/PDF generation.
- Source-preserving, Markdown-first handling remains stable even when external file generation is
  added later.
- The document-handling foundation can now close without leaving export behavior ambiguous.
