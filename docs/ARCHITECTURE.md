# Architecture

Application Tracker is being rebuilt as a small FastAPI monolith with a server-rendered UI and a documented integration API.

Initial architecture:

```text
Browser / extension / API client
        |
        v
FastAPI application
  |-- server-rendered UI
  |-- integration API
  |-- workflow services
  |-- ingestion services
        |
        v
SQL database + artefact storage
```

The database schema is managed by Alembic from the start. Runtime startup should not call `Base.metadata.create_all`; fresh installs and upgrades should run migrations explicitly.

Default local deployment:

- SQLite database in a persistent Docker volume.
- Local filesystem artefact storage in the same persistent volume.

Optional later deployment:

- MariaDB or Postgres-compatible database.
- S3-compatible artefact storage.
- Reverse proxy auth or local session auth.

The current product vision is in `docs/PRODUCT_VISION.md`.
The current delivery plan is in `docs/DELIVERY_PLAN.md`.
The resumable roadmap and historical staged backlog are in `project_tracker/PUBLIC_SELF_HOSTED_ROADMAP.md`.
The detailed authentication plan is in `docs/AUTHENTICATION.md`.
