from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth.csrf import create_csrf_token, set_csrf_cookie, verify_csrf_token
from app.auth.sessions import get_active_session
from app.core.config import settings
from app.db.models.user import User
from app.db.session import get_db_session

DbSession = Annotated[Session, Depends(get_db_session)]


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
