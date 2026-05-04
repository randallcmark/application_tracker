# Application Tracker

Application Tracker is a self-hosted, goal-aware job-search workspace for capturing roles, deciding what deserves attention, preparing applications, managing artefacts, and learning what works during a job search.

## Product Direction

The target product is:

- container-first and easy to self-host;
- local-first, with SQLite and local storage defaults;
- optionally multi-user inside one contained deployment;
- organised around Focus, Inbox, Active Work, Job Workspace, Artefacts, Capture, and Admin surfaces;
- uses a shared application shell with primary workflow navigation and a user-context menu for
  settings, capture setup, help, sign-out, and admin tools;
- workflow-board friendly for stage management without making kanban the product centre;
- browser-capture friendly for importing jobs from job pages;
- profile-aware over time, with optional visible AI guidance and writing assistance;
- private by default, with no required external services.

The board remains an important workflow view, especially for active applications, but the planned product direction is a focus-led workspace: the app should help the user understand what matters today, triage new opportunities, prepare strong applications, preserve context across external systems, and reuse artefacts intelligently.

Current planning starts with the three hub documents:

- Vision: `docs/PRODUCT_VISION.md`
- Strategy and order of execution: `docs/roadmap/implementation-sequencing.md`
- Execution-ready task breakdown: `docs/roadmap/task-map.md`

Current planning also includes active document-handling, AI/provider, and MCP planning tracks. MCP
is planning-only today and is framed as an alternative AI execution path, not a replacement for
the UI or the app’s visible-output rules.

### Product strategy and design docs

For supporting product background and UI handoff artifacts, see:

- `docs/product/application_tracker_product_doc_set_index.md`
- `docs/product/application_tracker_inbox_monitoring_decision_memo.md`
- `docs/ui/application_tracker_ui_mockup_inspectable.html`
- `docs/ui/handoff/README.md`

API token and browser capture examples live in:

- `docs/API_TOKENS_AND_CAPTURE.md`
- `docs/FIREFOX_EXTENSION.md`

Jobs API examples live in:

- `docs/JOBS_API.md`

User profile and intent notes live in:

- `docs/USER_PROFILE.md`

Focus surface notes live in:

- `docs/FOCUS.md`

Inbox notes live in:

- `docs/INBOX.md`

The visual design system lives in:

- `docs/design/DESIGN_SYSTEM.md`

Workflow board notes live in:

- `docs/KANBAN_BOARD.md`

Job detail page notes live in:

- `docs/JOB_DETAIL.md`

## Current State

The repository now contains a usable authenticated tracker with a substantial working product
surface:

- local login/logout and first admin bootstrap command;
- scoped API tokens for capture integrations;
- owner-scoped jobs API and browser capture endpoint;
- Focus home surface for due follow-ups, stale work, upcoming interviews, recent prospects, missing
  next actions, and recently viewed jobs;
- Inbox review surface for captured jobs and pasted email intake that need acceptance before active
  workflow views;
- shared server-rendered layout across the main authenticated pages, with a top-right user menu for
  User Settings, Capture Settings, appearance controls, Help, Sign out, and admin-only Admin/API
  Docs;
- built-in Help page with task-oriented guidance for the main workflow;
- manual job creation and editable job detail pages with compact section workspaces;
- workflow board views with drag/drop and a `Move to column` fallback;
- status-change timeline, notes, follow-up dates, applications, interviews, archive/unarchive;
- job-level artefact upload/download plus artefact detail views and Markdown/text previews where
  available;
- Markdown-first rendering for visible AI output and role/artefact preview surfaces;
- competency evidence storage and visible employer rubric mapping from pasted text;
- visible AI output workflows for fit summaries, next-step guidance, artefact analysis, tailoring,
  and drafting;
- provider-backed AI settings with owner-scoped configuration, encrypted API key storage, and model
  discovery for supported providers;
- stage-aging, stale-card, and follow-up indicators;
- Alembic migrations, Dockerfile, Docker Compose file, and pytest coverage.

Near-term work is driven by the roadmap hubs above. Current active/planned workstreams include:

- artefact AI and competency evidence continuation;
- scheduler/worker runtime planning;
- MCP planning and OAuth/DCR prerequisite design before any runtime MCP exposure.

Use `docs/roadmap/implementation-sequencing.md` for current order and
`docs/roadmap/task-map.md` for execution-ready breakdown.

## Local Docker Runtime

Docker Compose is the preferred way to run Application Tracker locally and is the same runtime
shape used for self-hosted deployment.

Create a local environment file:

```bash
cp .env.example .env
```

For real data, replace `SESSION_SECRET_KEY` with a generated value:

```bash
openssl rand -hex 32
```

Start the app:

```bash
make docker-up
```

Inspect status and logs:

```bash
make docker-ps
make docker-logs
```

Open the app:

```text
http://localhost:8000/setup
```

The container runs `alembic upgrade head` automatically on startup when `AUTO_MIGRATE=1`.

Stop the app:

```bash
make docker-down
```

