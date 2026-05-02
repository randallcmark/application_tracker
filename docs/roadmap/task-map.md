# Task Map

This is the canonical execution-ready task breakdown for current Application Tracker workstreams.
Use it after reading `docs/PRODUCT_VISION.md` and `docs/roadmap/implementation-sequencing.md`.

## Workstream Snapshot

| Order | Workstream | Status | Entry Point | Next Slice |
| --- | --- | --- | --- | --- |
| 1 | Planning harness cleanup and doc consolidation | Active | `docs/exec-plans/active/harness-adoption-and-validator.md` | Finish three-hub routing, archive/mark superseded docs, and clean active/completed plans. |
| 2 | Inbox follow-ons | Active | `docs/exec-plans/active/inbox-follow-up.md` | Validate review-readiness behavior in use, then scope provider-backed ingestion only if needed. |
| 3 | Job Workspace reduction | Active | `docs/exec-plans/active/job-workspace-reduction.md` | Run any remaining larger-viewport manual validation, then close or defer minor polish. |
| 4 | Artefact AI / competency evidence continuation | Active | `docs/exec-plans/active/artefact-ai-g4-continuation.md` | G4 save-back, compact provenance, and model-backed evidence-link history are implemented; next slice is provider expansion. |
| 5 | AI provider expansion | Active | `docs/exec-plans/active/provider-expansion.md` | Anthropic, minimum-input provider setup, and model discovery are implemented; next slice is provider polish from real use or scheduler/worker. |
| 6 | Scheduler and worker | Active planning | `docs/exec-plans/active/scheduler-worker.md` | Define the minimal runtime shape before implementing background jobs. |
| 7 | Admin, restore, and self-hosted operations | Active planning | `docs/exec-plans/active/admin-restore-ops.md` | Inventory restore and operations gaps, then add restore validation and operational smoke coverage. |
| 8 | Deferred auth/provider modes | Deferred | `docs/AUTHENTICATION.md`, `docs/quality/technical-debt.md` | Re-scope when workflow and operations priorities are stable. |

## Planning Harness Cleanup And Doc Consolidation

Goal: keep future sessions from restarting from stale roadmap surfaces.

Acceptance criteria:

- `docs/PRODUCT_VISION.md`, `docs/roadmap/implementation-sequencing.md`, and this file are the
  only current planning hubs.
- README, AGENTS, product brief, agent index, and architecture index route readers to the three
  hubs.
- Superseded planning docs are archived or clearly marked historical.
- Completed execution plans are moved out of `docs/exec-plans/active/`.

Validation:

```sh
bash scripts/validate-harness.sh
```

Also run a targeted `rg` stale-reference scan for old "start here", public-roadmap, and
multi-roadmap guidance in README, AGENTS, agent docs, product brief, architecture index, and
roadmap docs.

Supporting docs:

- `docs/agent/doc-maintenance.md`
- `docs/quality/technical-debt.md`
- `docs/quality/quality-score.md`

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
2. Polish Tasks, Notes, and Documents only where validation exposes usability issues.
3. Reassess utility cards only after validation is complete.

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
4. Outcome-aware refinement remains deferred until evidence reuse has real usage.

Next slice:

- Move to AI provider expansion. Do not add outcome-aware refinement until evidence-link history has
  real usage.

Acceptance criteria:

- Evidence grounding is opt-in.
- AI output remains visible and attributable.
- Saving shaped evidence or generated artefacts is an explicit user action.
- The app still works when no AI provider is configured.
- Evidence-link history is owner-scoped and queryable without parsing `source_context`.

Validation:

```sh
make test
```

Supporting docs:

- `docs/ARTEFACT_AI_PLAN.md`
- `docs/COMPETENCY_EVIDENCE_PLAN.md`
- `docs/AI_READINESS.md`
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
6. Next provider slice should come from real-use polish, error-message gaps, or scheduler/worker
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

## Scheduler And Worker

Goal: add the smallest self-hosted background runtime that can support imports, reminders,
notifications, stale detection, optional mailbox ingestion, and optional AI processing.

Next slices:

1. Decide the minimal runtime shape and Compose impact.
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
