import base64
import json
import ssl
import re
from urllib import error, request

import certifi
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.ai_output import AiOutput
from app.db.models.ai_output_competency_evidence_link import AiOutputCompetencyEvidenceLink
from app.db.models.ai_provider_setting import AiProviderSetting
from app.db.models.competency_evidence import CompetencyEvidence
from app.db.models.job import Job
from app.db.models.user import User
from app.db.models.user_profile import UserProfile
from app.security.sealed_secrets import SecretEnvelopeError, key_hint, open_secret, seal_secret
from app.db.models.artefact import Artefact
from app.services.artefacts import (
    ArtefactCandidateSummary,
    list_candidate_artefacts_for_job,
    load_artefact_document_payload,
    load_artefact_text_excerpt,
    summarise_artefact_for_ai,
)

KNOWN_PROVIDERS = ("openai", "gemini", "anthropic", "openai_compatible")
PROVIDER_DEFAULTS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-5.2",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model_name": "gemini-2.5-flash",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "model_name": "claude-sonnet-4-20250514",
    },
}
KNOWN_OUTPUT_TYPES = (
    "recommendation",
    "fit_summary",
    "draft",
    "profile_observation",
    "artefact_suggestion",
    "artefact_analysis",
    "tailoring_guidance",
    "competency_star_shaping",
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
    defaults = PROVIDER_DEFAULTS.get(provider, {})
    api_key_value = (api_key or "").strip()
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
    if provider == "openai_compatible":
        setting.base_url = (base_url or "").strip() or None
        setting.model_name = (model_name or "").strip() or None
    else:
        setting.base_url = None
        setting.model_name = (model_name or "").strip() or defaults.get("model_name")
    if api_key_value:
        setting.api_key_encrypted = seal_secret(api_key_value)
        setting.api_key_hint = key_hint(api_key_value)
        setting.discovered_models = None
        setting.model_discovery_status = None
        setting.model_discovery_error = None
    if is_enabled:
        if not setting.api_key_encrypted:
            raise ValueError("Enabled AI provider is missing an API key")
        if provider == "openai_compatible" and not setting.base_url:
            raise ValueError("OpenAI-compatible provider requires a base URL")
        if not setting.model_name:
            raise ValueError("Enabled AI provider is missing a model name")
    setting.is_enabled = is_enabled
    if is_enabled:
        for other_setting in list_user_ai_provider_settings(db, user):
            if other_setting.provider != provider and other_setting.is_enabled:
                other_setting.is_enabled = False
    db.flush()
    return setting


def save_ai_provider_key_and_discover_models(
    db: Session,
    user: User,
    *,
    provider: str,
    label: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> AiProviderSetting:
    if provider not in KNOWN_PROVIDERS:
        raise ValueError("Unsupported AI provider")
    setting = upsert_ai_provider_setting(
        db,
        user,
        provider=provider,
        label=label,
        base_url=base_url,
        model_name=None,
        api_key=api_key,
        is_enabled=False,
    )
    api_key_value = (api_key or "").strip()
    if not api_key_value and not setting.api_key_encrypted:
        raise ValueError("Save an API key before discovering models")
    try:
        models = discover_ai_provider_models(setting, api_key=api_key_value or None)
    except AiExecutionError as exc:
        if provider == "openai_compatible":
            setting.discovered_models = []
            setting.model_discovery_status = "failed"
            setting.model_discovery_error = str(exc)
            db.flush()
            return setting
        raise ValueError(str(exc)) from exc
    setting.discovered_models = models
    setting.model_discovery_status = "ready"
    setting.model_discovery_error = None
    default_model = provider_default_model(provider)
    discovered_ids = {model["id"] for model in models}
    if default_model and default_model in discovered_ids:
        setting.model_name = default_model
    elif models and setting.model_name not in discovered_ids:
        setting.model_name = models[0]["id"]
    db.flush()
    return setting


def enable_ai_provider_model(
    db: Session,
    user: User,
    *,
    provider: str,
    model_name: str,
) -> AiProviderSetting:
    if provider not in KNOWN_PROVIDERS:
        raise ValueError("Unsupported AI provider")
    setting = db.scalar(
        select(AiProviderSetting).where(
            AiProviderSetting.owner_user_id == user.id,
            AiProviderSetting.provider == provider,
        )
    )
    if setting is None or not setting.api_key_encrypted:
        raise ValueError("Save and validate an API key before enabling this provider")
    selected = (model_name or "").strip()
    if not selected:
        raise ValueError("Select a model before enabling this provider")
    discovered = setting.discovered_models if isinstance(setting.discovered_models, list) else []
    discovered_ids = {item.get("id") for item in discovered if isinstance(item, dict)}
    if discovered_ids and selected not in discovered_ids:
        raise ValueError("Selected model was not returned by provider discovery")
    if not discovered_ids and provider != "openai_compatible":
        raise ValueError("Discover provider models before enabling this provider")
    setting.model_name = selected
    setting.is_enabled = True
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
    def __init__(self, message: str, *, diagnostics: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def _ai_debug_value(value: object) -> str | None:
    if value in (None, "", False):
        return None
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).strip()
    return text or None


def _ai_debug_summary(exc: AiExecutionError) -> str:
    if not exc.diagnostics:
        return ""
    ordered_keys = (
        "action",
        "provider",
        "model",
        "content_mode",
        "document_attached",
        "prompt_chars",
        "timeout_seconds",
        "job_uuid",
        "artefact_uuid",
    )
    parts: list[str] = []
    for key in ordered_keys:
        value = _ai_debug_value(exc.diagnostics.get(key))
        if value is not None:
            parts.append(f"{key}={value}")
    return " | ".join(parts)


def _with_ai_diagnostics(exc: AiExecutionError, **diagnostics: object) -> AiExecutionError:
    merged = dict(exc.diagnostics)
    for key, value in diagnostics.items():
        if value is not None:
            merged[key] = value
    return AiExecutionError(str(exc), diagnostics=merged)


def _provider_label(setting: AiProviderSetting) -> str:
    return PROVIDER_LABELS.get(setting.provider, "AI provider")


def provider_default_base_url(provider: str) -> str | None:
    value = PROVIDER_DEFAULTS.get(provider, {}).get("base_url")
    return value if isinstance(value, str) else None


def provider_default_model(provider: str) -> str | None:
    value = PROVIDER_DEFAULTS.get(provider, {}).get("model_name")
    return value if isinstance(value, str) else None


def _model_option(model_id: str, *, display_name: str | None = None) -> dict[str, str]:
    option = {"id": model_id}
    if display_name and display_name != model_id:
        option["display_name"] = display_name
    return option


def _sort_model_options(models: list[dict[str, str]]) -> list[dict[str, str]]:
    def key(model: dict[str, str]) -> tuple[int, str]:
        model_id = model["id"].lower()
        preferred = model_id.startswith(("gpt-", "gemini-", "claude-"))
        return (0 if preferred else 1, model_id)

    return sorted(models, key=key)


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


def _timeout_error_message(setting: AiProviderSetting) -> str:
    provider = _provider_label(setting)
    return f"{provider} timed out before returning a response. Try again or reduce the request size."


def _provider_timeout_seconds(
    setting: AiProviderSetting,
    *,
    document_attached: bool = False,
) -> int:
    if setting.provider == "gemini":
        return 60 if document_attached else 30
    return 20


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


def _competency_evidence_context(evidence: CompetencyEvidence) -> str:
    fields = [
        ("Title", evidence.title),
        ("Competency", evidence.competency),
        ("Situation", evidence.situation),
        ("Task", evidence.task),
        ("Action", evidence.action),
        ("Result", evidence.result),
        ("Evidence notes", evidence.evidence_notes),
        ("Strength", evidence.strength),
        ("Tags", evidence.tags),
        ("Source kind", evidence.source_kind),
    ]
    visible = [f"{label}: {value}" for label, value in fields if value not in (None, "")]
    return "\n".join(visible) if visible else "No competency evidence details are available."


def _build_competency_star_shaping_prompt(
    *,
    profile: UserProfile | None,
    evidence: CompetencyEvidence,
) -> tuple[str, str]:
    title = "AI STAR shaping"
    prompt = (
        "Shape one saved competency evidence entry into a concise, truthful STAR response. "
        "Use markdown sections titled 'STAR response', 'Evidence to strengthen', 'Interview use', "
        "and 'Artefact use'. Do not invent missing facts, metrics, dates, employers, tools, or outcomes. "
        "If any STAR part is thin or missing, say exactly what the user should add. "
        "Keep the response reusable across roles rather than tailored to one specific vacancy.\n\n"
        f"User profile:\n{_profile_context(profile)}\n\n"
        f"Competency evidence:\n{_competency_evidence_context(evidence)}"
    )
    return title, prompt


def _normalise_selected_competency_evidence_uuids(values: list[str] | None) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        cleaned = (value or "").strip()
        if cleaned and cleaned not in seen:
            selected.append(cleaned)
            seen.add(cleaned)
    return selected


def _competency_result_snippet(evidence: CompetencyEvidence) -> str:
    return evidence.result or evidence.action or evidence.situation or "Result not captured yet"


def _selected_competency_evidence_context(
    db: Session,
    user: User,
    evidence_uuids: list[str] | None,
) -> tuple[list[CompetencyEvidence], dict[str, AiOutput]]:
    selected_uuids = _normalise_selected_competency_evidence_uuids(evidence_uuids)
    if not selected_uuids:
        return [], {}
    evidence_items = list(
        db.scalars(
            select(CompetencyEvidence).where(
                CompetencyEvidence.owner_user_id == user.id,
                CompetencyEvidence.uuid.in_(selected_uuids),
            )
        )
    )
    evidence_by_uuid = {evidence.uuid: evidence for evidence in evidence_items}
    ordered_evidence = [evidence_by_uuid[uuid] for uuid in selected_uuids if uuid in evidence_by_uuid]
    if not ordered_evidence:
        return [], {}

    outputs = db.scalars(
        select(AiOutput)
        .where(
            AiOutput.owner_user_id == user.id,
            AiOutput.output_type == "competency_star_shaping",
            AiOutput.status == "active",
        )
        .order_by(AiOutput.updated_at.desc(), AiOutput.created_at.desc())
    )
    selected_set = {evidence.uuid for evidence in ordered_evidence}
    latest_by_evidence_uuid: dict[str, AiOutput] = {}
    for output in outputs:
        source_context = output.source_context or {}
        evidence_uuid = source_context.get("competency_evidence_uuid")
        if (
            isinstance(evidence_uuid, str)
            and evidence_uuid in selected_set
            and evidence_uuid not in latest_by_evidence_uuid
        ):
            latest_by_evidence_uuid[evidence_uuid] = output
    return ordered_evidence, latest_by_evidence_uuid


def _competency_evidence_generation_summary(
    evidence_items: list[CompetencyEvidence],
    latest_shaping_by_evidence_uuid: dict[str, AiOutput],
) -> str:
    if not evidence_items:
        return ""
    rows: list[str] = [
        "Selected competency evidence is user-owned accomplishment context, not verified content from the selected artefact.",
        "Use it only where it helps ground examples. Do not invent metrics, tools, dates, employers, or outcomes beyond the saved evidence.",
    ]
    for index, evidence in enumerate(evidence_items, start=1):
        parts = [
            f"{index}. {evidence.title}",
            f"Competency: {evidence.competency or 'not set'}",
            f"Strength: {evidence.strength}",
            f"Reusable result/action: {_competency_result_snippet(evidence)}",
        ]
        if evidence.evidence_notes:
            parts.append(f"Credibility notes: {evidence.evidence_notes}")
        shaping = latest_shaping_by_evidence_uuid.get(evidence.uuid)
        if shaping is not None and shaping.body:
            parts.append(f"Latest STAR shaping:\n{shaping.body}")
        rows.append("\n".join(parts))
    return "\n\n".join(rows)


def _competency_evidence_source_refs(
    evidence_items: list[CompetencyEvidence],
    latest_shaping_by_evidence_uuid: dict[str, AiOutput],
) -> list[dict[str, object]]:
    refs: list[dict[str, object]] = []
    for evidence in evidence_items:
        shaping = latest_shaping_by_evidence_uuid.get(evidence.uuid)
        ref: dict[str, object] = {
            "uuid": evidence.uuid,
            "title": evidence.title,
            "competency": evidence.competency,
            "strength": evidence.strength,
        }
        if shaping is not None:
            ref["latest_star_shaping_output_id"] = shaping.id
        refs.append(ref)
    return refs


def _competency_evidence_snapshot(evidence: CompetencyEvidence) -> dict[str, object]:
    return {
        "uuid": evidence.uuid,
        "title": evidence.title,
        "competency": evidence.competency,
        "situation": evidence.situation,
        "task": evidence.task,
        "action": evidence.action,
        "result": evidence.result,
        "evidence_notes": evidence.evidence_notes,
        "strength": evidence.strength,
        "tags": evidence.tags,
        "source_kind": evidence.source_kind,
        "source_job_id": evidence.source_job_id,
        "source_artefact_id": evidence.source_artefact_id,
        "source_ai_output_id": evidence.source_ai_output_id,
    }


def _create_competency_evidence_links(
    db: Session,
    user: User,
    output: AiOutput,
    evidence_items: list[CompetencyEvidence],
    latest_shaping_by_evidence_uuid: dict[str, AiOutput],
    *,
    use_intent: str = "grounding",
    draft_kind: str | None = None,
) -> None:
    for evidence in evidence_items:
        shaping = latest_shaping_by_evidence_uuid.get(evidence.uuid)
        db.add(
            AiOutputCompetencyEvidenceLink(
                owner_user_id=user.id,
                ai_output_id=output.id,
                competency_evidence_id=evidence.id,
                job_id=output.job_id,
                artefact_id=output.artefact_id,
                output_type=output.output_type,
                draft_kind=draft_kind,
                use_intent=use_intent,
                user_selected=True,
                evidence_uuid=evidence.uuid,
                evidence_title=evidence.title,
                evidence_competency=evidence.competency,
                evidence_strength=evidence.strength,
                evidence_result_action_snippet=_competency_result_snippet(evidence),
                latest_star_shaping_output_id=shaping.id if shaping is not None else None,
                evidence_snapshot=_competency_evidence_snapshot(evidence),
            )
        )


def _build_artefact_suggestion_prompt(
    *,
    profile: UserProfile | None,
    job: Job,
    candidates: list[ArtefactCandidateSummary],
    candidate_analyses: list[AiOutput] | None = None,
) -> tuple[str, str]:
    title = "AI artefact suggestion"
    analyses_by_uuid: dict[str, AiOutput] = {}
    for analysis in candidate_analyses or []:
        source_context = analysis.source_context or {}
        artefact_uuid = source_context.get("artefact_uuid")
        if isinstance(artefact_uuid, str) and artefact_uuid:
            analyses_by_uuid[artefact_uuid] = analysis
    if candidates:
        candidate_rows: list[str] = []
        for index, candidate in enumerate(candidates):
            analysis = analyses_by_uuid.get(candidate.artefact_uuid)
            analysis_block = ""
            if analysis is not None:
                blocks: list[str] = []
                if analysis.body:
                    blocks.append(f"Candidate analysis {index + 1}:\n{analysis.body}")
                index_summary = _artefact_index_summary(analysis.source_context or {})
                if index_summary:
                    blocks.append(f"Candidate analysis index {index + 1}:\n{index_summary}")
                analysis_block = "\n" + "\n\n".join(blocks) if blocks else ""
            candidate_rows.append(
                (
                    f"Candidate {index + 1}:\n"
                    f"{candidate.summary_text}\n"
                    f"Outcome signals:\n{candidate.outcome_signal_summary.summary_text}"
                    f"{analysis_block}"
                )
            )
        candidate_block = "\n\n".join(candidate_rows)
    else:
        candidate_block = "No existing artefacts are available for this user."
    prompt = (
        "Recommend which existing artefacts should be reused or adapted for this job. "
        "Use markdown sections titled 'Best starting artefact', 'Other usable candidates', "
        "'Missing artefacts', 'Why', and 'What to adapt before submission'. "
        "Prefer 'no suitable artefact' over weak guesses. "
        "Do not invent unseen document content. "
        "Use the provided artefact summaries and outcome signals conservatively.\n\n"
        f"User profile:\n{_profile_context(profile)}\n\n"
        f"Job:\n{_job_context(job)}\n\n"
        f"Candidate artefacts:\n{candidate_block}"
    )
    return title, prompt


def _infer_job_artefact_requirements(job: Job) -> dict[str, object]:
    text = "\n".join(
        part for part in (job.title or "", job.description_raw or "") if part
    ).lower()
    required: list[str] = []
    optional: list[str] = []

    def add_unique(items: list[str], label: str) -> None:
        if label not in items:
            items.append(label)

    if "cover letter" in text:
        add_unique(required, "cover letter")
    if "supporting statement" in text or "personal statement" in text:
        add_unique(required, "supporting statement")
    if "writing sample" in text:
        add_unique(required, "writing sample")
    if "portfolio" in text:
        add_unique(optional, "portfolio")
    if "attestation" in text:
        add_unique(required, "attestation")

    summary_parts: list[str] = []
    if required:
        summary_parts.append("Required or explicitly requested: " + ", ".join(required))
    else:
        summary_parts.append("No explicit additional artefact requirement was detected in the job text.")
    if optional:
        summary_parts.append("Optional or supplementary artefacts mentioned: " + ", ".join(optional))

    return {
        "required": required,
        "optional": optional,
        "summary_text": " ".join(summary_parts),
    }


_SECTION_PATTERNS: tuple[tuple[str, str], ...] = (
    ("summary", r"\b(summary|profile|professional summary)\b"),
    ("experience", r"\b(experience|employment|work experience|professional experience)\b"),
    ("skills", r"\b(skills|technical skills|core skills)\b"),
    ("education", r"\b(education|academic background)\b"),
    ("certifications", r"\b(certifications|certificates|licenses)\b"),
    ("projects", r"\b(projects|selected projects)\b"),
    ("achievements", r"\b(achievements|accomplishments|key achievements)\b"),
)

_SENIORITY_TERMS: tuple[str, ...] = (
    "staff",
    "senior staff",
    "principal",
    "lead",
    "senior",
    "manager",
    "director",
    "head",
    "vp",
    "executive",
)

_TOOLING_DOMAIN_TERMS: tuple[str, ...] = (
    "aws",
    "azure",
    "gcp",
    "google cloud",
    "kubernetes",
    "terraform",
    "gitlab",
    "github",
    "jira",
    "ci/cd",
    "distributed systems",
    "cloud infrastructure",
    "platform",
    "security",
    "devsecops",
    "product",
    "analytics",
    "python",
    "sql",
)

_ACCOMPLISHMENT_TERMS: tuple[str, ...] = (
    "delivered",
    "launched",
    "increased",
    "reduced",
    "improved",
    "scaled",
    "saved",
    "optimized",
    "grew",
    "built",
    "led",
    "drove",
    "shipped",
)


def _normalise_artefact_text(
    artefact: Artefact,
    artefact_summary: ArtefactCandidateSummary,
    *,
    extracted_text: str | None,
) -> str:
    parts = [
        artefact.filename or "",
        artefact.kind or "",
        artefact.purpose or "",
        artefact.version_label or "",
        artefact.notes or "",
        artefact.outcome_context or "",
        artefact_summary.summary_text,
        extracted_text or "",
    ]
    return "\n".join(part for part in parts if part).lower()


def _detect_artefact_sections(text: str) -> list[str]:
    detected: list[str] = []
    for label, pattern in _SECTION_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            detected.append(label)
    return detected


def _estimate_accomplishment_density(text: str) -> str:
    if not text.strip():
        return "unknown"
    signals = sum(1 for term in _ACCOMPLISHMENT_TERMS if term in text)
    metric_hits = len(re.findall(r"(\d+%|\$\d+|\d+x|\d+\+)", text))
    score = signals + metric_hits
    if score >= 6:
        return "high"
    if score >= 3:
        return "moderate"
    return "low"


def _extract_ranked_terms(text: str, candidates: tuple[str, ...], *, limit: int) -> list[str]:
    found: list[str] = []
    for term in candidates:
        if term in text and term not in found:
            found.append(term)
        if len(found) >= limit:
            break
    return found


def _build_requirement_coverage_hints(
    artefact: Artefact,
    requirement_info: dict[str, object],
) -> list[str]:
    required = [str(item) for item in requirement_info.get("required", []) if isinstance(item, str)]
    optional = [str(item) for item in requirement_info.get("optional", []) if isinstance(item, str)]
    kind = (artefact.kind or "").replace("_", " ").strip().lower()
    hints: list[str] = []
    if kind and kind in required:
        hints.append(f"matches required artefact type: {kind}")
    elif required:
        hints.append("job requests additional artefacts beyond this baseline: " + ", ".join(required))
    if kind and kind in optional:
        hints.append(f"matches optional supporting artefact type: {kind}")
    elif optional:
        hints.append("job mentions optional supporting artefacts: " + ", ".join(optional))
    if not hints:
        hints.append("no explicit extra artefact requirement detected")
    return hints[:3]


def _build_artefact_structured_index(
    artefact: Artefact,
    artefact_summary: ArtefactCandidateSummary,
    *,
    extracted_text: str | None,
    requirement_info: dict[str, object],
) -> dict[str, object]:
    text = _normalise_artefact_text(
        artefact,
        artefact_summary,
        extracted_text=extracted_text,
    )
    return {
        "detected_sections": _detect_artefact_sections(text),
        "accomplishment_density": _estimate_accomplishment_density(text),
        "seniority_indicators": _extract_ranked_terms(text, _SENIORITY_TERMS, limit=5),
        "tooling_or_domain_mentions": _extract_ranked_terms(text, _TOOLING_DOMAIN_TERMS, limit=8),
        "requirement_coverage_hints": _build_requirement_coverage_hints(artefact, requirement_info),
    }


def _artefact_index_summary(index: dict[str, object] | None) -> str:
    if not index:
        return ""
    rows: list[str] = []
    sections = index.get("detected_sections")
    if isinstance(sections, list) and sections:
        rows.append("Detected sections: " + ", ".join(str(item) for item in sections))
    density = index.get("accomplishment_density")
    if isinstance(density, str) and density:
        rows.append("Accomplishment density: " + density)
    seniority = index.get("seniority_indicators")
    if isinstance(seniority, list) and seniority:
        rows.append("Seniority indicators: " + ", ".join(str(item) for item in seniority))
    tooling = index.get("tooling_or_domain_mentions")
    if isinstance(tooling, list) and tooling:
        rows.append("Tooling/domain mentions: " + ", ".join(str(item) for item in tooling))
    hints = index.get("requirement_coverage_hints")
    if isinstance(hints, list) and hints:
        rows.append("Requirement coverage hints: " + "; ".join(str(item) for item in hints))
    return "\n".join(rows)


def _artefact_requirement_strategy_summary(
    *,
    artefact: Artefact | None,
    requirement_info: dict[str, object],
    draft_kind: str | None = None,
) -> str:
    required = [str(item) for item in requirement_info.get("required", []) if isinstance(item, str)]
    optional = [str(item) for item in requirement_info.get("optional", []) if isinstance(item, str)]
    baseline_kind = ((artefact.kind or "") if artefact is not None else "").replace("_", " ").strip().lower()
    draft_kind_label = (draft_kind or "").replace("_draft", "").replace("_", " ").strip().lower()
    lines: list[str] = []
    if required:
        lines.append("Required or explicitly requested artefacts: " + ", ".join(required))
    else:
        lines.append("No explicit extra artefact requirement detected in the job text.")
    if optional:
        lines.append("Optional or supplementary artefacts mentioned: " + ", ".join(optional))
    if baseline_kind:
        if baseline_kind in required:
            lines.append(f"Selected baseline matches a required artefact type: {baseline_kind}")
        elif required:
            lines.append(
                "Selected baseline does not satisfy all explicitly requested artefact types by itself; "
                "guide the user on what should exist alongside it."
            )
    if draft_kind_label:
        if draft_kind_label in required:
            lines.append(f"The requested draft type directly satisfies one explicit job requirement: {draft_kind_label}")
        elif required:
            lines.append(
                "The requested draft type should stay consistent with the explicitly requested submission pack: "
                + ", ".join(required)
            )
    return "\n".join(lines)


def _draft_evidence_allocation_summary(
    *,
    draft_kind: str,
    requirement_info: dict[str, object],
) -> str:
    required = [str(item) for item in requirement_info.get("required", []) if isinstance(item, str)]
    lines: list[str] = []
    if draft_kind == "resume_draft":
        lines.append("Keep the resume focused on concrete role-relevant evidence, impact, scope, and skills.")
        if "supporting statement" in required:
            lines.append(
                "Do not overload the resume with long criteria-by-criteria narrative that belongs in the supporting statement."
            )
        if "cover letter" in required:
            lines.append(
                "Do not spend resume space on motivational opening/closing language that belongs in the cover letter."
            )
    elif draft_kind == "cover_letter_draft":
        lines.append("Use the cover letter for concise role motivation, fit framing, and a small number of high-signal examples.")
        if "supporting statement" in required:
            lines.append(
                "Do not turn the cover letter into a full criteria response if a supporting statement is also requested."
            )
    elif draft_kind == "supporting_statement_draft":
        lines.append("Use the supporting statement for explicit criteria coverage, fuller examples, and structured narrative evidence.")
        lines.append("Do not merely repeat resume bullets; expand them into context, actions, and outcomes where relevant.")
    elif draft_kind == "attestation_draft":
        lines.append("Keep the attestation factual and declarative, using concise supporting evidence rather than broad narrative.")
    return "\n".join(lines)


def _draft_section_emphasis_summary(
    *,
    draft_kind: str,
    artefact_analysis: AiOutput | None,
) -> str:
    if artefact_analysis is None:
        return ""
    source_context = artefact_analysis.source_context or {}
    sections = source_context.get("detected_sections")
    accomplishment_density = source_context.get("accomplishment_density")
    seniority = source_context.get("seniority_indicators")
    tooling = source_context.get("tooling_or_domain_mentions")

    section_list = [str(item) for item in sections] if isinstance(sections, list) else []
    seniority_list = [str(item) for item in seniority] if isinstance(seniority, list) else []
    tooling_list = [str(item) for item in tooling] if isinstance(tooling, list) else []

    lines: list[str] = []
    if draft_kind == "resume_draft":
        if accomplishment_density == "high":
            lines.append("Foreground quantified outcomes and impact bullets in the main evidence sections.")
        elif accomplishment_density in {"low", "unknown"}:
            lines.append("Keep claims restrained where quantified outcomes are thin; avoid overstating impact.")
        if "summary" in section_list:
            lines.append("Preserve a concise professional summary rather than expanding it into a long narrative block.")
        if "experience" in section_list:
            lines.append("Keep the experience section focused on the strongest role-relevant delivery evidence.")
        if "skills" in section_list and tooling_list:
            lines.append("Use the skills area to foreground the strongest relevant tooling/domain terms: " + ", ".join(tooling_list[:4]))
        elif "skills" in section_list:
            lines.append("Use the skills area to foreground the strongest role-relevant tools and domains.")
    elif draft_kind == "cover_letter_draft":
        if seniority_list:
            lines.append("Use the role-fit section to foreground seniority signals such as " + ", ".join(seniority_list[:3]) + ".")
        if accomplishment_density in {"low", "unknown"}:
            lines.append("Keep example claims brief and careful where outcome evidence is limited.")
    elif draft_kind == "supporting_statement_draft":
        if accomplishment_density == "high":
            lines.append("Expand the strongest evidence into fuller STAR-style or criteria-led examples.")
        if tooling_list:
            lines.append("Thread the most relevant tooling/domain terms into the example sections: " + ", ".join(tooling_list[:4]))
    elif draft_kind == "attestation_draft":
        lines.append("Keep section content compact and factual; do not expand into multi-paragraph narrative unless the evidence clearly supports it.")

    return "\n".join(lines)


def _evidence_phrasing_guidance(
    *,
    artefact_analysis: AiOutput | None,
    content_mode: str,
    context_kind: str,
) -> str:
    source_context = artefact_analysis.source_context or {} if artefact_analysis is not None else {}
    accomplishment_density = source_context.get("accomplishment_density")
    sections = source_context.get("detected_sections")
    section_list = [str(item) for item in sections] if isinstance(sections, list) else []

    lines: list[str] = [
        "Prefer direct, specific claims that are supported by the baseline artefact or verified analysis context.",
        "Do not invent quantified outcomes, scope, tools, or seniority signals that are not evidenced.",
    ]
    if content_mode == "metadata_only":
        lines.append(
            "Because verified document text is unavailable, keep phrasing cautious and avoid implying exact wording or evidence that has not been seen."
        )
    elif content_mode == "provider_document":
        lines.append(
            "Treat the provider-readable document as the primary source of truth, but still avoid inflating vague responsibility statements into unsupported achievements."
        )
    else:
        lines.append("Use the verified extracted text as the anchor for any stronger wording.")

    if accomplishment_density == "high":
        lines.append("Where the source clearly supports outcomes, use confident but precise impact phrasing.")
    elif accomplishment_density == "moderate":
        lines.append("Blend outcome language with role-scope language; do not overstate impact where the evidence is mixed.")
    else:
        lines.append("Where evidence is thin or mostly responsibility-based, use measured wording and mark gaps explicitly instead of polishing them into strengths.")

    if "achievements" not in section_list and "projects" not in section_list and context_kind == "draft":
        lines.append("Do not force an achievements-heavy tone if the baseline appears to rely more on experience/responsibility structure than explicit achievement sections.")
    return "\n".join(lines)


def _submission_pack_coordination_summary(
    *,
    draft_kind: str | None,
    requirement_info: dict[str, object],
) -> str:
    required = [str(item) for item in requirement_info.get("required", []) if isinstance(item, str)]
    optional = [str(item) for item in requirement_info.get("optional", []) if isinstance(item, str)]
    lines: list[str] = []
    if required:
        lines.append("Explicit submission pack requirements: " + ", ".join(required))
    if optional:
        lines.append("Optional or supplementary pack elements: " + ", ".join(optional))
    if not required and not optional:
        lines.append("No multi-document requirement is explicit in the job text; keep the submission pack focused and avoid unnecessary duplication.")
    if draft_kind == "resume_draft":
        if "cover letter" in required:
            lines.append("Keep motivation and narrative framing out of the resume when a cover letter is also part of the pack.")
        if "supporting statement" in required:
            lines.append("Leave longer criteria-by-criteria explanation to the supporting statement and keep the resume evidence-led.")
    elif draft_kind == "cover_letter_draft":
        if "supporting statement" in required:
            lines.append("Use the cover letter for concise framing and reserve fuller criteria evidence for the supporting statement.")
        if "resume" in required or not required:
            lines.append("Do not duplicate the resume bullet structure; use the letter to connect the evidence to role motivation.")
    elif draft_kind == "supporting_statement_draft":
        lines.append("Use this document to carry the densest requirement-by-requirement evidence so the other documents can stay tighter.")
    elif draft_kind == "attestation_draft":
        lines.append("Keep this document factual and supportive of the wider pack rather than repeating the narrative from other artefacts.")
    else:
        lines.append("Coordinate the submission pack so each artefact carries a distinct job-appropriate role.")
    return "\n".join(lines)


def _prepare_artefact_analysis_context(
    artefact: Artefact,
    *,
    setting: AiProviderSetting | None = None,
) -> tuple[str, bool, str | None, dict[str, object] | None]:
    extracted_text = load_artefact_text_excerpt(artefact)
    if extracted_text:
        return "extracted_text", True, extracted_text, None
    if setting is not None and setting.provider == "gemini":
        provider_document = load_artefact_document_payload(artefact)
        if provider_document is not None:
            mime_type, raw = provider_document
            return "provider_document", False, None, {"mime_type": mime_type, "data": raw}
    return "metadata_only", False, None, None


def _build_artefact_analysis_prompt(
    *,
    profile: UserProfile | None,
    job: Job,
    artefact_summary: ArtefactCandidateSummary,
    content_mode: str,
    extracted_text: str | None = None,
    requirement_summary: str,
    structured_index: dict[str, object] | None = None,
) -> tuple[str, str]:
    title = "AI artefact analysis"
    content_block = "Verified artefact text is unavailable. Analyze from metadata and job context only."
    if content_mode == "extracted_text" and extracted_text:
        content_block = f"Verified extracted artefact text:\n{extracted_text}"
    elif content_mode == "provider_document":
        content_block = "A provider-readable document payload is attached. Use it as the primary artefact content source."
    structured_index_block = ""
    index_summary = _artefact_index_summary(structured_index)
    if index_summary:
        structured_index_block = f"\n\nPrecomputed structured signals:\n{index_summary}"
    prompt = (
        "Analyze one artefact against one job. "
        "Use markdown sections titled 'Artefact type and structure', 'What this artefact emphasizes', "
        "'Evidence strength', 'Gaps or weak signals', 'Job requirement match', 'How well this fits the vacancy', "
        "and 'Best next improvements'. "
        "Keep the assessment qualitative and concrete. Do not assign scores. "
        "If verified artefact text is unavailable, say clearly that you are reasoning from metadata and job context only. "
        "Treat historical outcome signals as secondary supporting context, not the main explanation of quality.\n\n"
        f"User profile:\n{_profile_context(profile)}\n\n"
        f"Job:\n{_job_context(job)}\n\n"
        f"Inferred artefact requirements:\n{requirement_summary}\n\n"
        f"Selected artefact:\n{artefact_summary.summary_text}\n"
        f"Outcome signals:\n{artefact_summary.outcome_signal_summary.summary_text}\n\n"
        f"Content mode: {content_mode}\n"
        f"{content_block}"
        f"{structured_index_block}"
    )
    return title, prompt


def _build_artefact_tailoring_prompt(
    *,
    profile: UserProfile | None,
    job: Job,
    artefact: Artefact,
    artefact_summary: ArtefactCandidateSummary,
    extracted_text: str | None = None,
    prior_suggestion: AiOutput | None = None,
    artefact_analysis: AiOutput | None = None,
    requirement_strategy_summary: str | None = None,
    evidence_phrasing_summary: str | None = None,
    submission_pack_coordination_summary: str | None = None,
    generation_brief_summary: str | None = None,
    competency_evidence_summary: str | None = None,
) -> tuple[str, str]:
    title = "AI tailoring guidance"
    prior_context = ""
    if prior_suggestion is not None and prior_suggestion.body:
        prior_context = f"\n\nPrior artefact suggestion:\n{prior_suggestion.body}"
    analysis_context = ""
    if artefact_analysis is not None:
        analysis_parts: list[str] = []
        if artefact_analysis.body:
            analysis_parts.append(f"Artefact analysis:\n{artefact_analysis.body}")
        index_summary = _artefact_index_summary(artefact_analysis.source_context or {})
        if index_summary:
            analysis_parts.append(f"Artefact analysis index:\n{index_summary}")
        analysis_context = "\n\n" + "\n\n".join(analysis_parts) if analysis_parts else ""
    extracted_text_block = ""
    if extracted_text:
        extracted_text_block = f"\n\nExtracted artefact text (verified excerpt):\n{extracted_text}"
    requirement_strategy_block = ""
    if requirement_strategy_summary:
        requirement_strategy_block = f"\n\nSubmission strategy:\n{requirement_strategy_summary}"
    evidence_phrasing_block = ""
    if evidence_phrasing_summary:
        evidence_phrasing_block = f"\n\nEvidence phrasing guidance:\n{evidence_phrasing_summary}"
    pack_coordination_block = ""
    if submission_pack_coordination_summary:
        pack_coordination_block = f"\n\nSubmission pack coordination:\n{submission_pack_coordination_summary}"
    generation_brief_block = ""
    if generation_brief_summary:
        generation_brief_block = (
            "\n\nUser generation brief:\n"
            f"{generation_brief_summary}\n"
            "Use this brief to shape emphasis and tone, but do not invent evidence or claims that are not supported."
        )
    competency_evidence_block = ""
    if competency_evidence_summary:
        competency_evidence_block = (
            "\n\nSelected competency evidence:\n"
            f"{competency_evidence_summary}\n"
            "Treat this as optional user-owned accomplishment context. It is not proof that the selected artefact already contains those examples."
        )
    prompt = (
        "You are providing tailoring guidance for one selected artefact against one job. "
        "Use markdown sections titled 'Keep', 'Strengthen', 'De-emphasise or remove', "
        "'Missing evidence', 'Supporting documents', and 'How to use this artefact for this submission'. "
        "Do not invent document content. If extracted artefact text is unavailable, say that you are "
        "reasoning from metadata and prior usage history only. If extracted text is present, treat it as "
        "verified present content and keep any other claims clearly separate. Be concrete and job-specific.\n\n"
        f"User profile:\n{_profile_context(profile)}\n\n"
        f"Job:\n{_job_context(job)}\n\n"
        f"Selected artefact:\n{artefact_summary.summary_text}\n"
        f"Outcome signals:\n{artefact_summary.outcome_signal_summary.summary_text}"
        f"{analysis_context}{requirement_strategy_block}{pack_coordination_block}{evidence_phrasing_block}"
        f"{generation_brief_block}{competency_evidence_block}{extracted_text_block}{prior_context}"
    )
    return title, prompt


def _draft_request(draft_kind: str) -> tuple[str, str]:
    if draft_kind == "resume_draft":
        return (
            "AI tailored resume draft",
            (
                "Draft a tailored resume variant for this job. Use markdown sections titled "
                "'Headline', 'Professional summary', 'Relevant impact bullets', 'Skills to emphasise', "
                "and 'Gaps or evidence still needed'. If the baseline artefact content is unavailable, "
                "produce a cautious scaffold rather than pretending to rewrite exact document content. "
                "Do not invent experience."
            ),
        )
    if draft_kind == "cover_letter_draft":
        return (
            "AI cover letter draft",
            (
                "Draft a concise cover letter for this job. Use markdown sections titled "
                "'Opening', 'Role fit', 'Relevant evidence', 'Why this company or role', and 'Closing'. "
                "If the baseline artefact content is unavailable, produce a cautious scaffold based on "
                "metadata, tailoring guidance, and job context rather than inventing specifics."
            ),
        )
    if draft_kind == "supporting_statement_draft":
        return (
            "AI supporting statement draft",
            (
                "Draft a targeted supporting statement for this job. Use markdown sections titled "
                "'Fit summary', 'Relevant evidence', 'Operational examples', 'Why this role', and "
                "'Points still to evidence'. If the baseline artefact content is unavailable, produce "
                "a cautious scaffold based on metadata, tailoring guidance, and job context rather than "
                "inventing specifics."
            ),
        )
    if draft_kind == "attestation_draft":
        return (
            "AI attestation draft",
            (
                "Draft a concise attestation or supporting declaration for this job. Use markdown sections "
                "titled 'Context', 'Statement', 'Relevant evidence', and 'Closing'. If the baseline artefact "
                "content is unavailable, produce a cautious scaffold based on metadata, tailoring guidance, "
                "and job context rather than inventing specifics."
            ),
        )
    raise AiExecutionError("Unsupported draft kind")


def _build_artefact_draft_prompt(
    *,
    profile: UserProfile | None,
    job: Job,
    artefact_summary: ArtefactCandidateSummary,
    draft_kind: str,
    content_mode: str,
    extracted_text: str | None = None,
    tailoring_guidance: AiOutput | None = None,
    prior_suggestion: AiOutput | None = None,
    artefact_analysis: AiOutput | None = None,
    requirement_strategy_summary: str | None = None,
    evidence_allocation_summary: str | None = None,
    section_emphasis_summary: str | None = None,
    evidence_phrasing_summary: str | None = None,
    submission_pack_coordination_summary: str | None = None,
    generation_brief_summary: str | None = None,
    competency_evidence_summary: str | None = None,
) -> tuple[str, str]:
    title, instruction = _draft_request(draft_kind)
    content_block = "Baseline artefact content is unavailable. Reason from metadata only."
    if content_mode == "extracted_text" and extracted_text:
        content_block = f"Verified extracted artefact text:\n{extracted_text}"
    tailoring_block = ""
    if tailoring_guidance is not None and tailoring_guidance.body:
        tailoring_block = f"\n\nTailoring guidance:\n{tailoring_guidance.body}"
    prior_block = ""
    if prior_suggestion is not None and prior_suggestion.body:
        prior_block = f"\n\nPrior artefact suggestion:\n{prior_suggestion.body}"
    analysis_block = ""
    if artefact_analysis is not None:
        analysis_parts: list[str] = []
        if artefact_analysis.body:
            analysis_parts.append(f"Artefact analysis:\n{artefact_analysis.body}")
        index_summary = _artefact_index_summary(artefact_analysis.source_context or {})
        if index_summary:
            analysis_parts.append(f"Artefact analysis index:\n{index_summary}")
        analysis_block = "\n\n" + "\n\n".join(analysis_parts) if analysis_parts else ""
    requirement_strategy_block = ""
    if requirement_strategy_summary:
        requirement_strategy_block = f"\n\nSubmission strategy:\n{requirement_strategy_summary}"
    evidence_allocation_block = ""
    if evidence_allocation_summary:
        evidence_allocation_block = f"\n\nEvidence allocation guidance:\n{evidence_allocation_summary}"
    section_emphasis_block = ""
    if section_emphasis_summary:
        section_emphasis_block = f"\n\nSection emphasis guidance:\n{section_emphasis_summary}"
    evidence_phrasing_block = ""
    if evidence_phrasing_summary:
        evidence_phrasing_block = f"\n\nEvidence phrasing guidance:\n{evidence_phrasing_summary}"
    pack_coordination_block = ""
    if submission_pack_coordination_summary:
        pack_coordination_block = f"\n\nSubmission pack coordination:\n{submission_pack_coordination_summary}"
    generation_brief_block = ""
    if generation_brief_summary:
        generation_brief_block = (
            "\n\nUser generation brief:\n"
            f"{generation_brief_summary}\n"
            "Use this brief to shape emphasis and tone, but do not invent evidence or claims that are not supported."
        )
    competency_evidence_block = ""
    if competency_evidence_summary:
        competency_evidence_block = (
            "\n\nSelected competency evidence:\n"
            f"{competency_evidence_summary}\n"
            "Use selected evidence to ground examples where relevant, but do not present it as verified baseline artefact content unless the baseline also supports it."
        )
    prompt = (
        f"{instruction}\n\n"
        f"User profile:\n{_profile_context(profile)}\n\n"
        f"Job:\n{_job_context(job)}\n\n"
        f"Selected baseline artefact:\n{artefact_summary.summary_text}\n"
        f"Outcome signals:\n{artefact_summary.outcome_signal_summary.summary_text}\n\n"
        f"Content mode: {content_mode}\n"
        f"{content_block}"
        f"{analysis_block}"
        f"{requirement_strategy_block}"
        f"{pack_coordination_block}"
        f"{evidence_allocation_block}"
        f"{section_emphasis_block}"
        f"{evidence_phrasing_block}"
        f"{generation_brief_block}"
        f"{competency_evidence_block}"
        f"{tailoring_block}"
        f"{prior_block}"
    )
    return title, prompt


def _normalize_generation_brief(generation_brief: dict[str, str] | None) -> dict[str, str] | None:
    if not generation_brief:
        return None
    cleaned = {
        key: value.strip()
        for key, value in generation_brief.items()
        if isinstance(value, str) and value.strip()
    }
    return cleaned or None


def _generation_brief_summary(generation_brief: dict[str, str] | None) -> str | None:
    cleaned = _normalize_generation_brief(generation_brief)
    if cleaned is None:
        return None
    labels = {
        "focus_areas": "Focus areas",
        "must_include": "Must include",
        "avoid": "Avoid or de-emphasise",
        "tone": "Tone or positioning",
        "extra_context": "Extra context",
    }
    lines = []
    for key in ("focus_areas", "must_include", "avoid", "tone", "extra_context"):
        value = cleaned.get(key)
        if value:
            lines.append(f"- {labels[key]}: {value}")
    return "\n".join(lines) if lines else None


def _infer_missing_artefacts(job: Job) -> list[str]:
    description = (job.description_raw or "").lower()
    needed = ["resume"]
    if "cover letter" in description:
        needed.append("cover letter")
    if "supporting statement" in description or "personal statement" in description:
        needed.append("supporting statement")
    if "attestation" in description:
        needed.append("attestation")
    if "writing sample" in description:
        needed.append("writing sample")
    return needed


def _build_empty_artefact_suggestion_body(job: Job, *, profile: UserProfile | None) -> str:
    target_role = profile.target_roles if profile and profile.target_roles else "this role"
    missing = _infer_missing_artefacts(job)
    missing_text = ", ".join(missing)
    role_context = f" for {target_role}" if target_role else ""
    return (
        "### Best starting artefact\n"
        "* No existing artefact is available yet for this job.\n\n"
        "### Other usable candidates\n"
        "* None yet.\n\n"
        f"### Missing artefacts\n"
        f"* Prepare at least a {missing_text}{role_context}.\n\n"
        "### Why\n"
        "* The artefact library has no current candidates to reuse or adapt for this application.\n"
        "* Starting with a clear baseline artefact will make later tailoring suggestions much stronger.\n\n"
        "### What to adapt before submission\n"
        "* Upload a baseline resume or relevant submission document first.\n"
        "* Add purpose, version, and outcome notes so future suggestions have stronger evidence.\n"
        "* If the role asks for extra materials, add those as separate artefacts rather than folding everything into one file."
    )


def _build_sparse_tailoring_guidance_body(
    job: Job,
    artefact: Artefact,
    artefact_summary: ArtefactCandidateSummary,
    *,
    prior_suggestion: AiOutput | None = None,
) -> str:
    prior_note = ""
    if prior_suggestion is not None and prior_suggestion.body:
        prior_note = (
            "\n* A prior artefact suggestion exists for this job, but the selected artefact still needs "
            "clearer metadata before stronger tailoring advice will be reliable."
        )
    return (
        "### Keep\n"
        f"* Keep `{artefact.filename}` as a possible baseline only if it is the closest available starting point for {job.title or 'this job'}.\n"
        "* Keep any clearly relevant role, domain, or delivery evidence that you know is already in the file.\n\n"
        "### Strengthen\n"
        "* Add purpose, version, and notes so the system can understand what this artefact is meant to do.\n"
        "* Link the artefact to prior jobs or outcomes if it has been used before.\n"
        "* Add outcome context when this artefact helped lead to interviews or other meaningful progress.\n\n"
        "### De-emphasise or remove\n"
        "* Avoid assuming this artefact is submission-ready until its purpose and history are clearer.\n"
        "* Do not over-index on generic content that is not obviously tied to this role.\n\n"
        "### Missing evidence\n"
        f"* Tailoring is currently working from metadata only, and this artefact has **{artefact_summary.metadata_quality}** metadata quality.\n"
        "* The current record is too thin to give high-confidence line-by-line tailoring advice.\n"
        f"* Missing metadata should be filled in first: {', '.join(part for part in ['purpose' if not artefact.purpose else '', 'version' if not artefact.version_label else '', 'notes' if not artefact.notes else '', 'outcome context' if not artefact.outcome_context else ''] if part) or 'linked history or richer artefact notes'}.\n\n"
        "### Supporting documents\n"
        "* Check the role description for extra submission requirements such as a cover letter, supporting statement, or attestation.\n"
        "* Add those as separate artefacts if they are required for this application.\n\n"
        "### How to use this artefact for this submission\n"
        "* Treat this as a baseline candidate rather than a final recommendation.\n"
        "* Improve the artefact record first, then run tailoring guidance again for stronger advice."
        f"{prior_note}"
    )


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
        with request.urlopen(req, timeout=_provider_timeout_seconds(setting), context=ssl_context) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise AiExecutionError(_http_error_message(setting, exc)) from exc
    except error.URLError as exc:
        raise AiExecutionError(_url_error_message(setting, exc)) from exc
    except TimeoutError as exc:
        raise AiExecutionError(_timeout_error_message(setting)) from exc

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


def _request_json(setting: AiProviderSetting, req: request.Request) -> dict[str, object]:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        with request.urlopen(req, timeout=_provider_timeout_seconds(setting), context=ssl_context) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise AiExecutionError(_http_error_message(setting, exc)) from exc
    except error.URLError as exc:
        raise AiExecutionError(_url_error_message(setting, exc)) from exc
    except TimeoutError as exc:
        raise AiExecutionError(_timeout_error_message(setting)) from exc
    if not isinstance(raw, dict):
        raise AiExecutionError("AI provider returned an invalid response")
    return raw


def _discover_openai_models(setting: AiProviderSetting, api_key: str) -> list[dict[str, str]]:
    endpoint_root = (setting.base_url or provider_default_base_url("openai") or "").rstrip("/")
    req = request.Request(
        endpoint_root + "/models",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    raw = _request_json(setting, req)
    data = raw.get("data")
    if not isinstance(data, list):
        raise AiExecutionError("AI provider returned no models")
    models = []
    for item in data:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id")
        if not isinstance(model_id, str) or not model_id.strip():
            continue
        models.append(_model_option(model_id.strip()))
    if not models:
        raise AiExecutionError("AI provider returned no usable models")
    return _sort_model_options(models)


def _discover_gemini_models(setting: AiProviderSetting, api_key: str) -> list[dict[str, str]]:
    endpoint_root = (setting.base_url or provider_default_base_url("gemini") or "").rstrip("/")
    req = request.Request(
        endpoint_root + "/models",
        headers={"x-goog-api-key": api_key},
        method="GET",
    )
    raw = _request_json(setting, req)
    data = raw.get("models")
    if not isinstance(data, list):
        raise AiExecutionError("AI provider returned no models")
    models = []
    for item in data:
        if not isinstance(item, dict):
            continue
        methods = item.get("supportedGenerationMethods")
        if isinstance(methods, list) and "generateContent" not in methods:
            continue
        name = item.get("name")
        model_id = name.removeprefix("models/") if isinstance(name, str) else ""
        if not model_id:
            continue
        display_name = item.get("displayName")
        models.append(_model_option(model_id, display_name=display_name if isinstance(display_name, str) else None))
    if not models:
        raise AiExecutionError("AI provider returned no usable models")
    return _sort_model_options(models)


def _discover_anthropic_models(setting: AiProviderSetting, api_key: str) -> list[dict[str, str]]:
    endpoint_root = (setting.base_url or provider_default_base_url("anthropic") or "").rstrip("/")
    req = request.Request(
        endpoint_root + "/models?limit=1000",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="GET",
    )
    raw = _request_json(setting, req)
    data = raw.get("data")
    if not isinstance(data, list):
        raise AiExecutionError("AI provider returned no models")
    models = []
    for item in data:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id")
        if not isinstance(model_id, str) or not model_id.strip():
            continue
        display_name = item.get("display_name")
        models.append(_model_option(model_id.strip(), display_name=display_name if isinstance(display_name, str) else None))
    if not models:
        raise AiExecutionError("AI provider returned no usable models")
    return models


def discover_ai_provider_models(setting: AiProviderSetting, *, api_key: str | None = None) -> list[dict[str, str]]:
    api_key_value = (api_key or "").strip() or _open_provider_api_key(setting)
    if setting.provider == "openai":
        return _discover_openai_models(setting, api_key_value)
    if setting.provider == "gemini":
        return _discover_gemini_models(setting, api_key_value)
    if setting.provider == "anthropic":
        return _discover_anthropic_models(setting, api_key_value)
    if setting.provider == "openai_compatible":
        return _discover_openai_models(setting, api_key_value)
    raise AiExecutionError("Unsupported AI provider")


def _call_openai(setting: AiProviderSetting, prompt: str) -> str:
    model_name = setting.model_name or provider_default_model("openai")
    if not model_name:
        raise AiExecutionError("Enabled AI provider is missing a model name")
    api_key = _open_provider_api_key(setting)
    endpoint_root = (setting.base_url or provider_default_base_url("openai") or "").rstrip("/")
    payload = {
        "model": model_name,
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
        with request.urlopen(req, timeout=_provider_timeout_seconds(setting), context=ssl_context) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise AiExecutionError(_http_error_message(setting, exc)) from exc
    except error.URLError as exc:
        raise AiExecutionError(_url_error_message(setting, exc)) from exc
    except TimeoutError as exc:
        raise AiExecutionError(_timeout_error_message(setting)) from exc

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


def _call_gemini(
    setting: AiProviderSetting,
    prompt: str,
    *,
    document: dict[str, object] | None = None,
) -> str:
    model_name = setting.model_name or provider_default_model("gemini")
    if not model_name:
        raise AiExecutionError("Enabled AI provider is missing a model name")
    api_key = _open_provider_api_key(setting)
    endpoint_root = (setting.base_url or provider_default_base_url("gemini") or "").rstrip("/")
    parts: list[dict[str, object]] = [
        {
            "text": (
                "You are an assistant helping a jobseeker inside a private application tracker.\n\n"
                + prompt
            )
        }
    ]
    if document is not None:
        mime_type = document.get("mime_type")
        data = document.get("data")
        if isinstance(mime_type, str) and isinstance(data, (bytes, bytearray)):
            parts.append(
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64.b64encode(bytes(data)).decode("ascii"),
                    }
                }
            )
    payload = {
        "contents": [
            {
                "parts": parts
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint_root + f"/models/{model_name}:generateContent",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        with request.urlopen(
            req,
            timeout=_provider_timeout_seconds(setting, document_attached=document is not None),
            context=ssl_context,
        ) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise AiExecutionError(_http_error_message(setting, exc)) from exc
    except error.URLError as exc:
        raise AiExecutionError(_url_error_message(setting, exc)) from exc
    except TimeoutError as exc:
        raise AiExecutionError(_timeout_error_message(setting)) from exc

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


def _call_anthropic(setting: AiProviderSetting, prompt: str) -> str:
    model_name = setting.model_name or provider_default_model("anthropic")
    if not model_name:
        raise AiExecutionError("Enabled AI provider is missing a model name")
    api_key = _open_provider_api_key(setting)
    endpoint_root = (setting.base_url or provider_default_base_url("anthropic") or "").rstrip("/")
    payload = {
        "model": model_name,
        "max_tokens": 4096,
        "system": "You are an assistant helping a jobseeker inside a private application tracker.",
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint_root + "/messages",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        with request.urlopen(req, timeout=_provider_timeout_seconds(setting), context=ssl_context) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise AiExecutionError(_http_error_message(setting, exc)) from exc
    except error.URLError as exc:
        raise AiExecutionError(_url_error_message(setting, exc)) from exc
    except TimeoutError as exc:
        raise AiExecutionError(_timeout_error_message(setting)) from exc

    content = raw.get("content")
    if not isinstance(content, list) or not content:
        raise AiExecutionError("AI provider returned no content")
    text_parts: list[str] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        if part.get("type") != "text":
            continue
        text = part.get("text")
        if isinstance(text, str) and text.strip():
            text_parts.append(text.strip())
    if text_parts:
        return "\n\n".join(text_parts)
    raise AiExecutionError("AI provider returned an empty response")


def _execute_prompt(
    setting: AiProviderSetting,
    prompt: str,
    *,
    document: dict[str, object] | None = None,
    action: str | None = None,
    content_mode: str | None = None,
    job_uuid: str | None = None,
    artefact_uuid: str | None = None,
) -> str:
    try:
        if setting.provider == "openai_compatible":
            return _call_openai_compatible(setting, prompt)
        if setting.provider == "gemini":
            return _call_gemini(setting, prompt, document=document)
        if setting.provider == "openai":
            return _call_openai(setting, prompt)
        if setting.provider == "anthropic":
            return _call_anthropic(setting, prompt)
        raise AiExecutionError("Unsupported AI provider")
    except AiExecutionError as exc:
        raise _with_ai_diagnostics(
            exc,
            action=action,
            provider=setting.provider,
            model=setting.model_name,
            content_mode=content_mode,
            document_attached=document is not None,
            prompt_chars=len(prompt),
            timeout_seconds=_provider_timeout_seconds(setting, document_attached=document is not None),
            job_uuid=job_uuid,
            artefact_uuid=artefact_uuid,
        ) from exc


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
    body = _execute_prompt(
        setting,
        prompt,
        action=output_type,
        job_uuid=job.uuid,
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


def generate_competency_star_shaping(
    db: Session,
    user: User,
    evidence: CompetencyEvidence,
    *,
    profile: UserProfile | None = None,
) -> AiOutput:
    if evidence.owner_user_id != user.id:
        raise AiExecutionError("Competency evidence not found")
    setting = get_enabled_ai_provider(db, user)
    if setting is None:
        raise AiExecutionError("Enable an AI provider in Settings before generating AI output")

    title, prompt = _build_competency_star_shaping_prompt(
        profile=profile,
        evidence=evidence,
    )
    body = _execute_prompt(
        setting,
        prompt,
        action="competency_star_shaping",
    )
    output = AiOutput(
        owner_user_id=user.id,
        output_type="competency_star_shaping",
        title=title,
        body=body,
        provider=setting.provider,
        model_name=setting.model_name,
        status="active",
        source_context={
            "surface": "competency_library",
            "competency_evidence_uuid": evidence.uuid,
            "prompt_contract": "competency_star_shaping_v1",
            "strength": evidence.strength,
            "source_kind": evidence.source_kind,
            "provider_label": setting.label,
        },
    )
    db.add(output)
    db.flush()
    return output


def generate_job_artefact_suggestion(
    db: Session,
    user: User,
    job: Job,
    *,
    profile: UserProfile | None = None,
    shortlist_limit: int = 5,
) -> AiOutput:
    candidates = list_candidate_artefacts_for_job(db, user, job, limit=shortlist_limit)
    if not candidates:
        output = AiOutput(
            owner_user_id=user.id,
            job_id=job.id,
            output_type="artefact_suggestion",
            title="AI artefact suggestion",
            body=_build_empty_artefact_suggestion_body(job, profile=profile),
            provider="system",
            model_name=None,
            status="active",
            source_context={
                "job_uuid": job.uuid,
                "job_status": job.status,
                "job_title": job.title,
                "surface": "job_workspace",
                "prompt_contract": "artefact_suggestion_v1",
                "shortlisted_artefact_uuids": [],
                "local_fallback": True,
            },
        )
        db.add(output)
        db.flush()
        return output

    setting = get_enabled_ai_provider(db, user)
    if setting is None:
        raise AiExecutionError("Enable an AI provider in Settings before generating AI output")

    analysis_targets = {candidate.artefact_uuid for candidate in candidates[:3]}
    artefacts = list(
        db.scalars(
            select(Artefact).where(
                Artefact.owner_user_id == user.id,
                Artefact.uuid.in_(analysis_targets),
            )
        )
    )
    analyses = [
        build_job_artefact_analysis(
            db,
            user,
            job,
            artefact,
            profile=profile,
            persist=False,
        )
        for artefact in artefacts
    ]
    title, prompt = _build_artefact_suggestion_prompt(
        profile=profile,
        job=job,
        candidates=candidates,
        candidate_analyses=analyses,
    )
    body = _execute_prompt(
        setting,
        prompt,
        action="artefact_suggestion",
        job_uuid=job.uuid,
    )
    output = AiOutput(
        owner_user_id=user.id,
        job_id=job.id,
        output_type="artefact_suggestion",
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
            "surface": "job_workspace",
            "prompt_contract": "artefact_suggestion_v1",
            "shortlisted_artefact_uuids": [candidate.artefact_uuid for candidate in candidates],
        },
    )
    db.add(output)
    db.flush()
    return output


def build_job_artefact_analysis(
    db: Session,
    user: User,
    job: Job,
    artefact: Artefact,
    *,
    profile: UserProfile | None = None,
    persist: bool = False,
) -> AiOutput:
    setting = get_enabled_ai_provider(db, user)
    if setting is None:
        raise AiExecutionError("Enable an AI provider in Settings before generating AI output")

    artefact_summary = summarise_artefact_for_ai(artefact, current_job=job)
    requirement_info = _infer_job_artefact_requirements(job)
    content_mode, used_extracted_text, extracted_text, document_payload = _prepare_artefact_analysis_context(
        artefact,
        setting=setting,
    )
    structured_index = _build_artefact_structured_index(
        artefact,
        artefact_summary,
        extracted_text=extracted_text,
        requirement_info=requirement_info,
    )
    title, prompt = _build_artefact_analysis_prompt(
        profile=profile,
        job=job,
        artefact_summary=artefact_summary,
        content_mode=content_mode,
        extracted_text=extracted_text,
        requirement_summary=str(requirement_info["summary_text"]),
        structured_index=structured_index,
    )
    body = _execute_prompt(
        setting,
        prompt,
        document=document_payload,
        action="artefact_analysis",
        content_mode=content_mode,
        job_uuid=job.uuid,
        artefact_uuid=artefact.uuid,
    )
    output = AiOutput(
        owner_user_id=user.id,
        job_id=job.id,
        artefact_id=artefact.id,
        output_type="artefact_analysis",
        title=title,
        body=body,
        provider=setting.provider,
        model_name=setting.model_name,
        status="active",
        source_context={
            "surface": "job_workspace",
            "job_uuid": job.uuid,
            "artefact_uuid": artefact.uuid,
            "prompt_contract": "artefact_analysis_v1",
            "content_mode": content_mode,
            "used_extracted_text": used_extracted_text,
            "inferred_requirement_summary": requirement_info["summary_text"],
            "required_artefact_types": requirement_info["required"],
            "optional_artefact_types": requirement_info["optional"],
            "structured_analysis_v": 1,
            "detected_sections": structured_index["detected_sections"],
            "accomplishment_density": structured_index["accomplishment_density"],
            "seniority_indicators": structured_index["seniority_indicators"],
            "tooling_or_domain_mentions": structured_index["tooling_or_domain_mentions"],
            "requirement_coverage_hints": structured_index["requirement_coverage_hints"],
        },
    )
    if persist:
        db.add(output)
        db.flush()
    return output


def generate_job_artefact_analysis(
    db: Session,
    user: User,
    job: Job,
    artefact: Artefact,
    *,
    profile: UserProfile | None = None,
) -> AiOutput:
    return build_job_artefact_analysis(
        db,
        user,
        job,
        artefact,
        profile=profile,
        persist=True,
    )


def generate_job_artefact_tailoring_guidance(
    db: Session,
    user: User,
    job: Job,
    artefact: Artefact,
    *,
    profile: UserProfile | None = None,
    prior_suggestion: AiOutput | None = None,
    generation_brief: dict[str, str] | None = None,
    selected_competency_evidence_uuids: list[str] | None = None,
) -> AiOutput:
    artefact_summary = summarise_artefact_for_ai(artefact, current_job=job)
    extracted_text = load_artefact_text_excerpt(artefact)
    used_extracted_text = bool(extracted_text)
    requirement_info = _infer_job_artefact_requirements(job)
    requirement_strategy_summary = _artefact_requirement_strategy_summary(
        artefact=artefact,
        requirement_info=requirement_info,
    )
    submission_pack_coordination_summary = _submission_pack_coordination_summary(
        draft_kind=None,
        requirement_info=requirement_info,
    )
    generation_brief = _normalize_generation_brief(generation_brief)
    generation_brief_summary = _generation_brief_summary(generation_brief)
    selected_evidence, latest_shaping = _selected_competency_evidence_context(
        db,
        user,
        selected_competency_evidence_uuids,
    )
    selected_evidence_uuids = [evidence.uuid for evidence in selected_evidence]
    competency_evidence_summary = _competency_evidence_generation_summary(selected_evidence, latest_shaping)
    competency_evidence_refs = _competency_evidence_source_refs(selected_evidence, latest_shaping)
    if artefact_summary.metadata_quality == "thin" and not used_extracted_text:
        output = AiOutput(
            owner_user_id=user.id,
            job_id=job.id,
            artefact_id=artefact.id,
            output_type="tailoring_guidance",
            title="AI tailoring guidance",
            body=_build_sparse_tailoring_guidance_body(
                job,
                artefact,
                artefact_summary,
                prior_suggestion=prior_suggestion,
            ),
            provider="system",
            model_name=None,
            status="active",
            source_context={
                "surface": "job_workspace",
                "job_uuid": job.uuid,
                "artefact_uuid": artefact.uuid,
                "prompt_contract": "artefact_tailoring_v1",
                "used_extracted_text": False,
                "metadata_quality": artefact_summary.metadata_quality,
                "local_fallback": True,
                "draft_handoff_contract": "artefact_draft_seed_v1",
                "generation_brief": generation_brief,
                "selected_competency_evidence_uuids": selected_evidence_uuids,
                "selected_competency_evidence_refs": competency_evidence_refs,
                "competency_evidence_contract": "competency_evidence_generation_context_v1",
                **(
                    {"artefact_suggestion_output_id": prior_suggestion.id}
                    if prior_suggestion is not None
                    else {}
                ),
            },
        )
        db.add(output)
        db.flush()
        _create_competency_evidence_links(db, user, output, selected_evidence, latest_shaping)
        return output

    setting = get_enabled_ai_provider(db, user)
    if setting is None:
        raise AiExecutionError("Enable an AI provider in Settings before generating AI output")

    artefact_analysis = build_job_artefact_analysis(
        db,
        user,
        job,
        artefact,
        profile=profile,
        persist=False,
    )
    evidence_phrasing_summary = _evidence_phrasing_guidance(
        artefact_analysis=artefact_analysis,
        content_mode="extracted_text" if used_extracted_text else "metadata_only",
        context_kind="tailoring",
    )
    title, prompt = _build_artefact_tailoring_prompt(
        profile=profile,
        job=job,
        artefact=artefact,
        artefact_summary=artefact_summary,
        extracted_text=extracted_text,
        prior_suggestion=prior_suggestion,
        artefact_analysis=artefact_analysis,
        requirement_strategy_summary=requirement_strategy_summary,
        evidence_phrasing_summary=evidence_phrasing_summary,
        submission_pack_coordination_summary=submission_pack_coordination_summary,
        generation_brief_summary=generation_brief_summary,
        competency_evidence_summary=competency_evidence_summary,
    )
    body = _execute_prompt(
        setting,
        prompt,
        action="tailoring_guidance",
        content_mode="extracted_text" if used_extracted_text else "metadata_only",
        job_uuid=job.uuid,
        artefact_uuid=artefact.uuid,
    )
    output = AiOutput(
        owner_user_id=user.id,
        job_id=job.id,
        artefact_id=artefact.id,
        output_type="tailoring_guidance",
        title=title,
        body=body,
        provider=setting.provider,
        model_name=setting.model_name,
        status="active",
        source_context={
            "surface": "job_workspace",
            "job_uuid": job.uuid,
            "artefact_uuid": artefact.uuid,
            "prompt_contract": "artefact_tailoring_v1",
            "artefact_suggestion_output_id": prior_suggestion.id if prior_suggestion is not None else None,
            "used_extracted_text": used_extracted_text,
            "metadata_quality": artefact_summary.metadata_quality,
            "draft_handoff_contract": "artefact_draft_seed_v1",
            "inferred_requirement_summary": requirement_info["summary_text"],
            "required_artefact_types": requirement_info["required"],
            "optional_artefact_types": requirement_info["optional"],
            "generation_brief": generation_brief,
            "selected_competency_evidence_uuids": selected_evidence_uuids,
            "selected_competency_evidence_refs": competency_evidence_refs,
            "competency_evidence_contract": "competency_evidence_generation_context_v1",
        },
    )
    db.add(output)
    db.flush()
    _create_competency_evidence_links(db, user, output, selected_evidence, latest_shaping)
    return output


def generate_job_artefact_draft(
    db: Session,
    user: User,
    job: Job,
    artefact: Artefact,
    *,
    draft_kind: str,
    profile: UserProfile | None = None,
    tailoring_guidance: AiOutput | None = None,
    prior_suggestion: AiOutput | None = None,
    generation_brief: dict[str, str] | None = None,
    selected_competency_evidence_uuids: list[str] | None = None,
) -> AiOutput:
    setting = get_enabled_ai_provider(db, user)
    if setting is None:
        raise AiExecutionError("Enable an AI provider in Settings before generating AI output")

    artefact_summary = summarise_artefact_for_ai(artefact, current_job=job)
    extracted_text = load_artefact_text_excerpt(artefact)
    requirement_info = _infer_job_artefact_requirements(job)
    requirement_strategy_summary = _artefact_requirement_strategy_summary(
        artefact=artefact,
        requirement_info=requirement_info,
        draft_kind=draft_kind,
    )
    evidence_allocation_summary = _draft_evidence_allocation_summary(
        draft_kind=draft_kind,
        requirement_info=requirement_info,
    )
    submission_pack_coordination_summary = _submission_pack_coordination_summary(
        draft_kind=draft_kind,
        requirement_info=requirement_info,
    )
    document_payload = None
    content_mode = "extracted_text" if extracted_text else "metadata_only"
    if extracted_text is None and setting.provider == "gemini":
        provider_document = load_artefact_document_payload(artefact)
        if provider_document is not None:
            mime_type, raw = provider_document
            document_payload = {"mime_type": mime_type, "data": raw}
            content_mode = "provider_document"
    artefact_analysis = build_job_artefact_analysis(
        db,
        user,
        job,
        artefact,
        profile=profile,
        persist=False,
    )
    generation_brief = _normalize_generation_brief(generation_brief)
    generation_brief_summary = _generation_brief_summary(generation_brief)
    selected_evidence, latest_shaping = _selected_competency_evidence_context(
        db,
        user,
        selected_competency_evidence_uuids,
    )
    selected_evidence_uuids = [evidence.uuid for evidence in selected_evidence]
    competency_evidence_summary = _competency_evidence_generation_summary(selected_evidence, latest_shaping)
    competency_evidence_refs = _competency_evidence_source_refs(selected_evidence, latest_shaping)
    section_emphasis_summary = _draft_section_emphasis_summary(
        draft_kind=draft_kind,
        artefact_analysis=artefact_analysis,
    )
    evidence_phrasing_summary = _evidence_phrasing_guidance(
        artefact_analysis=artefact_analysis,
        content_mode=content_mode,
        context_kind="draft",
    )
    title, prompt = _build_artefact_draft_prompt(
        profile=profile,
        job=job,
        artefact_summary=artefact_summary,
        draft_kind=draft_kind,
        content_mode=content_mode,
        extracted_text=extracted_text,
        tailoring_guidance=tailoring_guidance,
        prior_suggestion=prior_suggestion,
        artefact_analysis=artefact_analysis,
        requirement_strategy_summary=requirement_strategy_summary,
        evidence_allocation_summary=evidence_allocation_summary,
        section_emphasis_summary=section_emphasis_summary,
        evidence_phrasing_summary=evidence_phrasing_summary,
        submission_pack_coordination_summary=submission_pack_coordination_summary,
        generation_brief_summary=generation_brief_summary,
        competency_evidence_summary=competency_evidence_summary,
    )
    body = _execute_prompt(
        setting,
        prompt,
        document=document_payload,
        action=draft_kind,
        content_mode=content_mode,
        job_uuid=job.uuid,
        artefact_uuid=artefact.uuid,
    )
    output = AiOutput(
        owner_user_id=user.id,
        job_id=job.id,
        artefact_id=artefact.id,
        output_type="draft",
        title=title,
        body=body,
        provider=setting.provider,
        model_name=setting.model_name,
        status="active",
        source_context={
            "surface": "job_workspace",
            "job_uuid": job.uuid,
            "artefact_uuid": artefact.uuid,
            "prompt_contract": "artefact_draft_v1",
            "draft_kind": draft_kind,
            "content_mode": content_mode,
            "used_extracted_text": bool(extracted_text),
            "provider_document_mime_type": document_payload["mime_type"] if document_payload is not None else None,
            "metadata_quality": artefact_summary.metadata_quality,
            "tailoring_guidance_output_id": tailoring_guidance.id if tailoring_guidance is not None else None,
            "artefact_suggestion_output_id": prior_suggestion.id if prior_suggestion is not None else None,
            "inferred_requirement_summary": requirement_info["summary_text"],
            "required_artefact_types": requirement_info["required"],
            "optional_artefact_types": requirement_info["optional"],
            "generation_brief": generation_brief,
            "selected_competency_evidence_uuids": selected_evidence_uuids,
            "selected_competency_evidence_refs": competency_evidence_refs,
            "competency_evidence_contract": "competency_evidence_generation_context_v1",
        },
    )
    db.add(output)
    db.flush()
    _create_competency_evidence_links(
        db,
        user,
        output,
        selected_evidence,
        latest_shaping,
        draft_kind=draft_kind,
    )
    return output
