from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.api_tokens import CAPTURE_JOBS_SCOPE, get_active_api_token, token_has_scope
from app.auth.csrf import create_csrf_token, set_csrf_cookie, verify_csrf_token
from app.auth.sessions import get_active_session
from app.core.config import settings
from app.db.models.api_token import ApiToken
from app.db.models.user import User
from app.db.session import get_db_session

DbSession = Annotated[Session, Depends(get_db_session)]
bearer_auth = HTTPBearer(auto_error=False)


def get_current_user(
    db: DbSession,
    session_token: Annotated[str | None, Cookie(alias=settings.session_cookie_name)] = None,
) -> User:
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    auth_session = get_active_session(db, session_token)
    if auth_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    return auth_session.user


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return current_user


def get_current_api_token(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_auth)] = None,
) -> ApiToken:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
        )

    api_token = get_active_api_token(db, credentials.credentials)
    if api_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired bearer token",
        )

    return api_token


def require_capture_jobs_api_token(
    api_token: Annotated[ApiToken, Depends(get_current_api_token)],
) -> User:
    if not token_has_scope(api_token, CAPTURE_JOBS_SCOPE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API token scope required: capture:jobs",
        )

    return api_token.owner


def issue_csrf_token(response: Response) -> str:
    token = create_csrf_token()
    set_csrf_cookie(response, token)
    return token


def require_csrf_token(
    csrf_cookie: Annotated[str | None, Cookie(alias=settings.csrf_cookie_name)] = None,
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> None:
    if not csrf_cookie or not csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token required",
        )

    if csrf_cookie != csrf_header or not verify_csrf_token(csrf_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )
