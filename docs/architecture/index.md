# Architecture Index

This directory is the system map for Application Tracker.

## System Summary

Application Tracker is a small FastAPI monolith with a server-rendered authenticated UI and a documented integration API. It uses SQLAlchemy models and Alembic migrations for persistence, SQLite and local filesystem storage by default, and Docker Compose for the primary self-hosted deployment path. The runtime is organized around owner-scoped workflows for Focus, Inbox, Board/Active Work, Job Workspace, Artefacts, Capture, Profile, Competencies, and Admin.

The application entrypoint is `app/main.py`. Route modules under `app/api/routes/` currently render HTML and expose JSON or form actions. Domain behavior is concentrated in `app/services/`. Authentication and authorization concerns live under `app/auth/` plus API dependencies in `app/api/`. Database setup and models live under `app/db/`, while artefact storage abstraction lives under `app/storage/`. Optional AI/provider behavior is integrated through the service layer and persisted visibly through owner-scoped models.

## Subsystems

| Subsystem | Purpose | Owner Doc |
| --- | --- | --- |
| Server-rendered UI routes | Authenticated HTML surfaces and related form flows for Focus, Inbox, Board, Job Workspace, Artefacts, settings, and admin | `docs/product/user-journeys.md` |
| Integration API routes | Capture, health, and authenticated route actions used by extensions or internal surfaces | `docs/JOBS_API.md` |
| Domain services | Business logic for jobs, profiles, artefacts, capture, inbox/email intake, interviews, competencies, and AI | `docs/architecture/boundaries.md` |
| Auth/session/token layer | Local auth, sessions, CSRF, API tokens, user ownership, and admin access | `docs/AUTHENTICATION.md` |
| Persistence/models/migrations | SQLAlchemy models, session setup, and Alembic-managed schema evolution | `docs/ARCHITECTURE.md` |
| Storage adapters | Provider abstraction, path safety, and local artefact storage | `docs/ARTEFACTS.md` |
| Document handling | Source-preserving, Markdown-first handling for free text, AI output, artefact working representations, future search, and export | `docs/DOCUMENT_HANDLING_ARCHITECTURE.md` |
| AI/provider integrations | Visible AI outputs, provider settings, encrypted key storage, and provider execution paths | `docs/AI_READINESS.md` |
| Docker/self-hosted runtime | Compose deployment, persistent data, admin setup, backup, and operational guidance | `docs/DOCKER_DEPLOYMENT.md` |

## Architecture Routes

- Boundaries and dependency rules: `docs/architecture/boundaries.md`.
- Decision records: `docs/architecture/decisions/`.
- Document handling strategy: `docs/DOCUMENT_HANDLING_STRATEGY.md`,
  `docs/DOCUMENT_HANDLING_ARCHITECTURE.md`, and `docs/DOCUMENT_HANDLING_TASK_MAP.md`.
- Product vision and roadmap: `docs/PRODUCT_VISION.md`, `docs/roadmap/implementation-sequencing.md`, and `docs/roadmap/task-map.md`.
- Product behavior contracts: `docs/product/product-brief.md`.
- Quality gaps: `docs/quality/technical-debt.md`.

## Dependency Policy

The project uses `pip` with `pyproject.toml` extras for development dependencies. Add dependencies only when the current FastAPI monolith and validation surface cannot solve the problem cleanly. Security-sensitive or runtime-shape-changing dependencies require architecture and security review plus validation updates.

## Change Rules

- Do not introduce a new architectural pattern without an execution plan.
- Do not add a cross-subsystem dependency without checking boundary rules.
- Prefer boring, inspectable technologies unless a decision record explains otherwise.
- Add or update an architecture decision record for durable tradeoffs.
