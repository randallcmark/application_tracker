import json
from urllib import error, request

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.ai_output import AiOutput
from app.db.models.ai_provider_setting import AiProviderSetting
from app.db.models.job import Job
from app.db.models.user import User
from app.db.models.user_profile import UserProfile

KNOWN_PROVIDERS = ("openai", "anthropic", "openai_compatible")
KNOWN_OUTPUT_TYPES = (
    "recommendation",
    "fit_summary",
    "draft",
    "profile_observation",
    "artefact_suggestion",
)


def list_user_ai_provider_settings(db: Session, user: User) -> list[AiProviderSetting]:
    return list(
        db.scalars(
            select(AiProviderSetting)
            .where(AiProviderSetting.owner_user_id == user.id)
            .order_by(AiProviderSetting.provider, AiProviderSetting.created_at)
        )
    )


def upsert_ai_provider_setting(
    db: Session,
    user: User,
    *,
    provider: str,
    label: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
    is_enabled: bool = False,
) -> AiProviderSetting:
    if provider not in KNOWN_PROVIDERS:
        raise ValueError("Unsupported AI provider")
    setting = db.scalar(
        select(AiProviderSetting).where(
            AiProviderSetting.owner_user_id == user.id,
            AiProviderSetting.provider == provider,
        )
    )
    if setting is None:
        setting = AiProviderSetting(owner_user_id=user.id, provider=provider)
        db.add(setting)
    setting.label = (label or "").strip() or None
    setting.base_url = (base_url or "").strip() or None
    setting.model_name = (model_name or "").strip() or None
    setting.is_enabled = is_enabled
    db.flush()
    return setting


def list_user_ai_outputs(db: Session, user: User) -> list[AiOutput]:
    return list(
        db.scalars(
            select(AiOutput)
            .where(AiOutput.owner_user_id == user.id)
            .order_by(AiOutput.updated_at.desc(), AiOutput.created_at.desc())
        )
    )


class AiExecutionError(RuntimeError):
    pass


def get_enabled_ai_provider(db: Session, user: User) -> AiProviderSetting | None:
    settings = list_user_ai_provider_settings(db, user)
    enabled = [setting for setting in settings if setting.is_enabled]
    if not enabled:
        return None
    for provider_name in ("openai_compatible", "openai", "anthropic"):
        for setting in enabled:
            if setting.provider == provider_name:
                return setting
    return enabled[0]


def _profile_context(profile: UserProfile | None) -> str:
    if profile is None:
        return "No user profile is configured."
    fields = [
        ("Target roles", profile.target_roles),
        ("Target locations", profile.target_locations),
        ("Remote preference", profile.remote_preference),
        ("Salary min", profile.salary_min),
        ("Salary max", profile.salary_max),
        ("Salary currency", profile.salary_currency),
        ("Preferred industries", profile.preferred_industries),
        ("Excluded industries", profile.excluded_industries),
        ("Constraints", profile.constraints),
        ("Urgency", profile.urgency),
        ("Positioning notes", profile.positioning_notes),
    ]
    visible = [f"{label}: {value}" for label, value in fields if value not in (None, "")]
    return "\n".join(visible) if visible else "No user profile is configured."


def _job_context(job: Job) -> str:
    fields = [
        ("Title", job.title),
        ("Company", job.company),
        ("Status", job.status),
        ("Location", job.location),
        ("Remote policy", job.remote_policy),
        ("Source", job.source),
        ("Source URL", job.source_url),
        ("Apply URL", job.apply_url),
        ("Description", job.description_raw),
    ]
    return "\n".join(f"{label}: {value}" for label, value in fields if value not in (None, ""))


def _output_request(output_type: str) -> tuple[str, str]:
    if output_type == "fit_summary":
        return (
            "AI fit summary",
            (
                "Write a concise fit summary for this job. Use three short sections titled "
                "'Strengths', 'Gaps', and 'Watch-outs'. Be direct and specific. Do not invent facts. "
                "If profile context is missing, say so plainly."
            ),
        )
    if output_type == "recommendation":
        return (
            "AI next-step recommendation",
            (
                "Recommend the next best action for this job search opportunity. Use three short bullet-style "
                "paragraphs titled 'Next step', 'Why now', and 'What to prepare'. Be direct and actionable."
            ),
        )
    raise AiExecutionError("Unsupported AI output type")


def _call_openai_compatible(setting: AiProviderSetting, prompt: str) -> str:
    if not setting.base_url:
        raise AiExecutionError("Enabled AI provider is missing a base URL")
    if not setting.model_name:
        raise AiExecutionError("Enabled AI provider is missing a model name")

    payload = {
        "model": setting.model_name,
        "messages": [
            {"role": "system", "content": "You are an assistant helping a jobseeker inside a private application tracker."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    endpoint = setting.base_url.rstrip("/") + "/chat/completions"
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise AiExecutionError(f"AI provider returned HTTP {exc.code}: {detail or exc.reason}") from exc
    except error.URLError as exc:
        raise AiExecutionError(f"Could not reach AI provider: {exc.reason}") from exc

    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AiExecutionError("AI provider returned no choices")
    message = choices[0].get("message", {})
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise AiExecutionError("AI provider returned an empty response")
    return content.strip()


def generate_job_ai_output(
    db: Session,
    user: User,
    job: Job,
    *,
    output_type: str,
    profile: UserProfile | None = None,
) -> AiOutput:
    setting = get_enabled_ai_provider(db, user)
    if setting is None:
        raise AiExecutionError("Enable an AI provider in Settings before generating AI output")
    if setting.provider != "openai_compatible":
        raise AiExecutionError(
            "This slice only executes enabled OpenAI-compatible local endpoints. OpenAI and Anthropic remain placeholders for now."
        )

    title, instruction = _output_request(output_type)
    prompt = (
        f"{instruction}\n\n"
        f"User profile:\n{_profile_context(profile)}\n\n"
        f"Job:\n{_job_context(job)}"
    )
    body = _call_openai_compatible(setting, prompt)
    output = AiOutput(
        owner_user_id=user.id,
        job_id=job.id,
        output_type=output_type,
        title=title,
        body=body,
        provider=setting.provider,
        model_name=setting.model_name,
        status="active",
        source_context={
            "job_uuid": job.uuid,
            "provider_label": setting.label,
            "job_status": job.status,
            "job_title": job.title,
        },
    )
    db.add(output)
    db.flush()
    return output
