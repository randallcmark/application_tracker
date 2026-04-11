from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.deps import DbSession, require_capture_jobs_api_token
from app.db.models.job import Job
from app.db.models.user import User
from app.services.capture import capture_job

router = APIRouter(prefix="/api/capture", tags=["capture"])


class CaptureJobRequest(BaseModel):
    source_url: str | None = Field(default=None, max_length=2048)
    apply_url: str | None = Field(default=None, max_length=2048)
    title: str | None = Field(default=None, max_length=300)
    company: str | None = Field(default=None, max_length=300)
    location: str | None = Field(default=None, max_length=300)
    description: str | None = None
    selected_text: str | None = None
    source_platform: str | None = Field(default=None, max_length=100)
    raw_extraction_metadata: dict | None = None

    @model_validator(mode="after")
    def require_capture_content(self) -> "CaptureJobRequest":
        if not self.title and not self.source_url:
            raise ValueError("Capture requires at least a title or source_url")
        return self


class CaptureJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    title: str
    company: str | None
    status: str
    source_url: str | None
    apply_url: str | None
    created: bool


def _response(job: Job, *, created: bool) -> CaptureJobResponse:
    return CaptureJobResponse(
        uuid=job.uuid,
        title=job.title,
        company=job.company,
        status=job.status,
        source_url=job.source_url,
        apply_url=job.apply_url,
        created=created,
    )


@router.post("/jobs", response_model=CaptureJobResponse, status_code=status.HTTP_201_CREATED)
def capture_job_route(
    payload: CaptureJobRequest,
    response: Response,
    db: DbSession,
    owner: Annotated[User, Depends(require_capture_jobs_api_token)],
) -> CaptureJobResponse:
    title = (payload.title or payload.source_url or "").strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job title is required")

    job, created = capture_job(
        db,
        owner,
        title=title,
        company=payload.company,
        source_url=payload.source_url,
        apply_url=payload.apply_url,
        location=payload.location,
        description=payload.description,
        selected_text=payload.selected_text,
        source_platform=payload.source_platform,
        raw_extraction_metadata=payload.raw_extraction_metadata,
    )
    db.commit()
    if not created:
        response.status_code = status.HTTP_200_OK
    return _response(job, created=created)
