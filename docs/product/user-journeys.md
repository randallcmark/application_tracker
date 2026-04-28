# User Journeys

Use this file for the workflows agents should understand and validate.

## Primary Journeys

### First-run setup and login

- User: self-hosting owner or first admin
- Goal: start a fresh deployment, create the first admin, and sign in safely
- Entry point: `/setup` on an empty deployment, then `/login`
- Main path: create first admin, sign in, reach Focus, use the shared shell
- Important states: empty deployment, authenticated home redirect, sign out
- Failure states: production guardrail misconfiguration, invalid credentials, setup disabled after first user
- Validation: auth and session tests, setup/login route checks, README and `docs/AUTHENTICATION.md`

### Focus daily triage

- User: authenticated jobseeker
- Goal: understand what needs attention today
- Entry point: `/focus`
- Main path: review due follow-ups, stale work, interviews, recent captures, and next-action gaps; navigate into job workspaces or intake flows
- Important states: empty state, populated state, visible AI nudge when enabled
- Failure states: no profile, no jobs, stale shell navigation, hidden primary action
- Validation: route/UI tests plus manual browser check against `docs/design/DESIGN_SYSTEM.md`

### Inbox review and acceptance

- User: authenticated jobseeker
- Goal: judge captured or recommended opportunities before spending effort
- Entry point: `/inbox` or `/inbox/email/new`
- Main path: inspect provenance, enrich fields, accept or dismiss, then move into active workflow
- Important states: low-confidence capture, email-captured opportunity, accepted transition, dismissed state
- Failure states: missing provenance, accidental direct activation, unclear enrichment path
- Validation: intake and owner-scope tests, Inbox route smoke, browser review against `docs/design/DESIGN_SYSTEM.md`

### Job Workspace execution

- User: authenticated jobseeker
- Goal: progress one role from review through application/follow-up work
- Entry point: job workspace/detail page
- Main path: inspect role overview, next action, readiness, activity, artefacts, notes, and external links; update workflow state without returning to the board
- Important states: no next action, long job description, collapsed journal/provenance, external workflow handoff
- Failure states: duplicate summary blocks, action clutter, mobile overlap, board-only workflows
- Validation: job detail tests, workspace reduction plan, browser review against `docs/design/DESIGN_SYSTEM.md`

### Artefact reuse and competency grounding

- User: authenticated jobseeker
- Goal: reuse existing artefacts and, when relevant, connect supporting evidence without hidden mutation
- Entry point: `/artefacts`, job workspace artefact actions, `/competencies`
- Main path: review artefact library, attach existing artefacts to jobs, inspect draft provenance, optionally use competency evidence as grounding for visible AI generation
- Important states: no artefacts, reused artefact, saved draft provenance, evidence-assisted tailoring
- Failure states: duplicate uploads when association was intended, hidden mutation of artefacts or evidence, thin-metadata confusion
- Validation: artefact and competency tests, manual UX review against `docs/design/DESIGN_SYSTEM.md` and `docs/design/COMPETENCY_EVIDENCE_UX.md`

### Admin backup and maintenance

- User: admin
- Goal: operate the self-hosted deployment safely
- Entry point: `/admin`
- Main path: inspect health, manage capture tokens, use setup/help/admin tools, download backup
- Important states: admin-only visibility, backup success path, health visibility
- Failure states: admin leakage to non-admin users, unclear maintenance path, unsafe defaults in production
- Validation: auth/admin tests, storage and docker-related tests, README operational docs

### Visible, non-mutating AI output flows

- User: authenticated jobseeker with or without configured providers
- Goal: generate contextual AI guidance without losing control of workflow state
- Entry point: Focus, Inbox review, Job Workspace, artefact actions, competency shaping
- Main path: trigger visible AI output, inspect provider/fallback result, optionally save explicit drafts or act manually
- Important states: provider-enabled generation, local fallback generation, visible attribution, disabled-AI operation
- Failure states: silent mutation, invisible provenance, provider error leakage, blocked core workflow without AI
- Validation: AI service tests, route tests, `docs/ARTEFACT_AI_PLAN.md`, browser review against `docs/design/DESIGN_SYSTEM.md`

## Regression Journeys

| Journey | Trigger For Testing | Validation Method |
| --- | --- | --- |
| First-run setup and login | Auth, sessions, setup, admin, or shell changes | Auth tests plus manual login/setup smoke |
| Focus daily triage | Focus, shell, profile, follow-up, or AI nudge changes | Focus route tests plus browser check |
| Inbox review and acceptance | Capture, email intake, Inbox, or intake model changes | Inbox/capture tests plus browser check |
| Job Workspace execution | Job detail, workflow actions, panes, or external action changes | Job detail tests plus browser check |
| Artefact reuse and competency grounding | Artefact library, draft provenance, competency, or grounding changes | Artefact/competency tests plus targeted browser check |
| Admin backup and maintenance | Authz, admin routes, storage, or Docker/backup changes | Admin/storage tests plus manual admin smoke |
| Visible AI output flows | Provider, prompt, visibility, fallback, or output-shape changes | AI tests plus targeted route/browser smoke |
