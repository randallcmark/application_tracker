# Task Map

This is the canonical execution-ready task breakdown for current Application Tracker workstreams.
Use it after reading `docs/PRODUCT_VISION.md` and `docs/roadmap/implementation-sequencing.md`.

## Workstream Snapshot

| Order | Workstream | Status | Entry Point | Next Slice |
| --- | --- | --- | --- | --- |
| 1 | Artefact AI / competency evidence continuation | Active | `docs/exec-plans/active/artefact-ai-g4-continuation.md` | Pasted-text employer rubric mapping is implemented; keep uploaded rubric documents and outcome-aware refinement deferred until real usage or document-handling needs justify them. |
| 2 | Scheduler and worker | Active planning | `docs/exec-plans/active/scheduler-worker.md` | Define the minimal runtime shape after document source/Markdown/provenance rules are stable. |
| 3 | Admin, restore, and self-hosted operations | Completed | `docs/exec-plans/completed/admin-restore-ops.md` | Runtime visibility, backup download, restore dry-run validation, and self-hosted backup/restore docs are complete. Resume only if object-management or scheduler-linked admin follow-ons justify a new slice. |
| 4 | MCP integration planning and auth prerequisite | Active planning | `docs/MCP_INTEGRATION_STRATEGY.md`, `docs/MCP_TASK_MAP.md` | Keep MCP at planning level; next slice is to choose deployment mode and turn the OAuth/DCR prerequisite into execution-ready implementation work after document/Markdown handling is closed. |
| 5 | UI/UX technical debt | Active planning | `docs/quality/technical-debt.md` | Keep broad responsive/polish debt centralized here instead of reopening ad hoc UI cleanup workstreams. |
| 6 | Job Detail section workbenches | Completed | `docs/exec-plans/completed/job-detail-section-workbenches.md` | Section workbench implementation and targeted validation are complete. Resume only if new workspace issues justify a dedicated follow-on slice. |
| 7 | Inbox follow-ons | Deferred | `docs/exec-plans/active/inbox-follow-up.md` | Leave provider/board-specific ingestion logic deferred until a later planning pass justifies the complexity. |
| 8 | AI provider expansion | Deferred | `docs/exec-plans/active/provider-expansion.md` | OpenAI, Gemini, Anthropic, and configurable OpenAI-compatible setup are sufficient for now; defer further provider work. |
| 9 | Deferred auth/provider modes | Deferred | `docs/AUTHENTICATION.md`, `docs/quality/technical-debt.md` | Re-scope when workflow and operations priorities are stable. |

Harness cleanup baseline is complete. Historical context now lives in
`docs/exec-plans/completed/harness-adoption-and-validator.md`; keep `bash scripts/validate-harness.sh`
passing and continue moving finished plans out of `docs/exec-plans/active/` promptly.

Document Handling Foundation is complete in
`docs/exec-plans/completed/document-handling-foundation.md`. The shared renderer, no-schema
Markdown access contract, search/retrieval decision, and export strategy now form the settled
document boundary for later work.

## Artefact AI / Competency Evidence Continuation

Goal: continue artefact-local AI and competency evidence grounding with explicit provenance and no
hidden mutation.

Current status:

1. Explicit save-back for AI-shaped STAR responses is implemented as a user action.
2. Artefact-local tailoring/draft outputs preserve resolved evidence UUIDs, compact visible
   evidence references in output metadata, and model-backed evidence-link history.
3. The model-backed evidence-link history stores generation-time evidence snapshots for later reuse
   reporting, audit, and outcome-aware refinement.
4. Employer rubric mapping is implemented for the first pasted-text slice through visible
   `employer_competency_mapping` output in the competency library.
5. Outcome-aware refinement remains deferred until evidence reuse has real usage.

Next slices:

1. Keep outcome-aware refinement deferred until evidence-link history has real usage.
2. Keep uploaded rubric documents deferred until artefact/document handling reuse is explicit.
3. Revisit rubric mapping only when real usage exposes gaps in preparation output or source
   handling.

Acceptance criteria:

- Evidence grounding is opt-in.
- AI output remains visible and attributable.
- Saving shaped evidence or generated artefacts is an explicit user action.
- The app still works when no AI provider is configured.
- Evidence-link history is owner-scoped and queryable without parsing `source_context`.
- Employer rubric mapping remains preparation support and must not fabricate or silently mutate
  evidence.

