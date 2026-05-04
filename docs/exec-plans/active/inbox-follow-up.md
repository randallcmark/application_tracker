# Execution Plan: Inbox Follow-On Work

Status: Deferred

Owner: Agent

Created: 2026-04-28

Last Updated: 2026-05-03

## Goal

Continue Inbox from the first capture/review slice into richer email review, provider-backed ingestion, and clearer review handling without collapsing manual and system-driven intake semantics.

## Non-Goals

- replacing manual Add Job as the intentional entry path
- hidden mailbox polling by default
- changing accepted-job owner scoping or workflow semantics without explicit design

## Context

- `docs/PRODUCT_VISION.md`
- `docs/roadmap/implementation-sequencing.md`
- `docs/roadmap/task-map.md`
- `docs/INBOX.md`
- `docs/product/application_tracker_inbox_monitoring_decision_memo.md`
- `docs/product/user-journeys.md`

## Acceptance Criteria

- Inbox continues to preserve provenance and review-before-activation semantics.
- Multi-candidate email handling and provider-backed ingestion are explicitly scoped before implementation.
- Validation covers intake transitions, owner boundaries, and review UX.

## Plan

1. Confirm remaining Inbox requirements from delivery and product docs.
2. Split provider-backed ingestion, richer review flows, and multi-candidate handling into reviewable slices.
3. Update tests, journeys, and validation guidance with each slice.
4. Keep intake semantics explicit and non-overlapping.

## Progress Log

- 2026-04-28: Created active workstream from roadmap and delivery-plan follow-on work.
- 2026-04-30: Started the multi-candidate email review slice. The first implementation uses the
  existing `EmailIntake` to many `Job` relationship: one pasted email can create one Inbox
  candidate per meaningful job URL, while duplicate URLs link to existing owned jobs.
- 2026-05-01: Added deterministic parsing for text-only Indeed saved-alert emails. A pasted alert
  now creates one Inbox candidate per visible job block instead of one generic job containing the
  whole email body.
- 2026-05-01: Added review-readiness checks to the Inbox review surface for missing company,
  location, source URL, description, and low/unknown confidence so partial candidates are cleaned
  up before acceptance.
- 2026-05-03: Deferred further Inbox follow-on work. Current pasted-email review behavior is
  sufficient for now, and board/provider-specific ingestion logic is intentionally left for a later
  planning pass instead of continuing incremental implementation now.

## Decisions

- The existing long-form docs remain the deep source; this plan is the resumable work surface.
- Multi-candidate email handling does not require a schema change for the first slice because
  `EmailIntake.jobs` already supports one provenance record tied to multiple candidate jobs.

## Validation

Commands to run before completion:

```sh
make test
```

## Risks

- Email ingestion can expand architecture and privacy scope quickly if scheduler/provider assumptions are made too early.
