from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from app.api.deps import DbSession, get_current_user, issue_csrf_token
from app.auth.csrf import clear_csrf_cookie
from app.auth.passwords import verify_password
from app.auth.sessions import create_user_session, revoke_session
from app.auth.users import get_user_by_email
from app.core.config import settings
from app.db.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    uuid: str
    email: EmailStr
    display_name: str | None
    is_admin: bool


class CsrfResponse(BaseModel):
    csrf_token: str


def user_response(user: User) -> UserResponse:
    return UserResponse(
        uuid=user.uuid,
        email=user.email,
        display_name=user.display_name,
        is_admin=user.is_admin,
    )


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.session_expire_days * 24 * 60 * 60,
        path="/",
    )


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: DbSession) -> UserResponse:
    if settings.auth_mode not in ("local", "mixed"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local auth is disabled")

    user = get_user_by_email(db, payload.email)
    if user is None or user.password_hash is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, _ = create_user_session(
        db,
        user,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    set_session_cookie(response, token)
    return user_response(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: DbSession,
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> None:
    if session_token:
        revoke_session(db, session_token)
        db.commit()

    response.delete_cookie(settings.session_cookie_name, path="/")
    clear_csrf_cookie(response)


@router.get("/me", response_model=UserResponse)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return user_response(current_user)


@router.get("/csrf", response_model=CsrfResponse)
def csrf(response: Response) -> CsrfResponse:
    return CsrfResponse(csrf_token=issue_csrf_token(response))
