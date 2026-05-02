# Document Handling Strategy

This is a supporting reference for the current planning hubs:

- `docs/PRODUCT_VISION.md`
- `docs/roadmap/implementation-sequencing.md`
- `docs/roadmap/task-map.md`

It defines the product direction for documents, free text, generated content, and external source
material inside Application Tracker.

## Core Principle

Application Tracker preserves external source material as canonical input, while using Markdown as
the internal working representation for text-heavy workflows.

In practice:

- uploaded files, raw captures, and pasted source material remain preserved;
- source provenance remains visible and auditable;
- extracted or entered text is normalized into Markdown for internal rendering and AI context;
- AI features consume and produce Markdown wherever possible;
- export to DOCX, PDF, HTML, plain text, clipboard, or email body happens at the boundary when the
  user needs content outside the app.

## Product Implications

Artefacts should become content assets, not only downloadable attachments. Over time, an artefact
may have:

- original source file or raw source text;
- source type, provenance, and owner scope;
- Markdown working representation;
- metadata and associations to jobs, applications, interviews, notes, and outcomes;
- extraction status and confidence where relevant;
- AI analysis, generated drafts, and derived artefact lineage.

Free-text fields that can contain structured user, extracted, or AI-generated content should render
consistently through a shared Markdown path. Candidate areas include job descriptions, notes,
interview notes, application notes, follow-up drafts, AI recommendations, STAR evidence, employer
rubric interpretations, generated document drafts, artefact summaries, and email capture text.

Generated content should not be trapped in raw panes. AI-generated suggestions, drafts, summaries,
or preparation aids should be visible as Markdown in a native internal viewer or work area. The user
decides when to save, promote, export, discard, or regenerate.

## What This Is Not

This is not a proposal to:

- discard original documents;
- force users to author everything in Markdown;
- build a full document editor immediately;
- implement full-text search before product need is proven;
- let AI silently mutate source artefacts, jobs, notes, profiles, or evidence;
- promise pixel-perfect roundtripping from source files into exported documents.

## Decisions

1. Source remains canonical.
   Preserve original file or raw text, filename/title, MIME type where known, source URL or origin,
   capture method, timestamp, owner, and associated job/interview/application where known.

2. Markdown is the internal working form.
   Markdown is used for rendering, AI prompting, summarization, comparison, reuse, and export
   preparation. It should be clear whether Markdown was user-authored, extracted, AI-generated,
   manually edited, or promoted from AI output.

3. Markdown rendering must be sanitized.
   The app must not blindly render arbitrary embedded HTML, scripts, unsafe links, iframes, or
   injected markup from external sources or AI outputs.

4. AI outputs remain attributable.
   Generated Markdown is tied to source context, output type, provider where relevant, timestamp,
   input artefacts/job context, and the user action that triggered generation.

5. Derived content preserves lineage.
   If an AI draft becomes a saved artefact, preserve the chain from source artefact to AI output to
   saved derived artefact to exported file.

## Search And Retrieval Position

Do not overbuild search yet.

Recommended sequence:

1. structured metadata queries by owner, job, artefact, source kind, output type, timestamps,
   status, outcome, and association;
2. simple text search if a concrete workflow needs it;
3. SQLite FTS5 only after product need is proven and Docker/QNAP runtime compatibility is verified;
4. semantic retrieval or embeddings only after a clear privacy-aware use case emerges.

## Export Position

Export is a boundary operation. Internal content remains Markdown; external formats are derived
outputs.

Recommended export sequence:

1. Markdown;
2. plain text;
3. DOCX with explicit templates;
4. PDF;
5. email body or clipboard-oriented output.

Do not promise layout fidelity or roundtrip equivalence to uploaded source documents.

## Risks

- Markdown extraction can lose layout, tables, styling, comments, tracked changes, and visual
  hierarchy. Preserve source and label extraction confidence.
- External documents can include prompt-injection content. Treat source content as data, not
  instructions.
- Documents may contain sensitive personal and employment data. Preserve owner scoping and avoid
  external AI calls unless the user has configured a provider and triggered the action.
- Markdown rendering creates a security boundary. Render through one sanitized path rather than
  per-template logic.
