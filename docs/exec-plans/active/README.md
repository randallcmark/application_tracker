# Active Execution Plans

This directory holds the current workstreams that future agent sessions should resume from first.

Current work should also be visible from the task hub:

- `docs/roadmap/task-map.md`

The primary implementation track at the moment is artefact AI / competency evidence continuation.
Broad UI cleanup and the Job Workspace section-workbench pass have been archived separately so
future sessions do not confuse completed workspace implementation with the current AI-focused work.

The completed Job Detail section-workbench execution record now lives in
`docs/exec-plans/completed/job-detail-section-workbenches.md`. Use it as historical context rather
than an active workstream.

Document-handling close-out is complete in
`docs/exec-plans/completed/document-handling-foundation.md`. Use that plan plus
`docs/SEARCH_AND_RETRIEVAL_DECISION.md` and `docs/EXPORT_STRATEGY.md` before starting richer
document-heavy AI, search, export, or MCP-dependent Markdown work. The free-text Markdown rendering
audit and first artefact Markdown representation slice are complete in
`docs/exec-plans/completed/free-text-markdown-rendering-audit.md` and
`docs/exec-plans/completed/artefact-markdown-representation.md`.

Completed broad UI cleanup history now lives in
`docs/exec-plans/completed/ui-density-layout-ai-cleanup.md` and
`docs/exec-plans/completed/job-workspace-reduction.md`. Treat new broad polish as UI/UX technical
debt or as dedicated feature/workbench work, not as revived active cleanup streams.

Completed admin/restore/ops history now lives in
`docs/exec-plans/completed/admin-restore-ops.md`. Use it as historical context for future
scheduler-linked admin follow-ons rather than as an active workstream.

MCP planning is tracked through the repository-level planning docs rather than a runtime execution
plan. Use `docs/MCP_INTEGRATION_STRATEGY.md`, `docs/MCP_TASK_MAP.md`, and
`docs/MCP_OAUTH_DCR_PLAN.md` before starting any MCP server, auth, or tool implementation work.
Runtime MCP is gated behind the OAuth/DCR prerequisite and should remain planning-only until the
roadmap workstream reaches it.

Completed work should move to `docs/exec-plans/completed/` once implementation and validation
notes are recorded.
