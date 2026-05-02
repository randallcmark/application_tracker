# Docker And QNAP Deployment

Application Tracker is run through Docker Compose by default for local use and QNAP deployment.
The direct virtualenv workflow remains available for debugging with `make run`.

## Local Docker Quick Start

Create the local environment file:

```bash
cp .env.example .env
```

For anything beyond throwaway local data, set a generated session secret:

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

Open:

```text
http://localhost:8000
```

On a fresh database, create the first admin user at:

```text
http://localhost:8000/setup
```

Stop the app:

```bash
make docker-down
```

Restart cleanly:

```bash
make docker-restart
```

Run a lightweight local Docker validation:

```bash
make docker-check
```

The container entrypoint applies Alembic migrations automatically when `AUTO_MIGRATE=1`.

## Environment

The Docker-first defaults in `.env.example` are:

```env
APP_ENV=development
AUTH_MODE=local
SESSION_SECRET_KEY=replace-with-a-generated-secret
PUBLIC_BASE_URL=http://localhost:8000
DATABASE_URL=sqlite:////app/data/app.db
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=/app/data/artefacts
AUTO_MIGRATE=1
```

For `APP_ENV=production`, use a non-default `SESSION_SECRET_KEY` and set `PUBLIC_BASE_URL` to an
HTTPS URL behind a reverse proxy or TLS terminator.

## Persistent Data

The Compose file stores `/app/data` in the `app_data` Docker volume. That path contains the SQLite
database and uploaded artefacts.

For NAS deployments, a bind mount can make backups easier if you choose to customize Compose:

```yaml
volumes:
  - /share/Container/application_tracker/data:/app/data
```

Do not commit `.env`, databases, uploads, generated artefacts, or NAS-specific private paths.

## QNAP Deployment Model

QNAP deployment is controlled from the Mac/local checkout. The NAS does not need Git and deployment
does not run `git pull` on the NAS.

The default command is:

```bash
make qnap-deploy
```

This runs `scripts/deploy_qnap.sh`, which:

- validates the command is running from the repository root;
- checks local `rsync` and `ssh`;
- checks SSH access to the QNAP;
- creates the remote app directory;
- syncs the current working tree with `rsync`;
- excludes local development files, `.env`, databases, and runtime data;
- preserves the remote `.env` and persistent data while using `--delete` for synced app files;
- runs Docker Compose remotely;
- prints remote `ps` output and recent app logs.

Defaults:

```env
QNAP_SSH_TARGET=qnap
QNAP_APP_DIR=/share/Container/application_tracker
QNAP_COMPOSE_CMD=sudo docker compose
```

Override them per command:

```bash
QNAP_SSH_TARGET=qnap \
QNAP_APP_DIR=/share/Container/application_tracker \
QNAP_COMPOSE_CMD="sudo docker compose" \
make qnap-deploy
```

If your NAS user can run Docker without sudo:

```bash
QNAP_COMPOSE_CMD="docker compose" make qnap-deploy
```

For older systems:

```bash
QNAP_COMPOSE_CMD="sudo docker-compose" make qnap-deploy
```

## QNAP One-Time Setup

Make sure SSH works from the Mac:

```bash
ssh qnap
```

Run the deploy once to create the remote directory and sync application files:

```bash
make qnap-deploy
```

On the first run, the script will stop if the remote `.env` does not exist. Create it on the NAS:

```bash
ssh qnap
cd /share/Container/application_tracker
cp .env.example .env
nano .env
```

At minimum, set:

```env
APP_ENV=production
AUTH_MODE=local
SESSION_SECRET_KEY=replace-with-a-generated-secret
PUBLIC_BASE_URL=https://your-qnap-hostname.example
DATABASE_URL=sqlite:////app/data/app.db
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=/app/data/artefacts
AUTO_MIGRATE=1
```

Then deploy again:

```bash
make qnap-deploy
```

## QNAP Operations

Show remote status:

```bash
make qnap-ps
```

Show recent remote app logs:

```bash
make qnap-logs
```

Equivalent manual commands:

```bash
ssh qnap "cd /share/Container/application_tracker && sudo docker compose ps"
ssh qnap "cd /share/Container/application_tracker && sudo docker compose logs --tail=120 app"
```

## Validation

Local validation:

```bash
make check
make docker-import-smoke
make docker-check
```

QNAP validation requires the actual NAS:

```bash
ssh qnap "echo ok"
make qnap-deploy
ssh qnap "cd /share/Container/application_tracker && sudo docker compose ps"
```

Do not treat QNAP deployment as tested unless these commands were run against the QNAP.
