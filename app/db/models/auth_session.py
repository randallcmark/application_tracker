from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import IdMixin, TimestampMixin


class AuthSession(IdMixin, TimestampMixin, Base):
    __tablename__ = "auth_sessions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    session_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="auth_sessions")
