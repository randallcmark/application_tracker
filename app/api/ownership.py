from typing import Protocol, TypeVar

from fastapi import HTTPException, status

from app.db.models.user import User


class OwnedResource(Protocol):
    owner_user_id: int


OwnedT = TypeVar("OwnedT", bound=OwnedResource)


def require_owner(resource: OwnedT | None, current_user: User) -> OwnedT:
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    if resource.owner_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    return resource


def require_owner_or_admin(resource: OwnedT | None, current_user: User) -> OwnedT:
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    if current_user.is_admin or resource.owner_user_id == current_user.id:
        return resource

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
