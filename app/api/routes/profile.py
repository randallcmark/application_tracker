from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.deps import DbSession, get_current_user
from app.db.models.user import User
from app.db.models.user_profile import UserProfile
from app.services.profiles import get_or_create_user_profile, get_user_profile

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str | None = None
    target_roles: str | None = None
    target_locations: str | None = None
    remote_preference: str | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str | None = None
    preferred_industries: str | None = None
    excluded_industries: str | None = None
    constraints: str | None = None
    urgency: str | None = None
    positioning_notes: str | None = None


class UserProfileUpdateRequest(BaseModel):
    target_roles: str | None = None
    target_locations: str | None = None
    remote_preference: str | None = Field(default=None, max_length=100)
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str | None = Field(default=None, max_length=3)
    preferred_industries: str | None = None
    excluded_industries: str | None = None
    constraints: str | None = None
    urgency: str | None = Field(default=None, max_length=100)
    positioning_notes: str | None = None

    @field_validator(
        "target_roles",
        "target_locations",
        "remote_preference",
        "salary_currency",
        "preferred_industries",
        "excluded_industries",
        "constraints",
        "urgency",
        "positioning_notes",
        mode="before",
    )
    @classmethod
    def strip_blank_strings(cls, value: str | None) -> str | None:
        return _clean_text(value)

    @field_validator("salary_currency")
    @classmethod
    def normalise_salary_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else None


def _empty_profile_response() -> UserProfileResponse:
    return UserProfileResponse()


def profile_response(profile: UserProfile | None) -> UserProfileResponse:
    if profile is None:
        return _empty_profile_response()
    return UserProfileResponse.model_validate(profile)


@router.get("", response_model=UserProfileResponse)
def get_profile(
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserProfileResponse:
    return profile_response(get_user_profile(db, current_user))


@router.put("", response_model=UserProfileResponse)
def update_profile(
    payload: UserProfileUpdateRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserProfileResponse:
    profile = get_or_create_user_profile(db, current_user)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile_response(profile)
