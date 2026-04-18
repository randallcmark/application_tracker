from datetime import UTC, datetime
import re
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.email_intake import EmailIntake
from app.db.models.job import Job
from app.db.models.user import User
from app.services.extraction import html_to_text
from app.services.jobs import create_job_note

URL_RE = re.compile(r"https?://[^\s<>\"]+")
IGNORED_URL_MARKERS = (
    "unsubscribe",
    "email-preference",
    "email_preference",
    "preferences",
    "privacy",
    "terms",
    "tracking-pixel",
    "pixel",
)
IGNORED_URL_EXTENSIONS = (".gif", ".png", ".jpg", ".jpeg", ".webp", ".svg")


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalise_url(raw_url: str) -> str:
    return raw_url.rstrip(").,;]'\"")


def extract_urls_from_email(*, body_text: str | None, body_html: str | None) -> list[str]:
    source = "\n".join(part for part in (body_text, body_html) if part)
    urls: list[str] = []
    seen: set[str] = set()
    for match in URL_RE.finditer(source):
        url = _normalise_url(match.group(0))
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def is_meaningful_job_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    lowered = url.lower()
    path = parsed.path.lower()
    if any(marker in lowered for marker in IGNORED_URL_MARKERS):
        return False
    if any(path.endswith(extension) for extension in IGNORED_URL_EXTENSIONS):
        return False
    return True


def choose_source_url(urls: list[str]) -> str | None:
    for url in urls:
        if is_meaningful_job_url(url):
            return url
    return None


def create_email_inbox_candidate(
    db: Session,
    owner: User,
    *,
    subject: str | None,
    sender: str | None = None,
    received_at: datetime | None = None,
    body_text: str | None = None,
    body_html: str | None = None,
    source_provider: str = "manual_paste",
) -> tuple[EmailIntake, Job, bool]:
    clean_subject = _clean_text(subject)
    clean_body_text = _clean_text(body_text)
    clean_body_html = _clean_text(body_html)
    description = clean_body_text or html_to_text(clean_body_html) or clean_subject
    all_urls = extract_urls_from_email(body_text=clean_body_text, body_html=clean_body_html)
    source_url = choose_source_url(all_urls)

    email_intake = EmailIntake(
        owner_user_id=owner.id,
        subject=clean_subject,
        sender=_clean_text(sender),
        received_at=received_at,
        body_text=clean_body_text,
        body_html=clean_body_html,
        source_provider=source_provider,
    )
    db.add(email_intake)
    db.flush()

    existing_job = None
    if source_url:
        existing_job = db.scalar(
            select(Job).where(
                Job.owner_user_id == owner.id,
                Job.source_url == source_url,
            )
        )

    provenance = {
        "email_capture": {
            "email_intake_uuid": email_intake.uuid,
            "source_provider": source_provider,
            "subject": clean_subject,
            "sender": email_intake.sender,
            "received_at": received_at.isoformat() if received_at else None,
            "all_urls": all_urls,
            "selected_source_url": source_url,
            "extraction": {
                "method": "deterministic_email_foundation",
                "confidence": "unknown",
            },
        }
    }

    if existing_job is not None:
        existing_job.email_intake_id = email_intake.id
        if existing_job.source_url is None:
            existing_job.source_url = source_url
        if existing_job.description_raw is None:
            existing_job.description_raw = description
            existing_job.description_clean = description
        existing_job.structured_data = {**(existing_job.structured_data or {}), **provenance}
        create_job_note(
            db,
            existing_job,
            subject="Email captured",
            notes="Email capture linked to existing job.",
        )
        db.flush()
        return email_intake, existing_job, False

    job = Job(
        owner_user_id=owner.id,
        email_intake_id=email_intake.id,
        title=(clean_subject or "Email captured job")[:300],
        status="saved",
        source="email_capture",
        intake_source="email_capture",
        intake_confidence="unknown",
        intake_state="needs_review",
        source_url=source_url,
        apply_url=source_url,
        description_raw=description,
        description_clean=description,
        structured_data=provenance,
        captured_at=datetime.now(UTC),
    )
    db.add(job)
    db.flush()
    create_job_note(db, job, subject="Email captured", notes="Created from pasted email.")
    return email_intake, job, True
