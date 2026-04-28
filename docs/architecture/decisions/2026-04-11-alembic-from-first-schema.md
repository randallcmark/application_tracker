# ADR 2026-04-11: Alembic From The First Schema

## Status

Accepted

## Decision

The rebuild uses Alembic migrations instead of startup-time `create_all`.

## Rationale

- Job-search history becomes valuable user data quickly.
- Self-hosted users need a documented upgrade path.
- Schema drift was a main issue in the original MVP.
