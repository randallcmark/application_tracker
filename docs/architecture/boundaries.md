# Architecture Boundaries

Use this file to make architecture legible and enforceable.

## Current Boundary Model

Application Tracker currently follows a pragmatic monolith boundary model:

- `app/api/routes/`: HTTP boundary, request parsing, auth dependencies, HTML/JSON responses, and form wiring.
- `app/services/`: domain behavior and orchestration for jobs, intake, artefacts, competencies, AI, and related workflows.
- `app/auth/`: password, session, token, CSRF, and user/auth helpers.
- `app/db/`: database configuration and ORM models.
- `app/storage/`: artefact storage abstraction and path/provider safety.
- `app/core/`: configuration and global runtime settings.

Some route modules still contain HTML and light workflow composition. Move logic out incrementally when touching those areas; do not rewrite the app to force a purer layering model in one pass.

## Allowed Dependencies

| From | May Depend On | Notes |
| --- | --- | --- |
| `app/api/routes` | `app/api`, `app/auth`, `app/services`, `app/db`, `app/core` | Routes may compose services and auth dependencies but should avoid owning business rules. |
| `app/services` | `app/db`, `app/storage`, `app/auth`, `app/core` | Services own workflow logic and can orchestrate persistence and provider calls. |
| `app/auth` | `app/db`, `app/core` | Auth helpers may read/write auth-related persistence but should not depend on product services. |
| `app/storage` | `app/core` | Storage stays infrastructure-focused and product-agnostic. |
| `app/db` | `app/core` | Models and session setup should not depend on routes or services. |

## Disallowed Dependencies

| Rule | Reason | Enforcement |
| --- | --- | --- |
| `app/db` must not depend on `app/services` or `app/api` | Persistence should stay below domain and HTTP layers. | Documented only; no import check yet. |
| `app/storage` must not depend on route or product workflow modules | Storage should remain reusable and safety-focused. | Documented only; no import check yet. |
| `app/auth` must not depend on product-specific services | Auth boundaries should remain reusable and auditable. | Documented only; no import check yet. |
| AI/provider code must not silently mutate workflow state | Product rule: AI output is visible, optional, and inspectable. | Enforced partially through tests and docs. |

## Boundary Rules

- Shared utilities must not accumulate product behavior.
- External systems should enter through explicit adapters or service/provider helpers.
- Data from browser capture, email intake, providers, or uploads must be validated at the boundary.
- Cross-cutting concerns such as auth, ownership, storage, and configuration should use explicit helpers.
- Route modules may keep local HTML/CSS while the app is server-rendered, but domain rules should move into services before adding more complexity.

## Enforcement

Current enforcement is partial:

- owner-scoping, auth, and route behavior are covered by pytest suites;
- migration discipline is enforced by Alembic usage and tests;
- no dedicated import-lint or architecture check exists yet.

Record enforcement gaps and future checks in `docs/quality/technical-debt.md`.
