import json
import ssl
from urllib import error, request

import certifi
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.ai_output import AiOutput
from app.db.models.ai_provider_setting import AiProviderSetting
from app.db.models.job import Job
from app.db.models.user import User
from app.db.models.user_profile import UserProfile
from app.security.sealed_secrets import SecretEnvelopeError, key_hint, open_secret, seal_secret

KNOWN_PROVIDERS = ("openai", "gemini", "anthropic", "openai_compatible")
KNOWN_OUTPUT_TYPES = (
    "recommendation",
    "fit_summary",
    "draft",
    "profile_observation",
    "artefact_suggestion",
)

PROVIDER_LABELS = {
    "openai": "OpenAI",
    "gemini": "Google Gemini",
    "anthropic": "Anthropic",
    "openai_compatible": "OpenAI-compatible provider",
}


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
    api_key: str | None = None,
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
    api_key_value = (api_key or "").strip()
    if api_key_value:
        setting.api_key_encrypted = seal_secret(api_key_value)
        setting.api_key_hint = key_hint(api_key_value)
    setting.is_enabled = is_enabled
    if is_enabled:
        for other_setting in list_user_ai_provider_settings(db, user):
            if other_setting.provider != provider and other_setting.is_enabled:
                other_setting.is_enabled = False
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


def _provider_label(setting: AiProviderSetting) -> str:
    return PROVIDER_LABELS.get(setting.provider, "AI provider")


def _parse_error_detail_payload(detail: str) -> tuple[dict[str, object], str]:
    text = detail.strip()
    if not text:
        return {}, ""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}, text
    if isinstance(payload, dict):
        error_payload = payload.get("error")
        if isinstance(error_payload, dict):
            message = error_payload.get("message")
            return error_payload, message.strip() if isinstance(message, str) else text
        message = payload.get("message")
        if isinstance(message, str):
            return payload, message.strip()
    return {}, text


def _http_error_message(setting: AiProviderSetting, exc: error.HTTPError) -> str:
    detail = exc.read().decode("utf-8", errors="ignore")
    payload, message = _parse_error_detail_payload(detail)
    provider = _provider_label(setting)
    normalized = message.lower()
    error_code = str(payload.get("code", "")).lower()
    error_type = str(payload.get("type", "")).lower()

    if exc.code == 404:
        if setting.provider == "gemini" and "model" in normalized and "not found" in normalized:
            return (
                f"{provider} could not find that model. Check the model name in Settings "
                "for the selected API version."
            )
        return (
            f"{provider} endpoint was not found. Check the Base URL in Settings and remove any extra path "
            "segments unless you intend to override the default endpoint."
        )
    if exc.code in (401, 403):
        return f"{provider} rejected the API key. Check the saved key and provider permissions in Settings."
    if exc.code == 429 and (
        "insufficient_quota" in error_code
        or "insufficient_quota" in error_type
        or "quota" in normalized
        or "billing" in normalized
    ):
        return (
            f"{provider} accepted the key, but the project has no available API quota. "
            "Check provider billing and quota for this key."
        )
    if exc.code == 429:
        return f"{provider} rate-limited the request. Wait a moment and try again."
    if exc.code == 400 and ("model" in normalized and ("not found" in normalized or "unsupported" in normalized)):
        return f"{provider} could not use that model. Check the model name in Settings."
    if exc.code == 400 and ("api key" in normalized or "credential" in normalized or "auth" in normalized):
        return f"{provider} rejected the credentials. Check the saved API key in Settings."

    fallback = message or exc.reason or "Unknown error"
    return f"{provider} returned an error ({exc.code}). {fallback}"


def _url_error_message(setting: AiProviderSetting, exc: error.URLError) -> str:
    provider = _provider_label(setting)
    reason = str(exc.reason)
    if "CERTIFICATE_VERIFY_FAILED" in reason:
        return (
            f"Could not reach {provider} because TLS certificate validation failed. "
            "Check the local trust store or custom HTTPS endpoint."
        )
    return f"Could not reach {provider}. Check the network connection and Base URL in Settings."


def get_enabled_ai_provider(db: Session, user: User) -> AiProviderSetting | None:
    settings = list_user_ai_provider_settings(db, user)
    enabled = [setting for setting in settings if setting.is_enabled]
    if not enabled:
        return None
    for provider_name in ("openai_compatible", "gemini", "openai", "anthropic"):
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


