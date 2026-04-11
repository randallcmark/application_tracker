from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import require_csrf_token
from app.api.ownership import require_owner, require_owner_or_admin
from app.auth.csrf import create_csrf_token, verify_csrf_token
from app.core.config import settings
from app.db.models.job import Job
from app.db.models.user import User
from app.main import app


def test_csrf_token_verifies_until_expired() -> None:
    issued_at = datetime(2026, 4, 11, 12, 0, tzinfo=UTC)
    token = create_csrf_token(now=issued_at)

    assert verify_csrf_token(token, now=issued_at + timedelta(minutes=10))
    assert not verify_csrf_token(
        token,
        now=issued_at + timedelta(seconds=settings.csrf_expire_seconds + 1),
    )


def test_csrf_token_rejects_tampering() -> None:
    token = create_csrf_token()
    tampered = f"{token}x"

    assert not verify_csrf_token(tampered)


def test_csrf_endpoint_sets_cookie_and_returns_matching_token() -> None:
    client = TestClient(app)

    response = client.get("/auth/csrf")

    assert response.status_code == 200
    token = response.json()["csrf_token"]
    assert client.cookies[settings.csrf_cookie_name] == token
    assert verify_csrf_token(token)


def test_require_csrf_token_accepts_matching_cookie_and_header() -> None:
    token = create_csrf_token()

    assert require_csrf_token(csrf_cookie=token, csrf_header=token) is None


def test_require_csrf_token_rejects_missing_or_mismatched_token() -> None:
    token = create_csrf_token()

    with pytest.raises(HTTPException) as missing:
        require_csrf_token(csrf_cookie=token, csrf_header=None)

    with pytest.raises(HTTPException) as mismatched:
        require_csrf_token(csrf_cookie=token, csrf_header=create_csrf_token())

    assert missing.value.status_code == 403
    assert mismatched.value.status_code == 403


def test_require_owner_accepts_matching_owner() -> None:
    user = User(id=1, email="owner@example.com")
    job = Job(id=10, owner_user_id=1, title="Designer")

    assert require_owner(job, user) is job


def test_require_owner_rejects_cross_user_access_as_not_found() -> None:
    user = User(id=1, email="owner@example.com")
    job = Job(id=10, owner_user_id=2, title="Designer")

    with pytest.raises(HTTPException) as exc_info:
        require_owner(job, user)

    assert exc_info.value.status_code == 404


def test_require_owner_or_admin_allows_admin_cross_user_access() -> None:
    admin = User(id=1, email="admin@example.com", is_admin=True)
    job = Job(id=10, owner_user_id=2, title="Designer")

    assert require_owner_or_admin(job, admin) is job
