# Product Vision

This is the canonical current product vision for Application Tracker. Historical product analysis,
older roadmap drafts, and detailed feature plans may add background, but they should not override
this document.

## Product Thesis

Application Tracker is a private, self-hosted, local-first job-search workspace. It helps a
jobseeker decide what matters, capture and triage opportunities, prepare applications, manage
reusable artefacts, and preserve a private learning record across the search.

The product is not a kanban board with extra pages. The board remains useful as a workflow lens
over active work, but the strategic center is a Focus-led workspace for choosing and doing the next
useful job-search action.

## North Star

A jobseeker should be able to run the app, state what they are trying to achieve, capture roles
from fragmented external systems, see what needs attention now, work through an application with
the right artefacts and context, and keep a private record of what worked.

The first public version should feel like a calm job-search operating environment, not a generic
CRUD admin console, project-management board, or hidden AI agent.

## Target Users

Primary user:

- An individual jobseeker running a private local, NAS, homelab, or small VPS deployment.
- Needs fast capture, practical triage, application preparation, follow-up tracking, artefact
  reuse, and portable backups.
- Cares about privacy because the data includes resumes, salary expectations, preferences,
  recruiter messages, interview notes, and outcomes.

Secondary user:

- A small trusted group in one contained deployment, such as a household, coach, or peer group.
- Needs separate workspaces, admin recovery, and clear ownership boundaries.
- Does not need SaaS-scale tenancy, billing, or cross-organisation administration.

## Primary Surfaces

- Focus is the default command surface. It answers what needs attention now: due follow-ups,
  artefact reviews, stale jobs, active applications, interviews, recent captures, and missing next
  actions.
- Inbox is the intake and judgement surface. It holds captured, imported, recommended,
  low-confidence, or partially enriched opportunities until the user accepts, dismisses, or
  enriches them.
- Active Work is the workflow view for jobs already worth effort. Board, lane, and list views are
  allowed lenses, not the product center.
- Job Workspace is the execution surface for one opportunity. It combines role overview, current
  state, next action, application readiness, artefacts, notes, journal, and external application
  links.
- Artefacts are reusable working assets. Resumes, cover letters, narratives, attestations,
  portfolios, writing samples, and generated drafts should be attributable to jobs and outcomes.
- Capture brings jobs into the system from manual entry, browser extension, API, email capture, and
  later scheduled imports.
- Admin supports self-hosted operation: users, API tokens, backups, restore, scheduler runs,
  health, and deployment maintenance.

## Product Guardrails

- User goal first: organize surfaces around what the jobseeker is trying to achieve.
- Next action over raw status: status matters, but the app should make the next useful step visible.
- Calm and precise: prioritize scanning, reading, and repeated use over decorative or gamified UI.
- External systems are first-class: employer sites, ATS pages, email, calendars, and document tools
  remain part of the workflow.
- Intake paths stay distinct: intentional manual entry, captured intake, and system-recommended
  intake must not collapse into the same product meaning.
- Artefacts are strategic: the system should help select, tailor, and learn from application
  materials over time.
- AI is optional, visible, attributable, and non-mutating. It must never silently change jobs,
  profiles, artefacts, notes, or workflow state.
- Local-first by default: the core tracker must work without external services.
- Owner scoping, admin boundaries, and safe upload handling are non-negotiable.

## Current Planning Sources

Use these three hub documents for current planning:

- Vision: `docs/PRODUCT_VISION.md`
- Strategy and order of execution: `docs/roadmap/implementation-sequencing.md`
- Execution-ready task breakdown: `docs/roadmap/task-map.md`

Supporting references:

- User journeys and behavior contracts: `docs/product/product-brief.md` and
  `docs/product/user-journeys.md`
- Design system: `docs/design/DESIGN_SYSTEM.md`
- Architecture boundaries: `docs/architecture/index.md` and `docs/architecture/boundaries.md`
- Active execution plans: `docs/exec-plans/active/`
