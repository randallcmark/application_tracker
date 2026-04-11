from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

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
