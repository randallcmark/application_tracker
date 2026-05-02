from datetime import UTC, datetime
from dataclasses import dataclass
from html import unescape
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
LINKEDIN_DIRECT_ROLE_START = "People with similar roles applied to these jobs"
LINKEDIN_DIRECT_ROLE_END_MARKERS = (
    "Companies with the most job openings in your role",
    "Improve your recommendations",
    "Update your experience",
)
INDEED_SAVED_ALERT_MARKERS = (
    "These job ads match your saved job alert",
    "Easily apply to this job",
)
INDEED_POSTED_RE = re.compile(
    r"^(just posted|today|\d+\+?\s+(?:hour|hours|day|days)\s+ago|active\s+\d+\s+(?:day|days)\s+ago)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class EmailJobCandidate:
    title: str
    company: str | None = None
    location: str | None = None
    source_url: str | None = None
    description: str | None = None
    extraction_method: str = "deterministic_email_multi_candidate"


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
    if "linkedin.com" in parsed.netloc.lower():
        return "/jobs/view" in path or "/comm/jobs/view" in path
    return True


def choose_source_url(urls: list[str]) -> str | None:
    for url in urls:
        if is_meaningful_job_url(url):
            return url
    return None


def choose_candidate_urls(urls: list[str]) -> list[str]:
    return [url for url in urls if is_meaningful_job_url(url)]


def _email_text_for_candidate_extraction(*, body_text: str | None, body_html: str | None) -> str:
    parts = []
    if body_text:
        parts.append(body_text)
    if body_html:
        parts.append(unescape(re.sub(r"<[^>]+>", "\n", body_html)))
    return "\n".join(parts)


def _non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.replace("\r\n", "\n").split("\n") if line.strip()]


def _parse_company_location(line: str) -> tuple[str | None, str | None]:
    if " · " not in line:
        return None, None
    company, location = line.split(" · ", 1)
    return _clean_text(company), _clean_text(location)


def _clean_indeed_company(line: str) -> str | None:
    company = line.split("\t", 1)[0]
    company = re.sub(r"\s+\d+(?:\.\d+)?(?:/5 rating)?$", "", company).strip()
    return _clean_text(company)


def _looks_like_indeed_alert(lines: list[str]) -> bool:
    return any(" new " in line.lower() and " jobs in " in line.lower() for line in lines[:4]) and any(
        marker in line for line in lines[:8] for marker in INDEED_SAVED_ALERT_MARKERS[:1]
    )


def _looks_like_indeed_posted_marker(line: str) -> bool:
    return bool(INDEED_POSTED_RE.match(line.strip()))


def _indeed_candidate_description(
    *,
    title: str,
    company: str,
    location: str,
    details: list[str],
) -> str:
    return "\n".join([title, f"{company} · {location}", *details])


def extract_indeed_saved_alert_candidates(text: str) -> list[EmailJobCandidate]:
    lines = _non_empty_lines(text)
    if not _looks_like_indeed_alert(lines):
        return []

    start = 0
    for index, line in enumerate(lines[:8]):
        if any(marker in line for marker in INDEED_SAVED_ALERT_MARKERS):
            start = index + 1
            break

    candidates: list[EmailJobCandidate] = []
    index = start
    while index + 2 < len(lines):
        title = lines[index]
        company = _clean_indeed_company(lines[index + 1])
        location = _clean_text(lines[index + 2])
        if not company or not location:
            index += 1
            continue
        if _looks_like_indeed_posted_marker(title) or _looks_like_indeed_posted_marker(location):
            index += 1
            continue

        details: list[str] = []
        index += 3
        while index < len(lines):
            line = lines[index]
            if _looks_like_indeed_posted_marker(line):
                index += 1
                break
            details.append(line)
            index += 1

        description = _indeed_candidate_description(
            title=title,
            company=company,
            location=location,
            details=details,
        )
        candidates.append(
            EmailJobCandidate(
                title=title,
                company=company,
                location=location,
                description=description,
                extraction_method="deterministic_indeed_saved_alert",
            )
        )

    return candidates


