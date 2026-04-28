# ADR 2026-04-11: Store Provider-Relative Artefact Keys

## Status

Accepted

## Decision

Artefact records store provider-relative keys, not absolute local paths or full provider URIs.

## Rationale

- The same database record can be interpreted by local and S3-compatible providers.
- Backups and restores stay more portable.
- Path traversal checks can be centralized before providers touch the filesystem or object store.
