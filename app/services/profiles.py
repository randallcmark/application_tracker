from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.user_profile import UserProfile


def get_user_profile(db: Session, user: User) -> UserProfile | None:
    return db.scalar(select(UserProfile).where(UserProfile.owner_user_id == user.id))


def get_or_create_user_profile(db: Session, user: User) -> UserProfile:
    profile = get_user_profile(db, user)
    if profile is not None:
        return profile

    profile = UserProfile(owner_user_id=user.id)
    db.add(profile)
    db.flush()
    return profile
