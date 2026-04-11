from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select

from app.api.deps import get_current_api_token, require_capture_jobs_api_token
from app.auth.api_tokens import CAPTURE_JOBS_SCOPE, get_active_api_token
from app.auth.tokens import hash_secret
from app.auth.users import create_local_user
from app.db.models.api_token import ApiToken
from app.db.models.user import User
from tests.test_local_auth_routes import build_client


def login(client, email: str, password: str) -> None:
    response = client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200


def test_create_api_token_returns_secret_once_and_stores_hash(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        login(client, "jobseeker@example.com", "password")

        response = client.post(
            "/auth/api-tokens",
            json={"name": "Browser extension", "scopes": [CAPTURE_JOBS_SCOPE]},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["name"] == "Browser extension"
        assert payload["scopes"] == [CAPTURE_JOBS_SCOPE]
        assert payload["token"].startswith("ats_")

        with session_local() as db:
            stored = db.scalar(select(ApiToken).where(ApiToken.uuid == payload["uuid"]))

            assert stored is not None
            assert stored.token_hash == hash_secret(payload["token"])
            assert stored.token_hash != payload["token"]
    finally:
        from app.main import app

        app.dependency_overrides.clear()


def test_create_api_token_rejects_unsupported_scope(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        login(client, "jobseeker@example.com", "password")

        response = client.post(
            "/auth/api-tokens",
            json={"name": "Bad token", "scopes": ["admin:everything"]},
        )

        assert response.status_code == 400
        assert "Unsupported API token scope" in response.json()["detail"]
    finally:
        from app.main import app

        app.dependency_overrides.clear()


def test_bearer_dependency_accepts_active_capture_jobs_token(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        login(client, "jobseeker@example.com", "password")
        create_response = client.post("/auth/api-tokens", json={"name": "Capture"})
        raw_token = create_response.json()["token"]

        with session_local() as db:
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=raw_token)
            api_token = get_current_api_token(db, credentials)
            user = require_capture_jobs_api_token(api_token)

            assert user.email == "jobseeker@example.com"
            assert api_token.last_used_at is not None
    finally:
        from app.main import app

        app.dependency_overrides.clear()


def test_revoke_api_token_disables_bearer_auth(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        login(client, "jobseeker@example.com", "password")
        create_response = client.post("/auth/api-tokens", json={"name": "Capture"})
        payload = create_response.json()

        revoke_response = client.delete(f"/auth/api-tokens/{payload['uuid']}")

        assert revoke_response.status_code == 204

        with session_local() as db:
            assert get_active_api_token(db, payload["token"]) is None
    finally:
        from app.main import app

        app.dependency_overrides.clear()


def test_revoke_api_token_does_not_cross_user_boundaries(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="owner@example.com", password="password")
            create_local_user(db, email="other@example.com", password="password")
            db.commit()

        login(client, "owner@example.com", "password")
        create_response = client.post("/auth/api-tokens", json={"name": "Capture"})
        token_uuid = create_response.json()["uuid"]
        client.post("/auth/logout")

        login(client, "other@example.com", "password")
        revoke_response = client.delete(f"/auth/api-tokens/{token_uuid}")

        assert revoke_response.status_code == 404
    finally:
        from app.main import app

        app.dependency_overrides.clear()


def test_capture_jobs_scope_dependency_rejects_missing_scope() -> None:
    user = User(id=1, email="jobseeker@example.com", is_active=True)
    api_token = ApiToken(owner=user, owner_user_id=user.id, name="Limited", scopes="profile:read")

    with pytest.raises(HTTPException) as exc_info:
        require_capture_jobs_api_token(api_token)

    assert exc_info.value.status_code == 403
