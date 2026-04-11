from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime

from fastapi import Response

from app.core.config import settings


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _sign(payload: str) -> str:
    signature = hmac.new(
        settings.session_secret_key.encode("utf-8"),
        payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64encode(signature)


def create_csrf_token(*, now: datetime | None = None) -> str:
    issued_at = int((now or datetime.now(UTC)).timestamp())
    nonce = _b64encode(secrets.token_bytes(32))
    payload = f"{nonce}.{issued_at}"
    return f"{payload}.{_sign(payload)}"


def verify_csrf_token(token: str, *, now: datetime | None = None) -> bool:
    parts = token.split(".")
    if len(parts) != 3:
        return False

    nonce, issued_at_raw, signature = parts
    if not nonce or not issued_at_raw or not signature:
        return False

    try:
        issued_at = int(issued_at_raw)
    except ValueError:
        return False

    current_timestamp = int((now or datetime.now(UTC)).timestamp())
    if issued_at > current_timestamp:
        return False

    if current_timestamp - issued_at > settings.csrf_expire_seconds:
        return False

    expected = _sign(f"{nonce}.{issued_at_raw}")
    return hmac.compare_digest(signature, expected)


def set_csrf_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.csrf_expire_seconds,
        path="/",
    )


def clear_csrf_cookie(response: Response) -> None:
    response.delete_cookie(settings.csrf_cookie_name, path="/")
