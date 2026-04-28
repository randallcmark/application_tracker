# ADR 2026-04-15: Intake Paths Distinguish User-Curated And System-Recommended Jobs

## Status

Accepted

## Decision

Manually added or user-captured jobs are distinct from system-recommended, scheduled-imported, or low-confidence captured jobs.

## Rationale

- User-curated jobs may already represent intent and can enter active workflow directly.
- System-recommended or low-confidence jobs require validation before consuming application effort.
- Inbox is the judgment surface for accepting, dismissing, or enriching uncertain opportunities.
