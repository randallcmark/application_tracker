from hashlib import sha256
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.artefact import Artefact
from app.db.models.job import Job
from app.db.models.user import User
from app.storage.base import StorageProvider
from app.storage.paths import sanitize_filename
from app.storage.provider import get_storage_provider


def get_user_job_artefact_by_uuid(
    db: Session,
    user: User,
    job: Job,
    artefact_uuid: str,
) -> Artefact | None:
    return db.scalar(
        select(Artefact).where(
            Artefact.uuid == artefact_uuid,
            Artefact.owner_user_id == user.id,
            Artefact.job_id == job.id,
        )
    )


def store_job_artefact(
    db: Session,
    job: Job,
    *,
    kind: str,
    filename: str,
    content: bytes,
    content_type: str | None = None,
    storage: StorageProvider | None = None,
) -> Artefact:
    safe_filename = sanitize_filename(filename)
    artefact_kind = kind.strip() or "other"
    storage_key = f"jobs/{job.uuid}/artefacts/{uuid4().hex}-{safe_filename}"
    provider = storage or get_storage_provider()
    stored = provider.save(storage_key, content)

    artefact = Artefact(
        owner_user_id=job.owner_user_id,
        job_id=job.id,
        kind=artefact_kind,
        filename=safe_filename,
        content_type=content_type,
        storage_key=stored.key,
        size_bytes=stored.size_bytes,
        checksum_sha256=sha256(content).hexdigest(),
    )
    db.add(artefact)
    db.flush()
    return artefact
