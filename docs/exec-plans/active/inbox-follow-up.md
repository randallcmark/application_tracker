# Execution Plan: Inbox Follow-On Work

Status: Active

Owner: Agent

Created: 2026-04-28

Last Updated: 2026-04-28

## Goal

Continue Inbox from the first capture/review slice into richer email review, provider-backed ingestion, and clearer review handling without collapsing manual and system-driven intake semantics.

## Non-Goals

- replacing manual Add Job as the intentional entry path
- hidden mailbox polling by default
- changing accepted-job owner scoping or workflow semantics without explicit design

## Context

- `docs/DELIVERY_PLAN.md`
- `project_tracker/PUBLIC_SELF_HOSTED_ROADMAP.md`
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

## Decisions

- The existing long-form docs remain the deep source; this plan is the resumable work surface.

## Validation

Commands to run before completion:

```sh
make test
```

## Risks

- Email ingestion can expand architecture and privacy scope quickly if scheduler/provider assumptions are made too early.
