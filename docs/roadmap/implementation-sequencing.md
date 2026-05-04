# Implementation Sequencing

This is the canonical current strategy and order of execution. It answers what to work on next and
why. Use `docs/roadmap/task-map.md` for execution-ready workstream detail.

## Current Sequence

Planning harness cleanup is complete enough to leave active execution. Keep the validator passing
and historical plans archived, but resume product work from the current active workstreams below.

1. Artefact AI and competency evidence continuation.
   Resume the active G4 grounding milestone after workspace and intake surfaces are better framed.
   Keep selected evidence opt-in, visible, attributable, and non-mutating.

2. Scheduler and worker.
   Add the smallest self-hosted background runtime once Inbox inputs and visible output surfaces are
   clear and document handling has a stable source/Markdown/provenance model. Protect Docker/QNAP
   deployment simplicity and keep scheduler output visible in Focus, Inbox, or Admin.

3. MCP integration planning and auth prerequisite.
   Keep MCP as a planning workstream for now, not an implementation shortcut. Treat it as an
   alternative AI execution path that preserves the app as system of record, stays optional, and
   begins with read-scoped context plus visible Markdown output creation only. Do not start runtime
   MCP exposure before document/Markdown handling is closed to the planned boundary and the OAuth
   2.0 / Dynamic Client Registration prerequisite, deployment mode, scope model, and consent/audit
   shape are settled.

4. UI/UX technical debt.
   Treat remaining broad polish, responsive hardening, shell overflow issues, and future
   cross-surface refinements as a single debt track so they do not drift into unrelated feature
   work. Resume it intentionally after the current document-handling and section-workbench tracks
   rather than reopening ad hoc UI cleanup streams.

5. Deferred follow-on work.
   Leave Inbox provider/board-specific ingestion logic and further AI provider expansion deferred
   for now. Resume them only if real use exposes concrete gaps that justify the extra complexity.

6. Deferred auth/provider modes.
   Resume OIDC, proxy auth, or broader provider modes only after the higher-priority workflow and
   operations work is stable.

## Recently Closed

Document Handling Foundation is complete and preserved in
`docs/exec-plans/completed/document-handling-foundation.md`.

Admin, restore, and self-hosted operations are complete in
`docs/exec-plans/completed/admin-restore-ops.md`. The admin surface now exposes runtime details,
backup download, and restore dry-run validation, and the deployment docs cover the validated manual
restore flow.

The foundation now has:

- a shared safe Markdown rendering path;
- a no-schema artefact Markdown access contract;
- `docs/SEARCH_AND_RETRIEVAL_DECISION.md`;
- `docs/EXPORT_STRATEGY.md`.

Later document-heavy work should build on that settled boundary rather than reopen representation,
search, or export assumptions by default.

## Sequencing Rules

- Prefer work that clarifies current user workflows before work that automates or schedules them.
- Do not add hidden automation before the review surface, provenance, and failure mode are explicit.
- Keep AI optional and visible; provider expansion should not drive product sequencing by itself.
- Put document-heavy automation behind source preservation, safe Markdown rendering, and visible
  provenance.
- Treat broad UI/UX refinement as a managed debt track, not as incidental work mixed into unrelated
  feature slices.
- Treat MCP as an alternative AI execution path, not a replacement for the UI or a shortcut around
  provider, auth, provenance, or workflow rules.
- Do not expose MCP runtime tools before OAuth/DCR, scope enforcement, consent, revocation, and
  owner-scoped auditability are planned well enough to implement coherently.
- Protect local-first and self-hosted deployment simplicity when adding background runtime.
- Move completed execution plans out of `docs/exec-plans/active/` promptly so active work remains
  easy to scan.

## How To Resume Work

1. Read `docs/PRODUCT_VISION.md`.
2. Read this file to confirm priority order.
3. Read `docs/roadmap/task-map.md` for the current workstream breakdown.
4. Open only the active execution plan and supporting feature docs for the selected workstream.
