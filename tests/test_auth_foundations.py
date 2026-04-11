from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.auth.passwords import hash_password, verify_password
from app.auth.tokens import create_api_token, create_session_token, hash_secret, verify_secret
from app.core.config import DEVELOPMENT_SESSION_SECRET, Settings
from app.db.models.auth_session import AuthSession
from app.db.models.user import User
from tests.test_database_baseline import run_migrations


def test_production_rejects_auth_mode_none() -> None:
    with pytest.raises(ValidationError, match="AUTH_MODE=none"):
        Settings(app_env="production", auth_mode="none")


def test_production_requires_changed_session_secret() -> None:
    with pytest.raises(ValidationError, match="SESSION_SECRET_KEY"):
        Settings(
            app_env="production",
            auth_mode="local",
            session_secret_key=DEVELOPMENT_SESSION_SECRET,
            public_base_url="https://tracker.example.com",
        )


def test_production_requires_https_public_base_url() -> None:
    with pytest.raises(ValidationError, match="PUBLIC_BASE_URL"):
        Settings(
            app_env="production",
            auth_mode="local",
            session_secret_key="not-the-dev-secret",
            public_base_url="http://tracker.example.com",
        )


def test_proxy_auth_requires_explicit_trust_in_production() -> None:
    with pytest.raises(ValidationError, match="TRUSTED_PROXY_AUTH"):
        Settings(
            app_env="production",
            auth_mode="proxy",
            session_secret_key="not-the-dev-secret",
            public_base_url="https://tracker.example.com",
            trusted_proxy_auth=False,
        )


def test_development_allows_default_local_settings() -> None:
    settings = Settings()

    assert settings.auth_mode == "local"
    assert settings.app_env == "development"


def test_password_hashing_verifies_correct_password() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_secret_hashing_is_stable_and_constant_time_verifiable() -> None:
    token = create_api_token()
    token_hash = hash_secret(token)

    assert token.startswith("ats_")
    assert token_hash != token
    assert verify_secret(token, token_hash)
    assert not verify_secret(f"{token}x", token_hash)


def test_session_token_prefix() -> None:
    assert create_session_token().startswith("ats_session_")


def test_auth_session_model_persists_hashed_session(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite:///{tmp_path / 'app.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    run_migrations(database_url)

    engine = create_engine(database_url)
    raw_session_token = create_session_token()
    session_hash = hash_secret(raw_session_token)

    with Session(engine) as session:
        user = User(email="jobseeker@example.com")
        session.add(user)
        session.flush()

        auth_session = AuthSession(
            user_id=user.id,
            session_hash=session_hash,
            user_agent="pytest",
            ip_address="127.0.0.1",
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        session.add(auth_session)
        session.commit()

    with Session(engine) as session:
        stored = session.scalar(select(AuthSession).where(AuthSession.session_hash == session_hash))

        assert stored is not None
        assert stored.user.email == "jobseeker@example.com"
        assert verify_secret(raw_session_token, stored.session_hash)


def test_require_admin_accepts_admin_user() -> None:
    user = User(email="admin@example.com", is_admin=True)

    assert require_admin(user) is user


def test_require_admin_rejects_non_admin_user() -> None:
    user = User(email="user@example.com", is_admin=False)

    with pytest.raises(HTTPException) as exc_info:
        require_admin(user)

    assert exc_info.value.status_code == 403
