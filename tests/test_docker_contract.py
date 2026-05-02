from pathlib import Path
import os
import subprocess


def test_dockerfile_runs_entrypoint_before_uvicorn() -> None:
    dockerfile = Path("Dockerfile").read_text()

    assert "COPY docker-entrypoint.sh ./docker-entrypoint.sh" in dockerfile
    assert 'ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]' in dockerfile
    assert 'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]' in dockerfile


def test_docker_entrypoint_auto_migrates_with_opt_out() -> None:
    entrypoint = Path("docker-entrypoint.sh").read_text()

    assert 'AUTO_MIGRATE:-1' in entrypoint
    assert 'alembic upgrade head' in entrypoint
    assert 'exec "$@"' in entrypoint


def test_compose_exposes_auto_migrate_default() -> None:
    compose = Path("docker-compose.yml").read_text()

    assert "AUTO_MIGRATE: ${AUTO_MIGRATE:-1}" in compose


def test_docker_entrypoint_runs_migration_before_app_command(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_path = tmp_path / "entrypoint.log"
    alembic = bin_dir / "alembic"
    app_command = bin_dir / "app-command"
    alembic.write_text(
        "#!/bin/sh\n"
        f"printf 'alembic %s %s\\n' \"$1\" \"$2\" >> {log_path}\n"
    )
    app_command.write_text(f"#!/bin/sh\nprintf 'app command\\n' >> {log_path}\n")
    alembic.chmod(0o755)
    app_command.chmod(0o755)

    result = subprocess.run(
        ["/bin/sh", "docker-entrypoint.sh", "app-command"],
        check=False,
        env={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert log_path.read_text().splitlines() == [
        "alembic upgrade head",
        "app command",
    ]