Validation:

```sh
make test
```

Supporting docs:

- `docs/exec-plans/active/artefact-ai-g4-continuation.md`
- `docs/ARTEFACT_AI_PLAN.md`
- `docs/COMPETENCY_EVIDENCE_PLAN.md`
- `docs/AI_READINESS.md`
- `docs/DOCUMENT_HANDLING_STRATEGY.md`
- `docs/design/COMPETENCY_EVIDENCE_UX.md`

## Job Detail Section Workbenches

Status: completed

Goal: finish the compact execution redesign inside Job Workspace one section at a time without
reopening broad shell or generic polish work.

Completion summary:

1. Application, Interviews, Follow-Ups, Tasks, and Notes now use compact workbench structure.
2. Targeted overflow and wrapping fixes were validated after implementation.
3. Resume only if new workspace issues justify a dedicated follow-on slice.

## Inbox Follow-Ons

Status: deferred

Goal: make intake review richer without losing the distinction between manual, captured, and
system-recommended opportunities.

Next slices:

1. Leave provider/board-specific parsing deferred until a later planning pass justifies the
   complexity.
2. Resume only if real use shows a review-readiness gap that current pasted-email handling cannot
   cover.

Acceptance criteria:

- Inbox preserves provenance and review-before-activation semantics.
- One email can produce zero, one, or many review candidates without auto-activating jobs.
- Accepted and dismissed items remain owner-scoped and do not leak into active views incorrectly.
- Provider-backed ingestion is explicit and optional when resumed.

Validation:

```sh
make test
```

Supporting docs:

- `docs/INBOX.md`
- `docs/product/application_tracker_inbox_monitoring_decision_memo.md`
- `docs/product/user-journeys.md`

## Artefact AI / Competency Evidence Continuation

Goal: continue artefact-local AI and competency evidence grounding with explicit provenance and no
hidden mutation.

Current status:

1. Explicit save-back for AI-shaped STAR responses is implemented as a user action.
2. Artefact-local tailoring/draft outputs preserve resolved evidence UUIDs, compact visible
   evidence references in output metadata, and model-backed evidence-link history.
3. The model-backed evidence-link history stores generation-time evidence snapshots for later reuse
   reporting, audit, and outcome-aware refinement.
4. Employer rubric mapping is implemented for the first pasted-text slice through visible
   `employer_competency_mapping` output in the competency library.
5. Outcome-aware refinement remains deferred until evidence reuse has real usage.

Next slices:

1. Keep outcome-aware refinement deferred until evidence-link history has real usage.
2. Keep uploaded rubric documents deferred until artefact/document handling reuse is explicit.
3. Revisit rubric mapping only when real usage exposes gaps in preparation output or source
   handling.

Acceptance criteria:

- Evidence grounding is opt-in.
- AI output remains visible and attributable.
- Saving shaped evidence or generated artefacts is an explicit user action.
- The app still works when no AI provider is configured.
- Evidence-link history is owner-scoped and queryable without parsing `source_context`.
- Employer rubric mapping remains preparation support and must not fabricate or silently mutate
  evidence.

Validation:

```sh
make test
```

Supporting docs:

- `docs/ARTEFACT_AI_PLAN.md`
- `docs/COMPETENCY_EVIDENCE_PLAN.md`
- `docs/AI_READINESS.md`
- `docs/DOCUMENT_HANDLING_STRATEGY.md`
- `docs/design/COMPETENCY_EVIDENCE_UX.md`

## AI Provider Expansion

Status: deferred

Goal: add provider capability without changing product semantics or making AI mandatory.

Next slices:

1. OpenAI, Gemini, Anthropic, and configurable OpenAI-compatible setup are sufficient for the
   current product surface.
2. Defer further provider work unless real use exposes a concrete provider gap that MCP does not
   supersede.

Acceptance criteria:

- Provider settings remain owner-scoped.
- Only one provider is active per user.
- Standard providers do not ask for endpoint details; users supply only an API token plus optional
  friendly label, then select from discovered models.
- Custom OpenAI-compatible providers ask for the extra endpoint fields needed to work and allow
  manual model entry if discovery fails.
- Disabled or misconfigured providers produce clear visible errors and no hidden mutation.
- Shared AI output contracts remain stable.

Validation:

```sh
make test
```

