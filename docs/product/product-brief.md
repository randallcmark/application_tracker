# Product Brief

This is the product source of truth for agents. It summarizes the current product framing and routes to deeper planning docs when more detail is needed.

## Product

Application Tracker is a private, self-hosted, local-first job-search workspace. It helps a jobseeker decide what matters, capture and triage opportunities, prepare applications, manage reusable artefacts, and preserve a private learning record across the search.

The product is organized around Focus, Inbox, Active Work, Job Workspace, Artefacts, Capture, and Admin. The board remains a workflow view, not the strategic center.

Primary references:

- `docs/PRODUCT_VISION.md`
- `docs/DELIVERY_PLAN.md`
- `project_tracker/PUBLIC_SELF_HOSTED_ROADMAP.md`

## Users

- Primary user: an individual jobseeker running a private local, NAS, homelab, or small VPS deployment.
- Secondary user: a small trusted group in one contained deployment, such as a household, coach, or peer group, with separate workspaces and clear ownership boundaries.

## Core Jobs

| Job | User | Success Criteria |
| --- | --- | --- |
| Decide what deserves attention now | Jobseeker | Focus highlights due follow-ups, stale work, interviews, and missing next actions without dashboard noise. |
| Triage new opportunities before spending effort | Jobseeker | Inbox separates captured or recommended intake from active workflow until the user accepts, dismisses, or enriches it. |
| Prepare and progress one application end-to-end | Jobseeker | Job Workspace makes the next useful action, readiness, notes, artefacts, and external links obvious without returning to the board. |
| Reuse and improve application materials | Jobseeker | Artefacts remain reusable working assets linked to jobs, drafts, evidence, and outcomes. |
| Run the system privately and safely | Self-hosting user/admin | The app works locally first, preserves owner boundaries, and supports setup, backup, and maintenance without SaaS assumptions. |

## Non-Goals

- A generic admin console with job records.
- A board-first project-management product.
- Hidden AI automation that mutates workflow state.
- A hosted SaaS tenancy model.
- A passive document repository detached from job outcomes.

## Behavior Contracts

- Authenticated users land in Focus as the default daily command surface.
- Inbox is the judgment surface for low-confidence, captured, or system-recommended jobs before they become Active Work.
- Manual Add Job remains an intentional entry path separate from captured intake.
- The board remains available as a workflow lens over active work, but product decisions should not assume it is the center.
- Job Workspace must support progressing a role without requiring board round-trips.
- Artefacts are reusable working assets, not just passive file attachments.
- AI output must be visible, attributable, and non-mutating; the core product must still work when AI is disabled.
- Owner scoping, admin boundaries, and safe handling of uploads/artefacts are non-negotiable.

Reference docs for these contracts:

- `docs/PRODUCT_VISION.md`
- `docs/DELIVERY_PLAN.md`
- `docs/AUTHENTICATION.md`
- `docs/ARTEFACT_AI_PLAN.md`

## Open Product Questions

| Question | Impact | Owner |
| --- | --- | --- |
| How far should provider-backed email ingestion go beyond the current user-initiated paste/forward path? | Affects Inbox architecture, scheduler design, and privacy posture. | Product planning |
| When should Anthropic and additional provider modes move from planned to required? | Affects AI provider abstraction, settings UX, and validation expectations. | Product and implementation |
| What is the minimal scheduler/worker shape that supports imports, notifications, and optional AI processing without overcomplicating self-hosted deployment? | Affects deployment, runtime architecture, and operations docs. | Architecture/product |
| Which remaining Job Workspace panes should be simplified first after the current cleanup pass? | Affects UI sequencing and regression priorities. | Product/UI |
