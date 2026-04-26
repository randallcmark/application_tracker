from pathlib import Path


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
