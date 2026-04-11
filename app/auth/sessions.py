from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.tokens import create_session_token, hash_secret
from app.core.config import settings
from app.db.models.auth_session import AuthSession
from app.db.models.user import User


def create_user_session(
    db: Session,
    user: User,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, AuthSession]:
    raw_token = create_session_token()
    auth_session = AuthSession(
        user_id=user.id,
        session_hash=hash_secret(raw_token),
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=datetime.now(UTC) + timedelta(days=settings.session_expire_days),
    )
    db.add(auth_session)
    db.flush()
    return raw_token, auth_session


def get_active_session(db: Session, raw_token: str) -> AuthSession | None:
    auth_session = db.scalar(
        select(AuthSession).where(AuthSession.session_hash == hash_secret(raw_token))
    )
    if auth_session is None:
        return None

    now = datetime.now(UTC)
    expires_at = auth_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if auth_session.revoked_at is not None or expires_at <= now:
        return None

    if not auth_session.user.is_active:
        return None

    return auth_session


def revoke_session(db: Session, raw_token: str) -> None:
    auth_session = db.scalar(
        select(AuthSession).where(AuthSession.session_hash == hash_secret(raw_token))
    )
    if auth_session is not None and auth_session.revoked_at is None:
        auth_session.revoked_at = datetime.now(UTC)
        db.flush()
