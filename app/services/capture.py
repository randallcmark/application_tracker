from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.job import Job
from app.db.models.user import User


def _capture_intake_source(raw_extraction_metadata: dict | None) -> str:
    extractor = str((raw_extraction_metadata or {}).get("extractor", "")).lower()
    if extractor in {"bookmarklet", "firefox_extension", "chrome_extension"}:
        return "browser_capture"
    return "api_capture"


def capture_job(
    db: Session,
    owner: User,
    *,
    title: str,
    company: str | None = None,
    source_url: str | None = None,
    apply_url: str | None = None,
    location: str | None = None,
    description: str | None = None,
    selected_text: str | None = None,
    source_platform: str | None = None,
    raw_extraction_metadata: dict | None = None,
    raw_html: str | None = None,
    extraction: dict | None = None,
) -> tuple[Job, bool]:
    existing_job = None
    if source_url:
        existing_job = db.scalar(
            select(Job).where(
                Job.owner_user_id == owner.id,
                Job.source_url == source_url,
            )
        )

    structured_data = {
        "capture": {
            "selected_text": selected_text,
            "raw_extraction_metadata": raw_extraction_metadata or {},
            "raw_html": raw_html,
            "extraction": extraction or {},
        }
    }

    if existing_job is not None:
        existing_job.title = title
        existing_job.company = company
        existing_job.apply_url = apply_url
        existing_job.location = location
        existing_job.description_raw = description
        existing_job.description_clean = description
        existing_job.source = source_platform or existing_job.source
        existing_job.intake_source = existing_job.intake_source or _capture_intake_source(
            raw_extraction_metadata
        )
        existing_job.intake_confidence = existing_job.intake_confidence or "medium"
        existing_job.structured_data = structured_data
        existing_job.captured_at = datetime.now(UTC)
        db.flush()
        return existing_job, False

    job = Job(
        owner_user_id=owner.id,
        title=title,
        company=company,
        status="saved",
        source=source_platform or "browser_capture",
        intake_source=_capture_intake_source(raw_extraction_metadata),
        intake_confidence="medium",
        intake_state="needs_review",
        source_url=source_url,
        apply_url=apply_url,
        location=location,
        description_raw=description,
        description_clean=description,
        structured_data=structured_data,
        captured_at=datetime.now(UTC),
    )
    db.add(job)
    db.flush()
    return job, True
