from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.tokens import create_api_token, hash_secret
from app.db.models.api_token import ApiToken
from app.db.models.user import User

CAPTURE_JOBS_SCOPE = "capture:jobs"
SUPPORTED_API_TOKEN_SCOPES = {CAPTURE_JOBS_SCOPE}


def normalize_scopes(scopes: list[str] | None) -> list[str]:
    if scopes is None:
        return [CAPTURE_JOBS_SCOPE]

    normalized = sorted({scope.strip() for scope in scopes if scope.strip()})
    if not normalized:
        return [CAPTURE_JOBS_SCOPE]

    unsupported = set(normalized) - SUPPORTED_API_TOKEN_SCOPES
    if unsupported:
        unsupported_list = ", ".join(sorted(unsupported))
        raise ValueError(f"Unsupported API token scope: {unsupported_list}")

    return normalized


def encode_scopes(scopes: list[str]) -> str:
    return " ".join(normalize_scopes(scopes))


def decode_scopes(scopes: str) -> list[str]:
    return sorted({scope for scope in scopes.replace(",", " ").split() if scope})


def token_has_scope(api_token: ApiToken, scope: str) -> bool:
    return scope in decode_scopes(api_token.scopes)


def create_user_api_token(
    db: Session,
    user: User,
    *,
    name: str,
    scopes: list[str] | None = None,
) -> tuple[str, ApiToken]:
    raw_token = create_api_token()
    api_token = ApiToken(
        owner_user_id=user.id,
        name=name.strip(),
        token_hash=hash_secret(raw_token),
        scopes=encode_scopes(normalize_scopes(scopes)),
    )
    db.add(api_token)
    db.flush()
    return raw_token, api_token


def get_active_api_token(db: Session, raw_token: str) -> ApiToken | None:
    api_token = db.scalar(select(ApiToken).where(ApiToken.token_hash == hash_secret(raw_token)))
    if api_token is None:
        return None

    now = datetime.now(UTC)
    expires_at = api_token.expires_at
    if expires_at is not None:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= now:
            return None

    if api_token.revoked_at is not None:
        return None

    if not api_token.owner.is_active:
        return None

    api_token.last_used_at = now
    db.flush()
    return api_token


def revoke_user_api_token(db: Session, user: User, token_uuid: str) -> bool:
    api_token = db.scalar(
        select(ApiToken).where(
            ApiToken.uuid == token_uuid,
            ApiToken.owner_user_id == user.id,
        )
    )
    if api_token is None:
        return False

    if api_token.revoked_at is None:
        api_token.revoked_at = datetime.now(UTC)
        db.flush()

    return True
