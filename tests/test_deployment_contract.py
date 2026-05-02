import os
from pathlib import Path


def test_makefile_exposes_docker_and_qnap_targets() -> None:
    makefile = Path("Makefile").read_text()

    for target in (
        "docker-up:",
        "docker-down:",
        "docker-restart:",
        "docker-ps:",
        "docker-logs:",
        "docker-check:",
        "qnap-deploy:",
        "qnap-ps:",
        "qnap-logs:",
    ):
        assert target in makefile

    assert "docker compose up -d --build" in makefile
    assert "docker compose down" in makefile
    assert "./scripts/deploy_qnap.sh" in makefile


def test_qnap_deploy_script_uses_rsync_ssh_and_configurable_defaults() -> None:
    script_path = Path("scripts/deploy_qnap.sh")
    script = script_path.read_text()

    assert os.access(script_path, os.X_OK)
    assert 'QNAP_SSH_TARGET="${QNAP_SSH_TARGET:-qnap}"' in script
    assert 'QNAP_APP_DIR="${QNAP_APP_DIR:-/share/Container/application_tracker}"' in script
    assert 'QNAP_COMPOSE_CMD="${QNAP_COMPOSE_CMD:-sudo docker compose}"' in script
    assert "require_command rsync" in script
    assert "require_command ssh" in script
    assert "rsync -az --delete" in script
    assert 'ssh "$QNAP_SSH_TARGET"' in script
    assert "$QNAP_COMPOSE_CMD up -d --build" in script


def test_qnap_deploy_script_preserves_env_and_runtime_data() -> None:
    script = Path("scripts/deploy_qnap.sh").read_text()

    for protected in (
        "--filter 'P .env'",
        "--filter 'P .env.*'",
        "--filter 'P data/***'",
        "--filter 'P app_data/***'",
        "--filter 'P uploads/***'",
        "--filter 'P artefacts/***'",
    ):
        assert protected in script

    for excluded in (
        "--exclude '.git/'",
        "--exclude '.venv/'",
        "--exclude '.env'",
        "--exclude '.env.*'",
        "--exclude 'data/'",
        "--exclude 'uploads/'",
        "--exclude 'artefacts/'",
        "--exclude '*.db'",
        "--exclude '*.sqlite'",
        "--exclude '*.sqlite3'",
    ):
        assert excluded in script

    assert "test -f $REMOTE_APP_DIR/.env" in script
    assert "remote .env is missing" in script
