from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.db.models.user import User


class UserAlreadyExists(ValueError):
    pass


def get_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()
    return db.scalar(select(User).where(User.email == normalized_email))


def create_local_user(
    db: Session,
    *,
    email: str,
    password: str,
    display_name: str | None = None,
    is_admin: bool = False,
) -> User:
    normalized_email = email.strip().lower()
    if get_user_by_email(db, normalized_email) is not None:
        raise UserAlreadyExists(f"User already exists: {normalized_email}")

    user = User(
        email=normalized_email,
        display_name=display_name,
        password_hash=hash_password(password),
        is_admin=is_admin,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user
