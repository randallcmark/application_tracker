# Agent Instructions

This file is a map, not a manual. Keep it short enough to stay in context.

## Start Here

1. Read this file.
2. Read `docs/agent/index.md`.
3. For product or roadmap work, start with the three planning hubs:
   - Vision: `docs/PRODUCT_VISION.md`
   - Strategy/order: `docs/roadmap/implementation-sequencing.md`
   - Task breakdown: `docs/roadmap/task-map.md`
4. Read only the deeper docs relevant to the task.
5. For complex work, create or update an execution plan in `docs/exec-plans/active/`.

## Operating Rules

- Do not invent product behavior.
- Do not make broad refactors without an execution plan.
- Prefer small, reviewable changes.
- Update docs when behavior, validation, or durable constraints change.
- Run the documented validation commands before proposing completion.
- If the agent gets stuck, improve the harness with the missing doc, route, check, or script.
- Treat repository-local docs as the system of record. External guidance must be captured locally before it becomes policy.
- Preserve user work. Do not revert unrelated changes.

## Product Guardrails

- Application Tracker is a private, self-hosted, local-first job-search workspace organized around Focus, Inbox, Active Work, Job Workspace, Artefacts, Capture, and Admin.
- Do not treat the product as a kanban board with extra pages or as a generic CRUD admin console. The board is a workflow lens, not the product center.
- Preserve user-goal-first flows, next-action emphasis, calm low-friction UI, external job-system awareness, artefact reuse, and optional visible AI.
- Preserve the distinction between intentional manual entry, captured intake, and system-recommended intake.

## Technical Guardrails

- The app is a server-rendered FastAPI monolith using SQLAlchemy, Alembic, SQLite/local storage defaults, Docker support, and owner-scoped authenticated workflows.
- Improve separation incrementally: domain/service logic first, persistence behind clear helpers, and UI rendering kept readable without broad framework churn.
- Preserve owner scoping, admin boundary safety, safe local upload handling, and route compatibility unless docs and tests explicitly cover the change.
- AI must never silently mutate jobs, profiles, artefacts, notes, or workflow state. Store AI output visibly with source context, and keep the app useful when AI is disabled.

## Routing

- Product vision and roadmap: `docs/PRODUCT_VISION.md`, `docs/roadmap/implementation-sequencing.md`, and `docs/roadmap/task-map.md`.
- Product behavior: `docs/product/product-brief.md` and `docs/product/user-journeys.md`.
- Architecture work: `docs/architecture/index.md`, `docs/architecture/boundaries.md`, and `docs/architecture/decisions/`.
- Document handling, Markdown rendering, source preservation, search, or export: `docs/DOCUMENT_HANDLING_STRATEGY.md`, `docs/DOCUMENT_HANDLING_ARCHITECTURE.md`, and `docs/DOCUMENT_HANDLING_TASK_MAP.md`.
- Task slicing, risk, and model guidance: `docs/agent/codex-routing.md`.
- UI work: `docs/agent/ui-ux-rules.md` and `docs/design/DESIGN_SYSTEM.md`.
- AI work: `docs/agent/ai-feature-rules.md`.
- Security-sensitive work: `docs/agent/security-rules.md`.
- Validation: `docs/agent/validation.md`.
- Documentation maintenance: `docs/agent/doc-maintenance.md`.
- Roadmap and active workstreams: `docs/roadmap/task-map.md`, `docs/roadmap/implementation-sequencing.md`, and `docs/exec-plans/active/`.
- Quality gaps: `docs/quality/technical-debt.md` and `docs/quality/quality-score.md`.
