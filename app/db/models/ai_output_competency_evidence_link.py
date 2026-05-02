from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import IdMixin, TimestampMixin


class AiOutputCompetencyEvidenceLink(IdMixin, TimestampMixin, Base):
    __tablename__ = "ai_output_competency_evidence_links"

    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    ai_output_id: Mapped[int] = mapped_column(ForeignKey("ai_outputs.id"), index=True, nullable=False)
    competency_evidence_id: Mapped[int] = mapped_column(
        ForeignKey("competency_evidence.id"), index=True, nullable=False
    )
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"), index=True, nullable=True)
    artefact_id: Mapped[int | None] = mapped_column(ForeignKey("artefacts.id"), index=True, nullable=True)
    output_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    draft_kind: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    use_intent: Mapped[str] = mapped_column(String(100), default="grounding", index=True, nullable=False)
    user_selected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    evidence_uuid: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    evidence_title: Mapped[str] = mapped_column(String(200), nullable=False)
    evidence_competency: Mapped[str | None] = mapped_column(String(200), nullable=True)
    evidence_strength: Mapped[str | None] = mapped_column(String(32), nullable=True)
    evidence_result_action_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    latest_star_shaping_output_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_outputs.id"), index=True, nullable=True
    )
    evidence_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    owner = relationship("User", back_populates="ai_output_competency_evidence_links")
    ai_output = relationship(
        "AiOutput",
        back_populates="competency_evidence_links",
        foreign_keys=[ai_output_id],
    )
    competency_evidence = relationship("CompetencyEvidence", back_populates="ai_output_links")
    job = relationship("Job", back_populates="ai_output_competency_evidence_links")
    artefact = relationship("Artefact", back_populates="ai_output_competency_evidence_links")
    latest_star_shaping_output = relationship("AiOutput", foreign_keys=[latest_star_shaping_output_id])
