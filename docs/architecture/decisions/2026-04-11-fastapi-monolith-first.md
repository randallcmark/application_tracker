# ADR 2026-04-11: FastAPI Monolith First

## Status

Accepted

## Decision

The first public version remains a FastAPI monolith.

## Rationale

- The product is workflow-heavy but not yet large enough to justify a split frontend/backend architecture.
- Docker Compose deployment should remain simple.
- Server-rendered pages plus focused JavaScript are enough for the initial workflow surfaces.
