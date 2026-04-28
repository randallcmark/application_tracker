# Execution Plan: Admin, Restore, And Self-Hosted Operations

Status: Active

Owner: Agent

Created: 2026-04-28

Last Updated: 2026-04-28

## Goal

Expand the self-hosted operations surface so backups, restore validation, operational visibility, and maintenance are explicit and trustworthy for private deployments.

## Non-Goals

- SaaS-style centralized admin
- weakening production guardrails
- mixing admin operations into daily workflow navigation

## Context

- `docs/DELIVERY_PLAN.md`
- `project_tracker/PUBLIC_SELF_HOSTED_ROADMAP.md`
- `README.md`
- `docs/AUTHENTICATION.md`
- `docs/product/user-journeys.md`

## Acceptance Criteria

- Admin-only operations remain clearly separated and owner-safe.
- Backup and restore guidance is explicit before adding new operations.
- Validation includes operational smoke paths where relevant.

## Plan

1. Inventory remaining admin and restore gaps from the roadmap.
2. Separate operational docs, admin UI changes, and restore validation into reviewable slices.
3. Keep Docker/self-hosted guidance aligned with implementation.
4. Add debt entries when admin/ops behavior is documented but not yet enforced or smoke-tested.

## Progress Log

- 2026-04-28: Created admin/restore/ops workstream from the delivery plan.

## Decisions

- Keep restore validation as a first-class acceptance criterion, not a later documentation-only step.

## Validation

Commands to run before completion:

```sh
make test
make docker-import-smoke
```

## Risks

- Self-hosted trust erodes quickly if backup or restore behavior is implied rather than explicitly validated.