def extract_linkedin_direct_role_candidates(text: str) -> list[EmailJobCandidate]:
    lines = _non_empty_lines(text)
    try:
        start = lines.index(LINKEDIN_DIRECT_ROLE_START) + 1
    except ValueError:
        return []

    section: list[str] = []
    for line in lines[start:]:
        if line in LINKEDIN_DIRECT_ROLE_END_MARKERS:
            break
        section.append(line)

    candidates: list[EmailJobCandidate] = []
    index = 0
    while index < len(section) - 2:
        company_line = section[index]
        title_line = section[index + 1]
        company_location_line = section[index + 2]
        company, location = _parse_company_location(company_location_line)
        if company and company == company_line and title_line.lower() != "view":
            description = "\n".join(
                part
                for part in (
                    title_line,
                    f"{company} · {location}" if location else company,
                    "Captured from LinkedIn direct-match email section.",
                )
                if part
            )
            candidates.append(
                EmailJobCandidate(
                    title=title_line,
                    company=company,
                    location=location,
                    description=description,
                    extraction_method="deterministic_linkedin_direct_roles",
                )
            )
            index += 4 if index + 3 < len(section) and section[index + 3].lower() == "view" else 3
            continue
        index += 1
    return candidates


def extract_email_job_candidates(
    *,
    body_text: str | None,
    body_html: str | None,
    subject: str | None,
    all_urls: list[str],
) -> list[EmailJobCandidate]:
    extraction_text = _email_text_for_candidate_extraction(body_text=body_text, body_html=body_html)
    description_text = body_text or html_to_text(body_html) or subject
    linkedin_candidates = extract_linkedin_direct_role_candidates(extraction_text)
    if linkedin_candidates:
        return linkedin_candidates
    indeed_candidates = extract_indeed_saved_alert_candidates(extraction_text)
    if indeed_candidates:
        return indeed_candidates

    candidate_urls = choose_candidate_urls(all_urls)
    if candidate_urls:
        title = subject or "Email captured job"
        return [
            EmailJobCandidate(
                title=title,
                source_url=url,
                description=description_text,
            )
            for url in candidate_urls
        ]

    return [
        EmailJobCandidate(
            title=subject or "Email captured job",
            description=description_text,
        )
    ]


def _email_capture_provenance(
    email_intake: EmailIntake,
    *,
    source_provider: str,
    received_at: datetime | None,
    all_urls: list[str],
    source_url: str | None,
    candidate_index: int,
    candidate_count: int,
    extraction_method: str,
) -> dict:
    return {
        "email_capture": {
            "email_intake_uuid": email_intake.uuid,
            "source_provider": source_provider,
            "subject": email_intake.subject,
            "sender": email_intake.sender,
            "received_at": received_at.isoformat() if received_at else None,
            "all_urls": all_urls,
            "selected_source_url": source_url,
            "candidate_index": candidate_index,
            "candidate_count": candidate_count,
            "extraction": {
                "method": extraction_method,
                "confidence": "unknown",
            },
        }
    }


def create_email_inbox_candidates(
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
    all_urls = extract_urls_from_email(body_text=clean_body_text, body_html=clean_body_html)
    candidates = extract_email_job_candidates(
        body_text=clean_body_text,
        body_html=clean_body_html,
        subject=clean_subject,
        all_urls=all_urls,
    )

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

    jobs: list[Job] = []
    created_count = 0
    candidate_count = len(candidates)

    for index, candidate in enumerate(candidates, start=1):
        source_url = candidate.source_url
        description = candidate.description or clean_body_text or html_to_text(clean_body_html) or clean_subject
        existing_job = None
        if source_url:
            existing_job = db.scalar(
                select(Job).where(
                    Job.owner_user_id == owner.id,
                    Job.source_url == source_url,
                )
            )

        provenance = _email_capture_provenance(
            email_intake,
            source_provider=source_provider,
            received_at=received_at,
            all_urls=all_urls,
            source_url=source_url,
            candidate_index=index,
            candidate_count=candidate_count,
            extraction_method=candidate.extraction_method,
        )

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
            jobs.append(existing_job)
            continue

        title = candidate.title
        if candidate_count > 1 and source_url:
            hostname = urlparse(source_url).hostname
            if hostname:
                title = f"{title} ({hostname.removeprefix('www.')})"

        job = Job(
            owner_user_id=owner.id,
            email_intake_id=email_intake.id,
            title=title[:300],
            company=candidate.company,
            status="saved",
            source="email_capture",
            intake_source="email_capture",
            intake_confidence="unknown",
            intake_state="needs_review",
            source_url=source_url,
            apply_url=source_url,
            location=candidate.location,
            description_raw=description,
            description_clean=description,
            structured_data=provenance,
            captured_at=datetime.now(UTC),
        )
        db.add(job)
        db.flush()
        create_job_note(db, job, subject="Email captured", notes="Created from pasted email.")
        jobs.append(job)
        created_count += 1

    return email_intake, jobs, created_count


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
    email_intake, jobs, created_count = create_email_inbox_candidates(
        db,
        owner,
        subject=subject,
        sender=sender,
        received_at=received_at,
        body_text=body_text,
        body_html=body_html,
        source_provider=source_provider,
    )
    return email_intake, jobs[0], created_count > 0
