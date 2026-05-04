# Search And Retrieval Decision

Status: Accepted for the current foundation phase

Last Updated: 2026-05-03

## Purpose

Decide what search and retrieval capability Application Tracker should implement next for
document-heavy and free-text workflows, and what remains intentionally deferred.

This decision closes the current ambiguity around document search without forcing premature
infrastructure into a local-first, self-hosted product.

## Current Product Reality

Application Tracker is not a general document repository. The current user workflows are:

- Focus surfaces due follow-ups, stale work, interviews, artefact reviews, and next-action gaps.
- Inbox handles review-before-activation for captured or recommended opportunities.
- Job Workspace helps the user progress one role with visible notes, artefacts, and AI output.
- Artefacts are reusable working assets linked to jobs and outcomes.

These workflows already depend heavily on structured relationships:

- owner;
- job;
- application or interview context;
- artefact kind and purpose;
- timestamps;
- workflow state;
- AI output type;
- provenance and associations.

The repo does not yet show a validated user need for cross-document full-text search, semantic
retrieval, or embeddings as a first-class product surface.

## Decision

Application Tracker should stay on **structured retrieval first** for the next implementation
phase.

That means:

1. Prefer owner-scoped metadata queries and targeted filters over broad text indexing.
2. Allow future narrow text search only when a specific workflow proves it is needed.
3. Defer SQLite FTS5 until the workflow need is concrete and Docker/QNAP runtime behavior is
   validated for this app's deployment model.
4. Defer embeddings or semantic retrieval until there is a clear privacy-aware use case that
   structured retrieval and narrow text search cannot serve.

## Why This Is The Right Boundary Now

### It matches the product

The product is organized around deciding what deserves attention, reviewing captured opportunities,
progressing one role, and reusing artefacts intentionally. Those are workflow and association
problems first, not search-engine problems first.

### It preserves self-hosted simplicity

The default runtime is a FastAPI monolith with SQLite/local storage defaults and Docker support for
small self-hosted deployments. Adding FTS tables, indexing jobs, staleness repair, or embedding
pipelines would raise operational and migration complexity before the product has proven the need.

### It respects the document boundary

The document-handling foundation now has a source-canonical, Markdown-first boundary and a
no-schema artefact Markdown access contract. Search should depend on that boundary later rather
than forcing early persistence or extraction changes now.

### It keeps AI and privacy risk contained

Embeddings and semantic retrieval would expand the amount of derived document state, increase
privacy sensitivity, and create new questions about rebuilds, invalidation, provider use, and
owner-scoped deletion. Those costs are not justified yet.

## What Is In Scope Next

If a near-term search slice is needed, it should stay narrow and workflow-specific. Valid examples:

- filtering artefacts by job, kind, purpose, outcome context, or follow-up state;
- listing AI outputs by job, output type, or recency;
- finding jobs with missing or stale preparation material through structured signals;
- locating evidence or rubric mappings by explicit association rather than semantic similarity.

Any such slice should reuse existing owner-scoped models and route through the current
source/Markdown/provenance contracts.

## What Stays Deferred

The following remain intentionally out of scope for now:

- global free-text search across all notes, jobs, artefacts, and AI outputs;
- SQLite FTS5 indexes;
- background indexing jobs;
- embeddings or vector stores;
- provider-backed retrieval pipelines;
- semantic ranking or recommendation based on document similarity.

## Triggers For Reconsideration

Reopen this decision only when one or more of these become true:

1. A repeated user workflow cannot be handled acceptably with owner-scoped metadata filters.
2. Users need to find content by remembered phrases across multiple Markdown/document surfaces.
3. The same Markdown/document corpus is being re-read across enough features that indexed lookup is
   clearly better than ad hoc scanning.
4. MCP, export, or background automation needs stable text retrieval beyond current associations.
5. There is evidence that retrieval quality, not workflow framing, is the bottleneck.

## Decision Ladder

When a new need appears, escalate in this order:

1. Strengthen structured filters and associations.
2. Add one narrow text-search surface for the proven workflow.
3. Evaluate SQLite FTS5 only after runtime and migration implications are documented.
4. Evaluate embeddings only after privacy, storage, rebuild, deletion, and provider-boundary rules
   are documented.

Do not skip directly to FTS or embeddings because the app handles documents.

## Implementation Guardrails

- Keep retrieval owner-scoped.
- Treat source material as canonical and Markdown as the working representation.
- Do not introduce hidden indexing jobs before scheduler/worker planning is ready.
- Do not make retrieval depend on provider availability.
- Do not introduce search persistence that bypasses the artefact Markdown access contract.

## Consequences

- The current document-handling foundation can proceed without adding search infrastructure.
- Future search work must begin with a concrete workflow and execution plan, not with a generic
  indexing implementation.
- `docs/EXPORT_STRATEGY.md` is the companion export-boundary decision for the same foundation.
