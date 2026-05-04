from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.auth.sessions import get_active_session
from app.auth.tokens import hash_secret
from app.auth.users import create_local_user
from app.core.config import settings
from app.db.models.auth_session import AuthSession
from app.db.session import get_db_session
from app.main import app
from tests.test_database_baseline import run_migrations


def build_client(tmp_path: Path, monkeypatch) -> tuple[TestClient, sessionmaker[Session]]:
    database_url = f"sqlite:///{tmp_path / 'app.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setattr(settings, "database_url", database_url)
    monkeypatch.setattr(settings, "local_storage_path", str(tmp_path / "artefacts"))
    run_migrations(database_url)

    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db() -> Generator[Session, None, None]:
        with test_session_local() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db
    return TestClient(app), test_session_local


def test_login_sets_session_cookie_and_me_returns_user(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(
                db,
                email="jobseeker@example.com",
                password="correct horse battery staple",
                display_name="Job Seeker",
            )
            db.commit()

        login_response = client.post(
            "/auth/login",
            json={
                "email": "jobseeker@example.com",
                "password": "correct horse battery staple",
            },
        )

        assert login_response.status_code == 200
        assert login_response.json()["email"] == "jobseeker@example.com"
        assert settings.session_cookie_name in client.cookies

        me_response = client.get("/auth/me")

        assert me_response.status_code == 200
        assert me_response.json()["display_name"] == "Job Seeker"
    finally:
        app.dependency_overrides.clear()


def test_login_rejects_bad_password(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="right")
            db.commit()

        response = client.post(
            "/auth/login",
            json={"email": "jobseeker@example.com", "password": "wrong"},
        )

        assert response.status_code == 401
        assert settings.session_cookie_name not in client.cookies
    finally:
        app.dependency_overrides.clear()


def test_logout_revokes_session(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        login_response = client.post(
            "/auth/login",
            json={"email": "jobseeker@example.com", "password": "password"},
        )
        assert login_response.status_code == 200
        raw_token = client.cookies[settings.session_cookie_name]

        logout_response = client.post("/auth/logout")

        assert logout_response.status_code == 204
        assert settings.session_cookie_name not in client.cookies

        with session_local() as db:
            stored = db.scalar(
                select(AuthSession).where(AuthSession.session_hash == hash_secret(raw_token))
            )

            assert stored is not None
            assert stored.revoked_at is not None
            assert get_active_session(db, raw_token) is None
    finally:
        app.dependency_overrides.clear()