Supporting docs:

- `docs/AI_READINESS.md`
- `docs/agent/ai-feature-rules.md`

## Document Handling Foundation

Status: completed

Goal: close the source-preserving, Markdown-first document-handling foundation before adding more
document-heavy AI, MCP-dependent Markdown features, search, export, or background automation
workflows.

Next slices:

1. Free-text Markdown rendering audit is complete. Historical audit:
   `docs/exec-plans/completed/free-text-markdown-rendering-audit.md`.
2. A shared safe Markdown renderer now covers AI outputs and Job Workspace
   `Job.description_raw`.
3. First artefact Markdown representation slice is complete in
   `docs/exec-plans/completed/artefact-markdown-representation.md`.
4. Keep current artefact behaviour computed/no-schema and route future feature work through the
   Markdown access contract instead of direct extraction helpers.
5. Close the foundation by deciding whether one more foundation slice is required or whether the
   remaining document work is intentionally deferred behind later dedicated decisions.
6. Move to persisted Markdown records only when the decision triggers in
   `docs/architecture/decisions/2026-05-02-artefact-markdown-access-contract.md` are met.
7. Keep uploaded rubric documents and richer rubric-source handling deferred until artefact/document
   handling reuse is explicit.
8. Defer search, FTS, embeddings, DOCX export, and PDF export until explicit decision docs exist.
   Search and retrieval now has its decision doc in `docs/SEARCH_AND_RETRIEVAL_DECISION.md`, and
   export now has its decision doc in `docs/EXPORT_STRATEGY.md`.

Acceptance criteria:

- Source material remains canonical and downloadable or inspectable where applicable.
- Markdown is the internal working representation for rendered text, AI context, generated output,
  and future export preparation.
- Rendered Markdown goes through one safe sanitized path.
- The foundation is explicit enough that MCP and later search/export planning can depend on the
  Markdown boundary without re-deciding the representation.
- AI prompts treat external source material as data, not instructions.
- Employer rubric mapping is not implemented before the Markdown foundation is in place.
- Search and export stay deferred until `docs/SEARCH_AND_RETRIEVAL_DECISION.md` and
  `docs/EXPORT_STRATEGY.md` are created by future decision work. Both requirements are now met.

Validation:

```sh
bash scripts/validate-harness.sh
git diff --check
```

Supporting docs:

- `docs/DOCUMENT_HANDLING_STRATEGY.md`
- `docs/DOCUMENT_HANDLING_ARCHITECTURE.md`
- `docs/DOCUMENT_HANDLING_TASK_MAP.md`
- `docs/SEARCH_AND_RETRIEVAL_DECISION.md`
- `docs/EXPORT_STRATEGY.md`
- `docs/architecture/decisions/2026-05-02-markdown-first-document-handling.md`
- `docs/architecture/decisions/2026-05-02-artefact-markdown-access-contract.md`

## UI/UX Technical Debt

Goal: keep broad cross-surface polish, responsive hardening, and remaining UI regressions in one
intentional debt track so they do not get lost or leak into unrelated feature slices.

Current status:

1. The broad UI density/layout cleanup pass is complete and preserved in
   `docs/exec-plans/completed/ui-density-layout-ai-cleanup.md`.
2. The broad Job Workspace reduction/polish pass is complete and preserved in
   `docs/exec-plans/completed/job-workspace-reduction.md`.
3. Remaining UI issues should now be resumed through this debt track or through the dedicated Job
   Detail section-workbench plan, not by reopening broad ad hoc polish plans.

Next slices:

1. Keep shell/header overflow issues, mobile portrait hardening, and similar cross-surface polish in
   `docs/quality/technical-debt.md`.
2. Use dedicated feature plans when a UI change is really part of a feature or workbench redesign,
   not generic debt.
3. Re-run browser/manual validation when layout changes land elsewhere so resolved polish work does
   not regress quietly.

Acceptance criteria:

- UI debt remains visible in one canonical place.
- Finished broad polish plans stay archived rather than lingering in `active/`.
- Cross-surface layout debt does not get mixed into unrelated feature implementation by default.

Validation:

```sh
bash scripts/validate-harness.sh
git diff --check
```

Supporting docs:

- `docs/quality/technical-debt.md`
- `docs/exec-plans/completed/ui-density-layout-ai-cleanup.md`
- `docs/exec-plans/completed/job-workspace-reduction.md`

