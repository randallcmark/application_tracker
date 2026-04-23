from io import BytesIO
from urllib.error import HTTPError, URLError

from app.db.models.job import Job
from app.db.models.ai_provider_setting import AiProviderSetting
from app.db.models.user_profile import UserProfile
from app.services.ai import _build_job_prompt, _http_error_message, _url_error_message


def _setting(provider: str, *, base_url: str | None = None) -> AiProviderSetting:
    return AiProviderSetting(provider=provider, base_url=base_url)


def _http_error(code: int, body: str, *, reason: str = "error") -> HTTPError:
    return HTTPError(
        url="https://example.test",
        code=code,
        msg=reason,
        hdrs=None,
        fp=BytesIO(body.encode("utf-8")),
    )


def test_http_error_message_maps_openai_quota_errors() -> None:
    setting = _setting("openai")
    exc = _http_error(
        429,
        '{"error":{"message":"You exceeded your current quota, please check your plan and billing details.","type":"insufficient_quota","code":"insufficient_quota"}}',
        reason="Too Many Requests",
    )

    message = _http_error_message(setting, exc)

    assert "OpenAI accepted the key" in message
    assert "no available API quota" in message


def test_http_error_message_maps_gemini_model_not_found() -> None:
    setting = _setting("gemini")
    exc = _http_error(
        404,
        '{"error":{"code":404,"message":"models/gemini-missing is not found for API version v1beta, or is not supported for generateContent.","status":"NOT_FOUND"}}',
        reason="Not Found",
    )

    message = _http_error_message(setting, exc)

    assert "Google Gemini could not find that model" in message
    assert "model name in Settings" in message


def test_http_error_message_maps_endpoint_not_found() -> None:
    setting = _setting("gemini", base_url="https://generativelanguage.googleapis.com/v1beta/models")
    exc = _http_error(404, "Not Found", reason="Not Found")

    message = _http_error_message(setting, exc)

    assert "endpoint was not found" in message
    assert "Base URL in Settings" in message


def test_http_error_message_maps_auth_errors() -> None:
    setting = _setting("gemini")
    exc = _http_error(401, '{"error":{"message":"Request had invalid authentication credentials."}}', reason="Unauthorized")

    message = _http_error_message(setting, exc)

    assert "rejected the API key" in message


def test_url_error_message_maps_tls_certificate_failures() -> None:
    setting = _setting("openai")
    exc = URLError("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")

    message = _url_error_message(setting, exc)

    assert "TLS certificate validation failed" in message


def test_url_error_message_maps_generic_connectivity_failures() -> None:
    setting = _setting("openai_compatible")
    exc = URLError("Connection refused")

    message = _url_error_message(setting, exc)

    assert "Could not reach OpenAI-compatible provider" in message
    assert "Base URL in Settings" in message


def test_build_job_prompt_uses_focus_specific_recommendation_instruction() -> None:
    profile = UserProfile(target_roles="Technical Program Manager", target_locations="Remote UK")
    job = Job(
        title="Staff TPM",
        company="Example Co",
        status="applied",
        location="Remote",
        description_raw="Lead cross-functional delivery.",
    )

    title, prompt = _build_job_prompt(
        "recommendation",
        profile=profile,
        job=job,
        surface="focus",
    )

    assert title == "AI next-step recommendation"
    assert "This recommendation is for the Focus surface" in prompt
    assert "Recommend exactly one concrete next action" in prompt
    assert "Why this now" in prompt
    assert "Do not suggest status changes or multiple parallel tasks" in prompt
    assert "Target roles: Technical Program Manager" in prompt
    assert "Title: Staff TPM" in prompt


def test_build_job_prompt_keeps_default_recommendation_instruction_for_non_focus_surfaces() -> None:
    job = Job(title="Generalist role", status="saved")

    _, prompt = _build_job_prompt(
        "recommendation",
        profile=None,
        job=job,
    )

    assert "This recommendation is for the Focus surface" not in prompt
    assert "Why now" in prompt
    assert "No user profile is configured." in prompt
