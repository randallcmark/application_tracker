# Task Map

This is the canonical execution-ready task breakdown for current Application Tracker workstreams.
Use it after reading `docs/PRODUCT_VISION.md` and `docs/roadmap/implementation-sequencing.md`.

## Workstream Snapshot

| Order | Workstream | Status | Entry Point | Next Slice |
| --- | --- | --- | --- | --- |
| 1 | UI density, layout, and AI surface cleanup | Active | `docs/exec-plans/active/ui-density-layout-ai-cleanup.md` | Core QA cleanup is complete: compact headings, Focus, Inbox, Board, Job Workspace AI/documents polish, Competency Evidence workspace redesign, and the first artefact Markdown preview quality pass. |
| 2 | Inbox follow-ons | Active | `docs/exec-plans/active/inbox-follow-up.md` | Validate review-readiness behavior in use, then scope provider-backed ingestion only if needed. |
| 3 | Job Workspace reduction | Active | `docs/exec-plans/active/job-workspace-reduction.md` | Core pane cleanup and QA-driven polish are complete; next work should follow the dedicated section-workbench plan rather than ad hoc workspace patches. |
| 4 | Job Detail section workbenches | Active | `docs/exec-plans/active/job-detail-section-workbenches.md` | Define and then implement compact workbenches for Application, Interviews, Follow-Ups, Tasks, and Notes one section at a time. |
| 5 | Artefact AI / competency evidence continuation | Active | `docs/exec-plans/active/artefact-ai-g4-continuation.md` | Pasted-text employer rubric mapping is implemented; keep uploaded rubric documents and outcome-aware refinement deferred until real usage or document-handling needs justify them. |
| 6 | AI provider expansion | Active | `docs/exec-plans/active/provider-expansion.md` | Anthropic, minimum-input provider setup, and model discovery are implemented; next slice is provider polish from real use or document handling needs. |
| 7 | Document Handling Foundation | Active planning | `docs/exec-plans/active/document-handling-foundation.md` | Shared renderer now covers AI outputs and Job Workspace descriptions; artefact access is formalized behind a no-schema Markdown contract and the next slice should build on that boundary. |
| 8 | Scheduler and worker | Active planning | `docs/exec-plans/active/scheduler-worker.md` | Define the minimal runtime shape after document source/Markdown/provenance rules are stable. |
| 9 | Admin, restore, and self-hosted operations | Active planning | `docs/exec-plans/active/admin-restore-ops.md` | Inventory restore and operations gaps, then add restore validation and operational smoke coverage. |
| 10 | Deferred auth/provider modes | Deferred | `docs/AUTHENTICATION.md`, `docs/quality/technical-debt.md` | Re-scope when workflow and operations priorities are stable. |

Harness cleanup baseline is complete. Historical context now lives in
`docs/exec-plans/completed/harness-adoption-and-validator.md`; keep `bash scripts/validate-harness.sh`
passing and continue moving finished plans out of `docs/exec-plans/active/` promptly.

## UI Density, Layout, And AI Surface Cleanup

Goal: incorporate the latest UI QA backlog into repository-owned planning and make the core
authenticated pages cleaner, denser, and more action-oriented without changing workflow semantics.

Next slices:

1. Compact page headers are implemented for Focus, Inbox, Board, Add Job, Paste Email, Settings,
   Artefacts, and Competency Evidence.
2. Focus counters and priority surfaces are compact and actionable.
3. Inbox cards and right rail are compacted.
4. Board count/subtext duplication is removed.
5. Job Workspace AI, navigation, and document layout cleanup is complete for the current QA pass.
6. Competency Evidence workspace redesign is complete.
7. The first artefact Markdown preview quality pass is complete.
8. Job Detail section workbenches now continue through a dedicated active plan instead of this
   cleanup checklist.

Acceptance criteria:

- Main page headers use compact title-first hierarchy.
- Primary actions remain visible and unchanged.
- UI changes preserve owner scoping, route compatibility, and AI non-mutation rules.
- Browser validation is included for layout-affecting slices when feasible.

Validation:

```sh
bash scripts/validate-harness.sh
git diff --check
```

Supporting docs:

- `docs/exec-plans/active/ui-density-layout-ai-cleanup.md`
- `docs/agent/ui-ux-rules.md`
- `docs/design/DESIGN_SYSTEM.md`
- `docs/exec-plans/active/job-workspace-reduction.md`
- `docs/exec-plans/active/job-detail-section-workbenches.md`

## Inbox Follow-Ons

Goal: make intake review richer without losing the distinction between manual, captured, and
system-recommended opportunities.

Next slices:

