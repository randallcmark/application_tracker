# ADR 2026-05-02: Artefact Markdown Access Contract Before Persistence

## Status

Accepted

## Decision

Application Tracker stays **no-schema** for artefact Markdown representation in the immediate next
phase, but feature code must stop depending directly on ad hoc preview or extraction helpers.

Artefact consumers should depend on a single service-layer Markdown access contract that can return:

- Markdown-compatible text when available;
- source kind and confidence;
- warnings about derived or low-confidence access;
- whether the returned text is canonical source text or a computed derivative.

Current implementation uses `app.services.artefacts.get_artefact_markdown_access(...)` as that
contract.

## Rationale

- Source files remain canonical and must not be silently replaced by extracted or normalized text.
- Current preview coverage is sufficient for UI inspection.
- Durable Markdown persistence introduces lifecycle, staleness, versioning, repair, and migration
  obligations that are not justified yet.
- Upcoming features such as rubric mapping should depend on a Markdown access boundary, not on
  whether Markdown is computed today or stored tomorrow.
- A stable contract lets persistence arrive later without changing feature call sites.

## Triggers For Persisted Markdown Records

Move from computed access to durable persisted Markdown records only when one or more of these
conditions become true:

1. The same artefact Markdown must be reused across multiple features and repeated extraction is a
   measurable cost or reliability problem.
2. The product needs staleness tracking between source files and derived Markdown.
3. Users need visible review, correction, or approval of extracted Markdown.
4. Features require durable lineage, version history, or auditability beyond source metadata plus
   current provenance.
5. Search/export pipelines need a stable Markdown working record rather than on-demand computation.

## Consequences

- New feature code should call the Markdown access contract instead of reaching straight for
  extraction helpers.
- UI preview, AI prompt context, and later rubric/search/export flows should all be able to pivot
  from computed access to persisted access without changing their call sites.
- Direct extraction helpers may remain as implementation details, but they are not the cross-feature
  contract.
- Introducing persisted Markdown later requires a new execution plan covering schema, lifecycle,
  staleness, and migration rules.
