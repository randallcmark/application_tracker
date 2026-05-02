# Validation

This file is the authoritative validation contract for Application Tracker. Keep commands copy-pasteable and runnable from the repository root.

## Harness Validation

Run this after changing harness docs or validator behavior:

```sh
bash scripts/validate-harness.sh
```

## Environment Setup

Create a local development environment:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Apply schema changes locally:

```sh
make migrate
```

When a change adds or edits a SQLAlchemy model field, Alembic migration, or durable database
constraint, applying the migration to the active local database is required before completion. Do
not rely only on tests that create a fresh temporary database. Confirm the active database is at
head after the migration:

```sh
.venv/bin/alembic current
```

## Project Validation

Primary automated checks:

```sh
make lint
make test
make check
```

Container build smoke:

```sh
make docker-import-smoke
```

Docker Compose runtime smoke:

```sh
make docker-check
```

## Validation Standard

Before proposing completion:

- Run the narrowest relevant tests during implementation.
- For schema/model changes, run the migration patch against the active local database and confirm
  Alembic is at head.
- Run the full documented validation set before final handoff when feasible.
- If validation fails, fix the cause or clearly report the failure.
- If validation cannot run, explain why and record any persistent gap.

## UI Validation

For UI work, include a browser-level check when the project can run locally:

- start the app with `make run` or `.venv/bin/uvicorn app.main:app --reload`;
- exercise the changed workflow;
- check desktop and mobile widths when layout is affected;
- describe the inspected states in the final handoff.

The design source of truth for UI validation is `docs/design/DESIGN_SYSTEM.md`. Competency evidence flows should also reference `docs/design/COMPETENCY_EVIDENCE_UX.md`.

## Performance And Reliability Validation

When the task changes startup, auth/session behavior, background jobs, data access, retries, storage, AI provider calls, or deployment semantics, validate with the relevant smoke path and inspect logs where available. If the project lacks logs or smoke coverage for the changed path, record that gap in `docs/quality/technical-debt.md`.