Run a lightweight container check:

```bash
make docker-check
```

Direct Uvicorn remains available for quick debugging, but it is no longer the preferred runtime
path.

## Local Virtualenv Development

Create a virtual environment and install development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the API directly for debugging:

```bash
make run
```

Open the app:

```text
http://127.0.0.1:8000/login
```

If you prefer to call Uvicorn directly, use the virtualenv binary:

```bash
.venv/bin/uvicorn app.main:app --reload
```

Run tests:

```bash
make test
```

Run all local checks:

```bash
make check
```

### Rebuild A Broken Virtualenv

If imports fail with an `incompatible architecture` error from `pydantic_core`, the virtualenv
contains binary wheels from a different Mac CPU architecture. Recreate it from scratch; running
`python -m venv .venv` over an existing environment does not remove old packages.

```bash
deactivate 2>/dev/null || true
rm -rf .venv
python3 -c "import platform; print(platform.machine())"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --no-cache-dir -e ".[dev]"
make run
```

Apply database migrations:

```bash
make migrate
```

Create the first local admin user from the browser:

```text
http://127.0.0.1:8000/setup
```

The setup page is only available while no users exist. A command-line fallback is also available:

```bash
EMAIL=you@example.com make create-admin
```

## Docker And QNAP Deployment

The detailed Docker and QNAP deployment guide lives in:

- `docs/DOCKER_DEPLOYMENT.md`

For local Docker usage, prefer the Make targets:

```bash
make docker-up
make docker-ps
make docker-logs
make docker-down
```

For QNAP deployment, the Mac/local machine is the deployment controller. The NAS does not need Git:
deployment syncs the current working tree with `rsync`, preserves the NAS `.env`, then runs Docker
Compose remotely over SSH.

```bash
make qnap-deploy
```

The QNAP deployment defaults are:

```env
QNAP_SSH_TARGET=qnap
QNAP_APP_DIR=/share/Container/application_tracker
QNAP_COMPOSE_CMD=sudo docker compose
```

Override them per deploy when needed:

```bash
QNAP_SSH_TARGET=qnap \
QNAP_APP_DIR=/share/Container/application_tracker \
QNAP_COMPOSE_CMD="sudo docker compose" \
make qnap-deploy
```

The QNAP must keep its own `.env` in `QNAP_APP_DIR`; deploys deliberately do not overwrite it or
delete persistent runtime data. On first setup, run `make qnap-deploy` once to sync the application
files, then SSH to the NAS and create/edit `.env` from `.env.example`, then run `make qnap-deploy`
again.

After the first admin user is created, admin setup and maintenance tasks are available from the
username menu for admin users, or directly:

```text
http://localhost:8000/admin
```

The admin page can create and revoke capture API tokens across users, open capture setup, check
health, download a backup ZIP containing the SQLite database and local artefact files, and dry-run
validate a backup archive before any manual restore.

For a NAS or homelab deployment, keep `/app/data` on persistent storage. That directory contains
the SQLite database and uploaded artefacts. The bundled Compose file uses a named volume:

```yaml
volumes:
  - app_data:/app/data
```

On QNAP Container Station or similar systems, an explicit bind mount can make backups easier:

```yaml
volumes:
  - /share/Container/application_tracker/data:/app/data
```

Use a non-default `SESSION_SECRET_KEY` before creating real data:

```bash
openssl rand -hex 32
```

Set it in `.env` next to `docker-compose.yml`:

```env
APP_ENV=development
AUTH_MODE=local
SESSION_SECRET_KEY=replace-with-the-generated-secret
PUBLIC_BASE_URL=http://your-nas-hostname-or-ip:8000
DATABASE_URL=sqlite:////app/data/app.db
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=/app/data/artefacts
AUTO_MIGRATE=1
```

After syncing updates, rebuild and rerun migrations:

```bash
make docker-up
```

The rebuilt container applies any pending Alembic migrations before starting the web server.

Download periodic backups from `/admin`, or back up the persistent `/app/data` mount directly from
the host.

Before replacing live data, validate any downloaded archive from `/admin` or from the CLI:

```bash
.venv/bin/python -m app.cli backup validate --file /path/to/application-tracker-backup.zip
```

Validation checks ZIP shape, manifest metadata, and SQLite readability without mutating the
deployment. Actual restore is still a deliberate manual operation: stop the app, replace `/app/data`
from a validated backup, then start the app again.

For `APP_ENV=production`, `PUBLIC_BASE_URL` must be HTTPS and the default session secret is
rejected. Put the app behind QNAP's reverse proxy, another reverse proxy, or a TLS terminator, then
set `PUBLIC_BASE_URL=https://...`.

## Repository Policy

Do not commit runtime databases, uploaded resumes, cover letters, screenshots, or generated local artefacts. The app should remain safe to publish and sync to GitHub as development continues.

## Security

See `SECURITY.md` before deploying this app beyond local development.

The detailed auth model and implementation sequence lives in `docs/AUTHENTICATION.md`.
