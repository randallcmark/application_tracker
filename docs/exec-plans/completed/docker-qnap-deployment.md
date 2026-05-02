# Execution Plan: Docker And QNAP Deployment Workflow

Status: Complete

Owner: Agent

Created: 2026-04-30

Last Updated: 2026-04-30

## Goal

Make Docker Compose the default local runtime path and add a repeatable QNAP deployment workflow driven from the local Mac with SSH, rsync, and remote Docker Compose.

## Non-Goals

- No product behavior changes.
- No UI changes.
- No database schema changes.
- No removal of the direct virtualenv or `make run` workflow.
- No deployment flow that requires Git on the QNAP.

## Context

- `README.md`
- `docs/agent/validation.md`
- `docs/architecture/index.md`
- `docker-compose.yml`
- `Makefile`

## Acceptance Criteria

- `make docker-up`, `docker-down`, `docker-restart`, `docker-ps`, `docker-logs`, and `docker-check` exist.
- `make qnap-deploy` uses a deploy script based on rsync and SSH.
- QNAP sync excludes local development files, `.env`, and runtime data.
- Remote `.env` and persistent data are not deleted by deployment.
- Docker-first local and QNAP deployment docs are current.
- Validation records what was actually run and what requires a real QNAP.

## Plan

1. Inspect the current Docker, Makefile, env, README, and validation contracts.
2. Add the Docker and QNAP Make targets.
3. Add a robust QNAP deployment script with configurable SSH target, app directory, and Compose command.
4. Update env and deployment documentation.
5. Add focused tests for the script and Makefile contracts.
6. Run the relevant validation commands that are possible locally.

## Progress Log

- 2026-04-30: Created plan after reading the task file and local agent docs.
- 2026-04-30: Implemented Docker Compose Make targets, QNAP rsync/SSH deployment script, Docker
  deployment docs, env-example updates, and deployment contract tests. Moved to completed plans
  after local Docker validation passed. Real QNAP deployment still requires manual NAS validation.

## Decisions

- Keep the bundled Compose file unchanged and make the workflow change through Makefile targets and docs.
- Preserve QNAP `.env` and data by excluding them from transfer and adding rsync protect rules while still using `--delete` for synced application files.

## Validation

Commands to run before completion where available:

```sh
bash scripts/validate-harness.sh
make check
make docker-import-smoke
make docker-check
```

Completed validation:

- `bash -n scripts/deploy_qnap.sh`
- `bash scripts/validate-harness.sh`
- `.venv/bin/python -m pytest tests/test_deployment_contract.py tests/test_docker_contract.py`
- `.venv/bin/python -m ruff check tests/test_deployment_contract.py`
- `make docker-import-smoke`
- `make docker-check`
- `make docker-up`
- `make docker-ps`
- `make docker-logs`
- `make docker-down`

QNAP validation requires the real NAS and should not be claimed unless run against it.

## Risks

- The local environment may not have Docker Desktop running; report this explicitly if Docker validation cannot run.
- The QNAP may require a different Compose command; mitigate with `QNAP_COMPOSE_CMD`.
