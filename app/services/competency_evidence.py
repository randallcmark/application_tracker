from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.ai_output import AiOutput
from app.db.models.artefact import Artefact
from app.db.models.competency_evidence import CompetencyEvidence
from app.db.models.job import Job
from app.db.models.user import User

VALID_STRENGTHS = {"seed", "working", "strong"}


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalise_strength(value: str | None) -> str:
    cleaned = (value or "seed").strip().lower()
    if cleaned not in VALID_STRENGTHS:
        raise ValueError("Competency evidence strength must be seed, working, or strong")
    return cleaned


def _normalise_tags(tags: str | Iterable[str] | None) -> str | None:
    if tags is None:
        return None
    if isinstance(tags, str):
        return _clean_optional(tags)
    cleaned = [item.strip() for item in tags if item.strip()]
    return ", ".join(cleaned) if cleaned else None


def _owner_scoped_source_id(source: Job | Artefact | AiOutput | None, user: User) -> int | None:
    if source is None:
        return None
    if source.owner_user_id != user.id:
        raise ValueError("Competency evidence sources must belong to the same user")
    return source.id


def list_competency_evidence(db: Session, user: User) -> list[CompetencyEvidence]:
    return list(
        db.scalars(
            select(CompetencyEvidence)
            .where(CompetencyEvidence.owner_user_id == user.id)
            .order_by(CompetencyEvidence.updated_at.desc(), CompetencyEvidence.created_at.desc())
        )
    )


def get_user_competency_evidence_by_uuid(
    db: Session,
    user: User,
    evidence_uuid: str,
) -> CompetencyEvidence | None:
    return db.scalar(
        select(CompetencyEvidence).where(
            CompetencyEvidence.owner_user_id == user.id,
            CompetencyEvidence.uuid == evidence_uuid,
        )
    )


def create_competency_evidence(
    db: Session,
    user: User,
    *,
    title: str,
    competency: str | None = None,
    situation: str | None = None,
    task: str | None = None,
    action: str | None = None,
    result: str | None = None,
    evidence_notes: str | None = None,
    strength: str | None = "seed",
    tags: str | Iterable[str] | None = None,
    source_kind: str | None = None,
    source_job: Job | None = None,
    source_artefact: Artefact | None = None,
    source_ai_output: AiOutput | None = None,
) -> CompetencyEvidence:
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValueError("Competency evidence title is required")

    evidence = CompetencyEvidence(
        owner_user_id=user.id,
        title=cleaned_title,
        competency=_clean_optional(competency),
        situation=_clean_optional(situation),
        task=_clean_optional(task),
        action=_clean_optional(action),
        result=_clean_optional(result),
        evidence_notes=_clean_optional(evidence_notes),
        strength=_normalise_strength(strength),
        tags=_normalise_tags(tags),
        source_kind=_clean_optional(source_kind),
        source_job_id=_owner_scoped_source_id(source_job, user),
        source_artefact_id=_owner_scoped_source_id(source_artefact, user),
        source_ai_output_id=_owner_scoped_source_id(source_ai_output, user),
    )
    db.add(evidence)
    db.flush()
    return evidence


def update_competency_evidence(
    evidence: CompetencyEvidence,
    *,
    title: str | None = None,
    competency: str | None = None,
    situation: str | None = None,
    task: str | None = None,
    action: str | None = None,
    result: str | None = None,
    evidence_notes: str | None = None,
    strength: str | None = None,
    tags: str | Iterable[str] | None = None,
    last_used_at: datetime | None = None,
) -> CompetencyEvidence:
    if title is not None:
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValueError("Competency evidence title is required")
        evidence.title = cleaned_title
    if competency is not None:
        evidence.competency = _clean_optional(competency)
    if situation is not None:
        evidence.situation = _clean_optional(situation)
    if task is not None:
        evidence.task = _clean_optional(task)
    if action is not None:
        evidence.action = _clean_optional(action)
    if result is not None:
        evidence.result = _clean_optional(result)
    if evidence_notes is not None:
        evidence.evidence_notes = _clean_optional(evidence_notes)
    if strength is not None:
        evidence.strength = _normalise_strength(strength)
    if tags is not None:
        evidence.tags = _normalise_tags(tags)
    if last_used_at is not None:
        evidence.last_used_at = last_used_at
    return evidence
