from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import IdMixin, TimestampMixin


class UserProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_profiles"

    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True, nullable=False
    )
    target_roles: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_locations: Mapped[str | None] = mapped_column(Text, nullable=True)
    remote_preference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    preferred_industries: Mapped[str | None] = mapped_column(Text, nullable=True)
    excluded_industries: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(100), nullable=True)
    positioning_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner = relationship("User", back_populates="profile")
