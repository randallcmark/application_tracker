# Execution Plan: Scheduler And Worker

Status: Active

Owner: Agent

Created: 2026-04-28

Last Updated: 2026-04-28

## Goal

Design and implement the smallest self-hosted background runtime that can support imports, optional mailbox ingestion, reminders, stale detection, notifications, and optional AI processing without overcomplicating deployment.

## Non-Goals

- broad microservice decomposition
- mandatory external queue infrastructure
- silent workflow mutation

## Context

- `docs/PRODUCT_VISION.md`
- `docs/roadmap/implementation-sequencing.md`
- `docs/roadmap/task-map.md`
- `docs/DOCKER_DEPLOYMENT.md`
- `docs/architecture/index.md`

## Acceptance Criteria

- The runtime shape is explicit before implementation.
- Deployment guidance remains compatible with the self-hosted default story.
- Background outputs feed visible product surfaces such as Focus and Inbox.

## Plan

1. Define the minimal background-job shape and deployment expectations.
2. Split scheduler, worker, notifications, and import paths into staged slices.
3. Document operational and validation expectations before adding runtime complexity.
4. Add smoke coverage as each background surface lands.

## Progress Log

- 2026-04-28: Created scheduler/worker workstream from the delivery plan.

## Decisions

- Keep scheduler/worker work separate from Inbox provider integration until runtime shape is explicit.

## Validation

Commands to run before completion:

```sh
make test
make docker-import-smoke
```

## Risks

- Background runtime choices can be expensive to unwind for a self-hosted product if deployment simplicity is not protected.
