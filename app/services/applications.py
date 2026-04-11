from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.application import Application
from app.db.models.communication import Communication
from app.db.models.job import Job


def get_job_application(db: Session, job: Job) -> Application | None:
    return db.scalar(
        select(Application).where(
            Application.job_id == job.id,
            Application.owner_user_id == job.owner_user_id,
        )
    )


def mark_job_applied(
    db: Session,
    job: Job,
    *,
    channel: str | None = None,
    notes: str | None = None,
    applied_at: datetime | None = None,
) -> tuple[Application, bool, Communication]:
    timestamp = applied_at or datetime.now(UTC)
    application = get_job_application(db, job)
    created = application is None

    if application is None:
        application = Application(
            job_id=job.id,
            owner_user_id=job.owner_user_id,
            status="applied",
            channel=channel,
            notes=notes,
            applied_at=timestamp,
        )
        db.add(application)
        db.flush()
    else:
        application.status = "applied"
        application.channel = channel or application.channel
        application.notes = notes or application.notes
        application.applied_at = application.applied_at or timestamp
        db.flush()

    event = Communication(
        job_id=job.id,
        application_id=application.id,
        owner_user_id=job.owner_user_id,
        event_type="application",
        direction="internal",
        occurred_at=timestamp,
        subject="Marked applied",
        notes=notes or "Application marked as applied.",
    )
    db.add(event)
    db.flush()
    return application, created, event
