#!/usr/bin/env bash
set -euo pipefail

QNAP_SSH_TARGET="${QNAP_SSH_TARGET:-qnap}"
QNAP_APP_DIR="${QNAP_APP_DIR:-/share/Container/application_tracker}"
QNAP_COMPOSE_CMD="${QNAP_COMPOSE_CMD:-sudo docker compose}"

log() {
  printf '[qnap-deploy] %s\n' "$*"
}

fail() {
  printf '[qnap-deploy] error: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

quote_for_remote() {
  printf "%q" "$1"
}

validate_repo_root() {
  [[ -f docker-compose.yml ]] || fail "docker-compose.yml not found; run from the repository root"
  [[ -f Dockerfile ]] || fail "Dockerfile not found; run from the repository root"
  [[ -f pyproject.toml ]] || fail "pyproject.toml not found; run from the repository root"
}

run_remote() {
  ssh "$QNAP_SSH_TARGET" "$@"
}

REMOTE_APP_DIR="$(quote_for_remote "$QNAP_APP_DIR")"

validate_repo_root
require_command rsync
require_command ssh

log "Using SSH target: $QNAP_SSH_TARGET"
log "Using remote app directory: $QNAP_APP_DIR"
log "Using remote Compose command: $QNAP_COMPOSE_CMD"

log "Checking SSH access"
run_remote "echo ok" >/dev/null || fail "cannot connect to $QNAP_SSH_TARGET over SSH"

log "Creating remote app directory if needed"
run_remote "mkdir -p $REMOTE_APP_DIR"

log "Syncing repository working tree to QNAP"
rsync -az --delete \
  --filter 'P .env' \
  --filter 'P .env.*' \
  --filter 'P data/***' \
  --filter 'P app_data/***' \
  --filter 'P uploads/***' \
  --filter 'P artefacts/***' \
  --include '.env.example' \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude '.env' \
  --exclude '.env.*' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude '.ruff_cache/' \
  --exclude '.mypy_cache/' \
  --exclude '.coverage' \
  --exclude '.DS_Store' \
  --exclude 'dist/' \
  --exclude 'build/' \
  --exclude 'htmlcov/' \
  --exclude 'data/' \
  --exclude 'app_data/' \
  --exclude 'uploads/' \
  --exclude 'artefacts/' \
  --exclude '*.db' \
  --exclude '*.sqlite' \
  --exclude '*.sqlite3' \
  ./ "$QNAP_SSH_TARGET:$QNAP_APP_DIR/"

log "Checking remote .env"
if ! run_remote "test -f $REMOTE_APP_DIR/.env"; then
  fail "remote .env is missing. SSH to $QNAP_SSH_TARGET, then run: cd $QNAP_APP_DIR && cp .env.example .env && edit .env"
fi

log "Building and starting remote Compose stack"
run_remote "cd $REMOTE_APP_DIR && $QNAP_COMPOSE_CMD up -d --build"

log "Remote container status"
run_remote "cd $REMOTE_APP_DIR && $QNAP_COMPOSE_CMD ps"

log "Recent app logs"
run_remote "cd $REMOTE_APP_DIR && $QNAP_COMPOSE_CMD logs --tail=80 app"

log "Deployment complete"