def _output_request(output_type: str, *, surface: str = "default") -> tuple[str, str]:
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
        if surface == "focus":
            return (
                "AI next-step recommendation",
                (
                    "This recommendation is for the Focus surface, where the user needs one immediate next move. "
                    "Recommend exactly one concrete next action for this role right now. Keep it short and specific. "
                    "Use three short sections titled 'Next step', 'Why this now', and 'What to prepare'. "
                    "Explain why this role deserves attention in Focus based on the available context. "
                    "Do not suggest status changes or multiple parallel tasks. Do not invent facts."
                ),
            )
        return (
            "AI next-step recommendation",
            (
                "Recommend the next best action for this job search opportunity. Use three short bullet-style "
                "paragraphs titled 'Next step', 'Why now', and 'What to prepare'. Be direct and actionable."
            ),
        )
    raise AiExecutionError("Unsupported AI output type")


def _build_job_prompt(
    output_type: str,
    *,
    profile: UserProfile | None,
    job: Job,
    surface: str = "default",
) -> tuple[str, str]:
    title, instruction = _output_request(output_type, surface=surface)
    prompt = (
        f"{instruction}\n\n"
        f"User profile:\n{_profile_context(profile)}\n\n"
        f"Job:\n{_job_context(job)}"
    )
    return title, prompt


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
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        with request.urlopen(req, timeout=20, context=ssl_context) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise AiExecutionError(_http_error_message(setting, exc)) from exc
    except error.URLError as exc:
        raise AiExecutionError(_url_error_message(setting, exc)) from exc

    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AiExecutionError("AI provider returned no choices")
    message = choices[0].get("message", {})
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise AiExecutionError("AI provider returned an empty response")
    return content.strip()


def _open_provider_api_key(setting: AiProviderSetting) -> str:
    try:
        value = open_secret(setting.api_key_encrypted)
    except SecretEnvelopeError as exc:
        raise AiExecutionError("Stored API key could not be opened. Re-save the provider in Settings.") from exc
    if not value:
        raise AiExecutionError("Enabled AI provider is missing an API key")
    return value


def _call_openai(setting: AiProviderSetting, prompt: str) -> str:
    if not setting.model_name:
        raise AiExecutionError("Enabled AI provider is missing a model name")
    api_key = _open_provider_api_key(setting)
    endpoint_root = (setting.base_url or "https://api.openai.com/v1").rstrip("/")
    payload = {
        "model": setting.model_name,
        "input": prompt,
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint_root + "/responses",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        with request.urlopen(req, timeout=20, context=ssl_context) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise AiExecutionError(_http_error_message(setting, exc)) from exc
    except error.URLError as exc:
        raise AiExecutionError(_url_error_message(setting, exc)) from exc

    output_text = raw.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = raw.get("output")
    if isinstance(output, list):
        for item in output:
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for entry in content:
                text = entry.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()
    raise AiExecutionError("AI provider returned an empty response")


def _call_gemini(setting: AiProviderSetting, prompt: str) -> str:
    if not setting.model_name:
        raise AiExecutionError("Enabled AI provider is missing a model name")
    api_key = _open_provider_api_key(setting)
    endpoint_root = (setting.base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are an assistant helping a jobseeker inside a private application tracker.\n\n"
                            + prompt
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint_root + f"/models/{setting.model_name}:generateContent",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        with request.urlopen(req, timeout=20, context=ssl_context) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise AiExecutionError(_http_error_message(setting, exc)) from exc
    except error.URLError as exc:
        raise AiExecutionError(_url_error_message(setting, exc)) from exc

    candidates = raw.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise AiExecutionError("AI provider returned no candidates")
    for candidate in candidates:
        content = candidate.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue
        for part in parts:
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    raise AiExecutionError("AI provider returned an empty response")


def generate_job_ai_output(
    db: Session,
    user: User,
    job: Job,
    *,
    output_type: str,
    profile: UserProfile | None = None,
    surface: str = "default",
) -> AiOutput:
    setting = get_enabled_ai_provider(db, user)
    if setting is None:
        raise AiExecutionError("Enable an AI provider in Settings before generating AI output")

    title, prompt = _build_job_prompt(
        output_type,
        profile=profile,
        job=job,
        surface=surface,
    )
    if setting.provider == "openai_compatible":
        body = _call_openai_compatible(setting, prompt)
    elif setting.provider == "gemini":
        body = _call_gemini(setting, prompt)
    elif setting.provider == "openai":
        body = _call_openai(setting, prompt)
    else:
        raise AiExecutionError(
            "Anthropic execution is not implemented yet. Use OpenAI or an OpenAI-compatible endpoint."
        )
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
            "surface": surface,
        },
    )
    db.add(output)
    db.flush()
    return output