## MCP Integration Planning And Auth Prerequisite

Goal: treat MCP as an alternative AI execution path for Application Tracker without bypassing the
product’s visible-output, owner-scoped, non-mutating rules.

Current status:

1. Strategy, architecture, security, tool-contract, task-map, and OAuth/DCR prerequisite planning
   docs exist.
2. MCP is explicitly framed as optional and as a complement to the existing UI and provider-backed
   AI path, not a replacement for either.
3. Production-quality MCP runtime support is gated behind OAuth 2.0 with Dynamic Client
   Registration or a deliberate documented self-hosted equivalent.

Next slices:

1. Decide first deployment mode: embedded FastAPI surface, sidecar service, or local CLI/server.
2. Convert the OAuth/DCR prerequisite into execution-ready implementation planning for registered
   clients, scoped consent, token issuance/revocation, and audit foundations.
3. Keep V1 runtime scope narrow: read-scoped context plus visible Markdown `ai_output_create`.
4. Defer workflow mutation, destructive writes, and broad account/admin access until the scope,
   confirmation, and audit model is proven.

Acceptance criteria:

- MCP remains disabled unless explicitly configured.
- Runtime MCP is not treated as a static API-token feature in production.
- Tool naming and schemas stay domain-oriented, stable, and owner-scoped.
- External AI clients can only save visible, attributable outputs in the first runtime slice.
- MCP does not outrank current workflow, document-handling, or operational work.

Validation:

```sh
bash scripts/validate-harness.sh
git diff --check
```

Supporting docs:

- `docs/MCP_INTEGRATION_STRATEGY.md`
- `docs/MCP_TOOL_CONTRACTS.md`
- `docs/MCP_ARCHITECTURE_PLAN.md`
- `docs/MCP_SECURITY_MODEL.md`
- `docs/MCP_TASK_MAP.md`
- `docs/MCP_OAUTH_DCR_PLAN.md`
- `docs/exec-plans/completed/free-text-markdown-rendering-audit.md`
- `docs/exec-plans/completed/artefact-markdown-representation.md`

## Scheduler And Worker

Goal: add the smallest self-hosted background runtime that can support imports, reminders,
notifications, stale detection, optional mailbox ingestion, and optional AI processing.

Next slices:

1. Decide the minimal runtime shape and Compose impact after document source/Markdown/provenance
   rules are stable.
2. Add scheduler run records and admin visibility.
3. Add one background task path at a time, feeding visible surfaces.

Acceptance criteria:

- Scheduler can be disabled.
- Failed background jobs do not break the web app.
- Background outputs feed Focus, Inbox, or Admin visibly.
- Docker/QNAP deployment guidance remains simple.

Validation:

```sh
make test
make docker-import-smoke
```

Supporting docs:

- `docs/architecture/index.md`
- `docs/DOCKER_DEPLOYMENT.md`
- `docs/DELIVERY_PLAN.md`

## Admin, Restore, And Self-Hosted Operations

Goal: make private self-hosted operation trustworthy.

Current status:

1. Admin runtime visibility is available on `/admin`.
2. Backup download and restore dry-run validation are implemented.
3. Deployment docs cover the validated manual restore flow.

Resume only if:

1. Scheduler/worker work needs admin run visibility.
2. Object-management pages become necessary.
3. Real self-hosted use exposes an operational gap not covered by the current backup/restore flow.

Acceptance criteria:

- Admin-only operations stay clearly separated from daily workflow navigation.
- Restore validates archive shape before replacing data.
- Deployment docs cover migration, first admin, backup, restore, and upgrade flow.
- Runtime databases, uploads, and private artefacts remain excluded from Git.

Validation:

```sh
make test
make docker-import-smoke
```

Supporting docs:

- `docs/DOCKER_DEPLOYMENT.md`
- `docs/AUTHENTICATION.md`
- `docs/product/user-journeys.md`

## Deferred Auth / Provider Modes

Goal: keep future auth and provider expansion visible without letting it displace core workflow
work.

Resume when:

- Inbox, workspace, artefact AI, scheduler, and operations priorities are stable.
- A concrete deployment need requires OIDC, proxy auth, or broader provider behavior.

Supporting docs:

- `docs/AUTHENTICATION.md`
- `docs/quality/technical-debt.md`
