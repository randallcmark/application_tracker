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

Default local deployment:

- SQLite database in a persistent Docker volume.
- Local filesystem artefact storage in the same persistent volume.

Optional later deployment:

- MariaDB or Postgres-compatible database.
- S3-compatible artefact storage.
- Reverse proxy auth or local session auth.

The detailed staged plan is in `project_tracker/PUBLIC_SELF_HOSTED_ROADMAP.md`.

