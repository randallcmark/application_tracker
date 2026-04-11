from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select

from app.api.deps import DbSession, get_current_user
from app.api.ownership import require_owner
from app.db.models.application import Application
from app.db.models.artefact import Artefact
from app.db.models.communication import Communication
from app.db.models.interview_event import InterviewEvent
from app.db.models.job import Job
from app.db.models.user import User
from app.services.applications import mark_job_applied
from app.services.artefacts import store_job_artefact
from app.services.interviews import schedule_interview
from app.services.jobs import (
    BOARD_STATUSES,
    JOB_STATUSES,
    BoardOrderValidationError,
    create_job_note,
    get_user_job_by_uuid,
    list_user_jobs,
    record_job_status_change,
    update_job_board_state,
    update_user_board_order,
)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    title: str
    company: str | None
    status: str
    board_position: int
    source: str | None
    source_url: str | None
    apply_url: str | None
    location: str | None
    remote_policy: str | None
    salary_min: Decimal | None
    salary_max: Decimal | None
    salary_currency: str | None
    description_raw: str | None
    captured_at: datetime | None
    archived_at: datetime | None


class JobBoardUpdateRequest(BaseModel):
    status: str | None = None
    board_position: int | None = Field(default=None, ge=0)


class JobBoardOrderRequest(BaseModel):
    columns: dict[str, list[str]]


class CreateJobRequest(BaseModel):
    title: str = Field(max_length=300)
    company: str | None = Field(default=None, max_length=300)
    status: str = "saved"
    source_url: str | None = Field(default=None, max_length=2048)
    apply_url: str | None = Field(default=None, max_length=2048)
    location: str | None = Field(default=None, max_length=300)
    remote_policy: str | None = Field(default=None, max_length=50)
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str | None = Field(default=None, max_length=3)
    description_raw: str | None = None
    initial_note: str | None = None


class JobTimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    event_type: str
    direction: str | None
    occurred_at: datetime | None
    follow_up_at: datetime | None
    subject: str | None
    notes: str | None


class JobTimelineCreateRequest(BaseModel):
    subject: str = Field(default="Note", max_length=300)
    notes: str
    occurred_at: datetime | None = None
    follow_up_at: datetime | None = None


class MarkAppliedRequest(BaseModel):
    channel: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    applied_at: datetime | None = None


class ArchiveJobRequest(BaseModel):
    notes: str | None = None


class UnarchiveJobRequest(BaseModel):
    target_status: str = "saved"
    notes: str | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    job_id: int
    status: str
    channel: str | None
    applied_at: datetime | None
    notes: str | None
    created: bool


class ScheduleInterviewRequest(BaseModel):
    stage: str = Field(max_length=100)
    scheduled_at: datetime | None = None
    location: str | None = Field(default=None, max_length=300)
    participants: str | None = Field(default=None, max_length=500)
    notes: str | None = None


class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    stage: str
    scheduled_at: datetime | None
    location: str | None
    participants: str | None
    notes: str | None
    outcome: str | None


class JobArtefactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    job_id: int
    kind: str
    filename: str
    content_type: str | None
    storage_key: str
    size_bytes: int | None
    checksum_sha256: str | None


def _validate_status(job_status: str | None) -> None:
    if job_status is not None and job_status not in JOB_STATUSES:
        allowed = ", ".join(JOB_STATUSES)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported job status. Allowed values: {allowed}",
        )


def _validate_active_status(target_status: str, *, detail: str) -> None:
    _validate_status(target_status)
    if target_status not in BOARD_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


