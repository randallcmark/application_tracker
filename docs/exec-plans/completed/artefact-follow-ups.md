# Execution Plan: Artefact Follow-Ups

Status: Complete

Owner: Agent

Created: 2026-04-28

Last Updated: 2026-04-28

## Goal

Let users set a small manual follow-up date on an artefact and see due artefact reminders in Focus.

## Non-Goals

- scheduler or notification delivery
- AI-generated artefact tasks
- broad artefact workflow redesign

## Context

- `docs/product/product-brief.md`
- `docs/product/user-journeys.md`
- `docs/FOCUS.md`
- `docs/agent/ui-ux-rules.md`

## Acceptance Criteria

- Artefact Library shows, edits, and clears an owner-scoped follow-up date.
- Focus lists due or overdue artefact follow-ups without exposing other users' artefacts.
- Schema migration covers the new durable field.
- Focused route and migration tests cover the behavior.

## Plan

1. Add nullable artefact follow-up storage.
2. Extend artefact metadata editing with a date field.
3. Add due artefact reminders to Focus.
4. Update tests and docs.

## Progress Log

- 2026-04-28: Created plan for a narrow manual artefact follow-up slice.
- 2026-04-28: Implemented storage, Artefact Library editing, Focus reminders, tests, and docs.

## Decisions

- Store one nullable `follow_up_at` timestamp on each artefact. This keeps the first slice small and avoids introducing task objects before the workflow needs them.
- Use explicit form edits only. No AI, scheduler, or hidden mutation participates in this feature.

## Validation

Commands to run before completion:

```sh
make test
make check
```

Completed validation:

- `env PYTHONPATH=. arch -arm64 .venv/bin/pytest tests/test_artefact_routes.py tests/test_focus_routes.py tests/test_database_baseline.py`
- `arch -arm64 .venv/bin/python -m ruff check app/api/routes/artefacts.py app/api/routes/focus.py app/db/models/artefact.py app/services/artefacts.py tests/test_artefact_routes.py tests/test_focus_routes.py tests/test_database_baseline.py`
- `make test PYTHON='arch -arm64 .venv/bin/python'`
- `env DATABASE_URL=sqlite:////tmp/application_tracker_artefact_followup_check.db arch -arm64 .venv/bin/alembic check`

## Risks

- Focus can become noisy if artefact follow-ups compete with job follow-ups. Mitigate by limiting the list and keeping copy specific to artefact review.
