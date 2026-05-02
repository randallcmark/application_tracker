from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import IdMixin, TimestampMixin


class CompetencyEvidence(IdMixin, TimestampMixin, Base):
    __tablename__ = "competency_evidence"

    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    competency: Mapped[str | None] = mapped_column(String(200), nullable=True)
    situation: Mapped[str | None] = mapped_column(Text, nullable=True)
    task: Mapped[str | None] = mapped_column(Text, nullable=True)
    action: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    strength: Mapped[str] = mapped_column(String(32), default="seed", nullable=False)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_kind: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"), index=True, nullable=True)
    source_artefact_id: Mapped[int | None] = mapped_column(
        ForeignKey("artefacts.id"), index=True, nullable=True
    )
    source_ai_output_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_outputs.id"), index=True, nullable=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="competency_evidence")
    source_job = relationship("Job")
    source_artefact = relationship("Artefact")
    source_ai_output = relationship("AiOutput")
    ai_output_links = relationship(
        "AiOutputCompetencyEvidenceLink",
        back_populates="competency_evidence",
        cascade="all, delete-orphan",
    )