@router.get("", response_model=list[JobResponse])
def list_jobs(
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    include_archived: bool = False,
    job_status: Annotated[str | None, Query(alias="status")] = None,
) -> list[Job]:
    _validate_status(job_status)
    return list_user_jobs(
        db,
        current_user,
        include_archived=include_archived,
        status=job_status,
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: CreateJobRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Job:
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job title is required")

    job_status = payload.status.strip() or "saved"
    _validate_active_status(job_status, detail="New job status must be an active board status")
    next_position = (
        db.scalar(
            select(func.max(Job.board_position)).where(
                Job.owner_user_id == current_user.id,
                Job.status == job_status,
            )
        )
        or -1
    ) + 1

    job = Job(
        owner_user_id=current_user.id,
        title=title,
        company=_clean_optional(payload.company),
        status=job_status,
        board_position=next_position,
        source="manual",
        source_url=_clean_optional(payload.source_url),
        apply_url=_clean_optional(payload.apply_url),
        location=_clean_optional(payload.location),
        remote_policy=_clean_optional(payload.remote_policy),
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        salary_currency=_clean_optional(payload.salary_currency),
        description_raw=_clean_optional(payload.description_raw),
        description_clean=_clean_optional(payload.description_raw),
    )
    db.add(job)
    db.flush()
    if payload.initial_note and payload.initial_note.strip():
        create_job_note(db, job, subject="Created manually", notes=payload.initial_note.strip())
    db.commit()
    return job


@router.patch("/board", response_model=list[JobResponse])
def update_board_order(
    payload: JobBoardOrderRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Job]:
    try:
        jobs = update_user_board_order(db, current_user, payload.columns)
    except BoardOrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    return jobs


@router.get("/{job_uuid}", response_model=JobResponse)
def get_job(
    job_uuid: str,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Job:
    return require_owner(get_user_job_by_uuid(db, current_user, job_uuid), current_user)


@router.get("/{job_uuid}/timeline", response_model=list[JobTimelineEventResponse])
def get_job_timeline(
    job_uuid: str,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Communication]:
    job = require_owner(get_user_job_by_uuid(db, current_user, job_uuid), current_user)
    return sorted(
        job.communications,
        key=lambda event: event.occurred_at or event.created_at,
    )


@router.post(
    "/{job_uuid}/timeline",
    response_model=JobTimelineEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job_timeline_event(
    job_uuid: str,
    payload: JobTimelineCreateRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Communication:
    subject = payload.subject.strip() or "Note"
    notes = payload.notes.strip()
    if not notes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Note text is required")

    job = require_owner(get_user_job_by_uuid(db, current_user, job_uuid), current_user)
    event = create_job_note(
        db,
        job,
        subject=subject,
        notes=notes,
        occurred_at=payload.occurred_at,
        follow_up_at=payload.follow_up_at,
    )
    db.commit()
    return event


@router.post(
    "/{job_uuid}/artefacts",
    response_model=JobArtefactResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_job_artefact(
    job_uuid: str,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    kind: Annotated[str, Form()] = "other",
    file: UploadFile = File(...),
) -> Artefact:
    filename = file.filename or ""
    if not filename.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    job = require_owner(get_user_job_by_uuid(db, current_user, job_uuid), current_user)
    artefact = store_job_artefact(
        db,
        job,
        kind=kind,
        filename=filename,
        content=content,
        content_type=file.content_type,
    )
    create_job_note(db, job, subject="Artefact uploaded", notes=f"Uploaded {artefact.filename}.")
    db.commit()
    return artefact


@router.patch("/{job_uuid}/board", response_model=JobResponse)
def update_job_board(
    job_uuid: str,
    payload: JobBoardUpdateRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Job:
    if payload.status is None and payload.board_position is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide status or board_position",
        )

    _validate_status(payload.status)
    job = require_owner(get_user_job_by_uuid(db, current_user, job_uuid), current_user)
    old_status = job.status
    update_job_board_state(
        job,
        status=payload.status,
        board_position=payload.board_position,
    )
    if payload.status is not None:
        record_job_status_change(db, job, old_status=old_status, new_status=job.status)
    db.commit()
    return job


@router.post(
    "/{job_uuid}/mark-applied",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_job_applied_route(
    job_uuid: str,
    payload: MarkAppliedRequest,
    response: Response,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Application:
    job = require_owner(get_user_job_by_uuid(db, current_user, job_uuid), current_user)
    old_status = job.status
    application, created, _ = mark_job_applied(
        db,
        job,
        channel=payload.channel.strip() if payload.channel else None,
        notes=payload.notes.strip() if payload.notes else None,
        applied_at=payload.applied_at,
    )
    update_job_board_state(job, status="applied")
    record_job_status_change(db, job, old_status=old_status, new_status=job.status)
    db.commit()
    if not created:
        response.status_code = status.HTTP_200_OK
    application.created = created
    return application


@router.post(
    "/{job_uuid}/interviews",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def schedule_interview_route(
    job_uuid: str,
    payload: ScheduleInterviewRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> InterviewEvent:
    interview_stage = payload.stage.strip()
    if not interview_stage:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Interview stage is required")

    job = require_owner(get_user_job_by_uuid(db, current_user, job_uuid), current_user)
    old_status = job.status
    interview, _ = schedule_interview(
        db,
        job,
        stage=interview_stage,
        scheduled_at=payload.scheduled_at,
        location=payload.location,
        participants=payload.participants,
        notes=payload.notes,
    )
    if job.status in {"saved", "interested", "preparing", "applied"}:
        update_job_board_state(job, status="interviewing")
        record_job_status_change(db, job, old_status=old_status, new_status=job.status)
    db.commit()
    return interview


@router.post("/{job_uuid}/archive", response_model=JobResponse)
def archive_job_route(
    job_uuid: str,
    payload: ArchiveJobRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Job:
    job = require_owner(get_user_job_by_uuid(db, current_user, job_uuid), current_user)
    old_status = job.status
    update_job_board_state(job, status="archived")
    record_job_status_change(db, job, old_status=old_status, new_status=job.status)
    if payload.notes and payload.notes.strip():
        create_job_note(
            db,
            job,
            subject="Archived",
            notes=payload.notes.strip(),
        )
    db.commit()
    return job


@router.post("/{job_uuid}/unarchive", response_model=JobResponse)
def unarchive_job_route(
    job_uuid: str,
    payload: UnarchiveJobRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Job:
    target_status = payload.target_status.strip() or "saved"
    _validate_active_status(target_status, detail="Unarchive target status cannot be archived")

    job = require_owner(get_user_job_by_uuid(db, current_user, job_uuid), current_user)
    old_status = job.status
    update_job_board_state(job, status=target_status)
    record_job_status_change(db, job, old_status=old_status, new_status=job.status)
    if payload.notes and payload.notes.strip():
        create_job_note(
            db,
            job,
            subject="Unarchived",
            notes=payload.notes.strip(),
        )
    db.commit()
    return job