1. Validate multi-candidate and review-readiness behavior against real pasted/captured examples.
2. Keep provider-specific parsing conservative and stop at provider-backed ingestion decisions unless
   the review model exposes a hard gap.
3. Scope provider-backed ingestion after the review model is stable.

Acceptance criteria:

- Inbox preserves provenance and review-before-activation semantics.
- One email can produce zero, one, or many review candidates without auto-activating jobs.
- Accepted and dismissed items remain owner-scoped and do not leak into active views incorrectly.
- Provider-backed ingestion is explicit and optional.

Validation:

```sh
make test
```

Supporting docs:

- `docs/INBOX.md`
- `docs/product/application_tracker_inbox_monitoring_decision_memo.md`
- `docs/product/user-journeys.md`

## Job Workspace Reduction

Goal: make the Job Workspace calmer and easier to execute from, especially on narrow screens.

Next slices:

1. Run any remaining larger-viewport manual checks not covered by the available browser viewport.
2. Treat further section redesign through `docs/exec-plans/active/job-detail-section-workbenches.md`
   rather than ad hoc workspace polish.
3. Reassess utility cards only after section-workbench changes expose a concrete need.

Acceptance criteria:

- The workspace remains a one-opportunity execution surface.
- Duplicate summaries and redundant actions are reduced.
- Mobile portrait remains readable and actionable.
- AI controls remain visible, optional, and non-mutating.

Validation:

```sh
make test
```

Include browser/manual checks for desktop and mobile widths when layout changes.

Supporting docs:

- `docs/JOB_WORKSPACE_REDUCTION_PLAN.md`
- `docs/JOB_DETAIL.md`
- `docs/design/DESIGN_SYSTEM.md`

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

Goal: add provider capability without changing product semantics or making AI mandatory.

Next slices:

1. Standard provider setup is normalized around one active provider per user and minimum viable
   user input.
2. Published service details are preconfigured for standard providers: OpenAI, Gemini, and
   Anthropic.
3. Model discovery is implemented for OpenAI, Gemini, Anthropic, and best-effort
   OpenAI-compatible endpoints.
4. Custom OpenAI-compatible setup remains explicit: friendly label, base URL, API token, and
   selected or manually entered model name.
5. Anthropic provider execution is implemented through the Messages API.
6. Next provider slice should come from real-use polish, error-message gaps, or document handling
   needs rather than adding more provider modes speculatively.

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

Goal: establish source-preserving, Markdown-first content handling before adding more
document-heavy AI, artefact, rubric, search, export, or background automation workflows.

Next slices:

1. Free-text Markdown rendering audit is complete. Historical audit:
   `docs/exec-plans/completed/free-text-markdown-rendering-audit.md`.
2. A shared safe Markdown renderer now covers AI outputs and Job Workspace
   `Job.description_raw`.
3. First artefact Markdown representation slice is complete in
   `docs/exec-plans/completed/artefact-markdown-representation.md`.
4. Keep current artefact behaviour computed/no-schema and route future feature work through the
   Markdown access contract instead of direct extraction helpers.
5. Move to persisted Markdown records only when the decision triggers in
   `docs/architecture/decisions/2026-05-02-artefact-markdown-access-contract.md` are met.
6. Keep uploaded rubric documents and richer rubric-source handling deferred until artefact/document
   handling reuse is explicit.
7. Defer search, FTS, embeddings, DOCX export, and PDF export until explicit decision docs exist.

Acceptance criteria:

- Source material remains canonical and downloadable or inspectable where applicable.
- Markdown is the internal working representation for rendered text, AI context, generated output,
  and future export preparation.
- Rendered Markdown goes through one safe sanitized path.
- AI prompts treat external source material as data, not instructions.
- Employer rubric mapping is not implemented before the Markdown foundation is in place.
- Search and export stay deferred until `docs/SEARCH_AND_RETRIEVAL_DECISION.md` and
  `docs/EXPORT_STRATEGY.md` are created by future decision work.

Validation:

```sh
bash scripts/validate-harness.sh
git diff --check
```

Supporting docs:

- `docs/DOCUMENT_HANDLING_STRATEGY.md`
- `docs/DOCUMENT_HANDLING_ARCHITECTURE.md`
- `docs/DOCUMENT_HANDLING_TASK_MAP.md`
- `docs/architecture/decisions/2026-05-02-markdown-first-document-handling.md`
- `docs/architecture/decisions/2026-05-02-artefact-markdown-access-contract.md`
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

Next slices:

1. Inventory restore and operations gaps.
2. Add backup restore dry-run validation before destructive restore behavior.
3. Add admin operational visibility and smoke checks alongside scheduler/runtime work.

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
