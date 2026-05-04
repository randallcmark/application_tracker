import json
from io import BytesIO
from pathlib import Path
import sqlite3
from urllib.error import URLError
from zipfile import ZipFile

from sqlalchemy import select

from app.auth.users import create_local_user
from app.core.config import settings
from app.db.models.ai_provider_setting import AiProviderSetting
from app.db.models.api_token import ApiToken
from app.db.models.job import Job
from app.db.models.user import User
from app.main import app
from tests.test_local_auth_routes import build_client


class _JsonResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_login_page_renders_form(tmp_path: Path, monkeypatch) -> None:
    client, _ = build_client(tmp_path, monkeypatch)
    try:
        response = client.get("/login")

        assert response.status_code == 200
        assert '<form method="post" action="/login">' in response.text
        assert 'name="email"' in response.text
        assert 'name="password"' in response.text
    finally:
        app.dependency_overrides.clear()


def test_root_redirects_to_setup_when_no_users_exist(tmp_path: Path, monkeypatch) -> None:
    client, _ = build_client(tmp_path, monkeypatch)
    try:
        response = client.get("/", follow_redirects=False)

        assert response.status_code == 307
        assert response.headers["location"] == "/setup"
    finally:
        app.dependency_overrides.clear()


def test_setup_form_creates_first_admin_and_logs_in(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        form_response = client.get("/setup")

        assert form_response.status_code == 200
        assert '<form method="post" action="/setup">' in form_response.text
        assert "Create admin" in form_response.text

        response = client.post(
            "/setup",
            data={
                "email": "admin@example.com",
                "display_name": "Admin User",
                "password": "correct horse battery staple",
                "confirm_password": "correct horse battery staple",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/focus"
        assert settings.session_cookie_name in client.cookies

        with session_local() as db:
            user = db.scalar(select(User).where(User.email == "admin@example.com"))

            assert user is not None
            assert user.display_name == "Admin User"
            assert user.is_admin is True
            assert user.is_active is True
    finally:
        app.dependency_overrides.clear()


def test_setup_form_rejects_mismatched_passwords(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        response = client.post(
            "/setup",
            data={
                "email": "admin@example.com",
                "password": "correct horse battery staple",
                "confirm_password": "different horse battery staple",
            },
        )

        assert response.status_code == 200
        assert "Passwords do not match" in response.text

        with session_local() as db:
            assert db.scalar(select(User)) is None
    finally:
        app.dependency_overrides.clear()


def test_setup_redirects_after_user_exists(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        response = client.get("/setup", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/login"
    finally:
        app.dependency_overrides.clear()


def test_login_form_sets_cookie_and_redirects_to_focus(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        response = client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/focus"
        assert settings.session_cookie_name in client.cookies
    finally:
        app.dependency_overrides.clear()


def test_login_form_shows_error_for_bad_credentials(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        response = client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "wrong"},
        )

        assert response.status_code == 200
        assert "Invalid email or password" in response.text
        assert settings.session_cookie_name not in client.cookies
    finally:
        app.dependency_overrides.clear()


def test_logout_form_clears_cookie_and_redirects_to_login(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        login_response = client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )
        assert login_response.status_code == 303

        logout_response = client.post("/logout", follow_redirects=False)

        assert logout_response.status_code == 303
        assert logout_response.headers["location"] == "/login"
        assert settings.session_cookie_name not in client.cookies
    finally:
        app.dependency_overrides.clear()


def test_settings_requires_login(tmp_path: Path, monkeypatch) -> None:
    client, _ = build_client(tmp_path, monkeypatch)
    try:
        response = client.get("/settings")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_settings_shows_ai_readiness_placeholders(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.get("/settings")

        assert response.status_code == 200
        assert "Appearance" in response.text
        assert 'id="at-theme-swatches"' in response.text
        assert 'data-theme="ocean"' in response.text
        assert 'data-theme="custom"' in response.text
        assert 'id="at-theme-custom-row"' in response.text
        assert "localStorage.setItem('at-theme'" in response.text
        assert "AI readiness" in response.text
        assert "OpenAI" in response.text
        assert "Google Gemini (AI Studio)" in response.text
        assert "Anthropic" in response.text
        assert "OpenAI-compatible local endpoint" in response.text
        assert "disabled by default" in response.text
        assert "API key setup help" in response.text
        assert "Consumer chat subscriptions do not configure this app by themselves" in response.text
        assert 'name="api_key"' in response.text
        assert "Leave blank to reuse saved key" in response.text
        assert 'href="/help#ai-setup"' in response.text
        assert 'href="https://help.openai.com/en/articles/9039756-billing-settings-in-chatgpt-vs-platform"' in response.text
        assert 'href="https://platform.openai.com/docs/quickstart/using-the-api"' in response.text
        assert 'href="https://ai.google.dev/gemini-api/docs/api-key"' in response.text
    finally:
        app.dependency_overrides.clear()


def test_settings_updates_ai_provider_placeholder(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            create_local_user(db, email="other@example.com", password="password")
            db.commit()

        client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.post(
            "/settings/ai-provider",
            data={
                "provider": "openai_compatible",
                "label": "Local endpoint",
                "base_url": "http://localhost:11434/v1",
                "model_name": "local-model",
                "api_key": "local-secret-1234",
                "is_enabled": "true",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/settings#ai"

        with session_local() as db:
            setting = db.scalar(select(AiProviderSetting))

            assert setting is not None
            assert setting.owner.email == "jobseeker@example.com"
            assert setting.provider == "openai_compatible"
            assert setting.label == "Local endpoint"
            assert setting.base_url == "http://localhost:11434/v1"
            assert setting.model_name == "local-model"
            assert setting.api_key_encrypted is not None
            assert setting.api_key_hint == "loca...1234"
            assert setting.is_enabled is True

        settings_response = client.get("/settings")

        assert "local-model" in settings_response.text
        assert "http://localhost:11434/v1" in settings_response.text
        assert "loca...1234" in settings_response.text
        assert "Enabled" in settings_response.text
    finally:
        app.dependency_overrides.clear()


def test_settings_ai_provider_enable_disables_other_enabled_provider(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )

        first = client.post(
            "/settings/ai-provider",
            data={
                "provider": "openai",
                "label": "Personal OpenAI",
                "base_url": "",
                "model_name": "gpt-5",
                "api_key": "sk-openai-1234",
                "is_enabled": "true",
            },
            follow_redirects=False,
        )
        assert first.status_code == 303

        second = client.post(
            "/settings/ai-provider",
            data={
                "provider": "gemini",
                "label": "AI Studio",
                "base_url": "",
                "model_name": "gemini-2.5-flash",
                "api_key": "gemini-secret-1234",
                "is_enabled": "true",
            },
            follow_redirects=False,
        )
        assert second.status_code == 303

        with session_local() as db:
            settings_by_provider = {
                setting.provider: setting for setting in db.scalars(select(AiProviderSetting)).all()
            }
            assert settings_by_provider["openai"].is_enabled is False
            assert settings_by_provider["gemini"].is_enabled is True

        settings_response = client.get("/settings")
        assert settings_response.status_code == 200
        assert "Only one provider is active at a time" in settings_response.text
    finally:
        app.dependency_overrides.clear()


def test_settings_page_handles_provider_rows_with_missing_model_name(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            db.add(
                AiProviderSetting(
                    owner_user_id=user.id,
                    provider="openai",
                    label="OpenAI",
                    model_name=None,
                    base_url=None,
                    api_key_hint="sk-t...1234",
                    is_enabled=True,
                )
            )
            db.commit()

        client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.get("/settings")

        assert response.status_code == 200
        assert "Not set" in response.text
        assert "sk-t...1234" in response.text
    finally:
        app.dependency_overrides.clear()


def test_settings_updates_openai_provider_with_encrypted_api_key(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.post(
            "/settings/ai-provider",
            data={
                "provider": "openai",
                "label": "Personal OpenAI",
                "base_url": "",
                "model_name": "gpt-5",
                "api_key": "sk-test-secret-1234",
                "is_enabled": "true",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/settings#ai"

        with session_local() as db:
            setting = db.scalar(select(AiProviderSetting))

            assert setting is not None
            assert setting.provider == "openai"
            assert setting.api_key_encrypted is not None
            assert "sk-test-secret-1234" not in setting.api_key_encrypted
            assert setting.api_key_hint == "sk-t...1234"

        settings_response = client.get("/settings")

        assert "sk-t...1234" in settings_response.text
        assert "sk-test-secret-1234" not in settings_response.text
    finally:
        app.dependency_overrides.clear()


def test_settings_standard_provider_uses_default_model_and_no_base_url(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.post(
            "/settings/ai-provider",
            data={
                "provider": "anthropic",
                "label": "Claude",
                "base_url": "https://malicious.example/v1",
                "model_name": "",
                "api_key": "anthropic-secret-1234",
                "is_enabled": "true",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303

        with session_local() as db:
            setting = db.scalar(select(AiProviderSetting))
            assert setting is not None
            assert setting.provider == "anthropic"
            assert setting.label == "Claude"
            assert setting.base_url is None
            assert setting.model_name == "claude-sonnet-4-20250514"
            assert setting.is_enabled is True

        settings_response = client.get("/settings")

        assert "claude-sonnet-4-20250514" in settings_response.text
        assert "https://api.anthropic.com/v1" in settings_response.text
        assert "https://malicious.example/v1" not in settings_response.text
    finally:
        app.dependency_overrides.clear()


def test_settings_discovers_provider_models_then_enables_selected_model(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    captured: dict[str, object] = {}

    def _fake_urlopen(req, *args, **kwargs):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        return _JsonResponse(
            {
                "data": [
                    {"id": "claude-haiku-4-20250514", "display_name": "Claude Haiku 4"},
                    {"id": "claude-sonnet-4-20250514", "display_name": "Claude Sonnet 4"},
                ]
            }
        )

    monkeypatch.setattr("app.services.ai.request.urlopen", _fake_urlopen)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )

        discover_response = client.post(
            "/settings/ai-provider/discover",
            data={
                "provider": "anthropic",
                "label": "Claude",
                "api_key": "anthropic-secret-1234",
            },
            follow_redirects=False,
        )

        assert discover_response.status_code == 303
        assert discover_response.headers["location"] == "/settings#ai"
        assert captured["url"] == "https://api.anthropic.com/v1/models?limit=1000"
        headers = {key.lower(): value for key, value in captured["headers"].items()}
        assert headers["x-api-key"] == "anthropic-secret-1234"

        settings_response = client.get("/settings")
        assert "Claude Sonnet 4" in settings_response.text
        assert "claude-sonnet-4-20250514" in settings_response.text
        assert "Enable selected model" in settings_response.text

        enable_response = client.post(
            "/settings/ai-provider/enable",
            data={"provider": "anthropic", "model_name": "claude-haiku-4-20250514"},
            follow_redirects=False,
        )

        assert enable_response.status_code == 303

        with session_local() as db:
            setting = db.scalar(select(AiProviderSetting))
            assert setting is not None
            assert setting.provider == "anthropic"
            assert setting.model_discovery_status == "ready"
            assert setting.discovered_models == [
                {"id": "claude-haiku-4-20250514", "display_name": "Claude Haiku 4"},
                {"id": "claude-sonnet-4-20250514", "display_name": "Claude Sonnet 4"},
            ]
            assert setting.model_name == "claude-haiku-4-20250514"
            assert setting.is_enabled is True
    finally:
        app.dependency_overrides.clear()


def test_settings_custom_provider_discovery_failure_allows_manual_model(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)

    def _fake_urlopen(*args, **kwargs):
        raise URLError("Connection refused")

    monkeypatch.setattr("app.services.ai.request.urlopen", _fake_urlopen)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )

        discover_response = client.post(
            "/settings/ai-provider/discover",
            data={
                "provider": "openai_compatible",
                "label": "Local endpoint",
                "base_url": "http://localhost:11434/v1",
                "api_key": "local-secret-1234",
            },
            follow_redirects=False,
        )

        assert discover_response.status_code == 303

        settings_response = client.get("/settings")
        assert "Model discovery failed for this custom endpoint" in settings_response.text
        assert "Enter model manually" in settings_response.text

        enable_response = client.post(
            "/settings/ai-provider/enable",
            data={"provider": "openai_compatible", "model_name": "llama3.2"},
            follow_redirects=False,
        )

        assert enable_response.status_code == 303

        with session_local() as db:
            setting = db.scalar(select(AiProviderSetting))
            assert setting is not None
            assert setting.provider == "openai_compatible"
            assert setting.model_discovery_status == "failed"
            assert setting.model_discovery_error is not None
            assert setting.model_name == "llama3.2"
            assert setting.is_enabled is True
    finally:
        app.dependency_overrides.clear()


def test_settings_rejects_enabled_provider_without_api_key(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.post(
            "/settings/ai-provider",
            data={
                "provider": "gemini",
                "label": "AI Studio",
                "model_name": "",
                "api_key": "",
                "is_enabled": "true",
            },
            follow_redirects=False,
        )

        assert response.status_code == 400
        assert "Enabled AI provider is missing an API key" in response.text
    finally:
        app.dependency_overrides.clear()


def test_help_page_includes_ai_setup_guidance(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.get("/help")

        assert response.status_code == 200
        assert 'id="ai-setup"' in response.text
        assert "AI generation uses provider API access, not a consumer chat subscription sign-in" in response.text
        assert "ChatGPT and the OpenAI API are separate billing systems" in response.text
        assert "create a Gemini API key in Google AI Studio" in response.text
        assert "provider API keys are stored encrypted at rest" in response.text
        assert 'href="/settings#ai"' in response.text
        assert 'href="https://ai.google.dev/docs/gemini_api_overview/"' in response.text
        assert 'href="https://docs.anthropic.com/en/api/getting-started"' in response.text
    finally:
        app.dependency_overrides.clear()


def test_admin_requires_login(tmp_path: Path, monkeypatch) -> None:
    client, _ = build_client(tmp_path, monkeypatch)
    try:
        response = client.get("/admin")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_admin_rejects_non_admin_user(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.get("/admin")

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_admin_page_shows_system_links_and_counts(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            admin = create_local_user(
                db,
                email="admin@example.com",
                password="password",
                is_admin=True,
            )
            db.flush()
            db.add(Job(owner_user_id=admin.id, title="Tracked role", status="saved"))
            db.add(
                ApiToken(
                    owner_user_id=admin.id,
                    name="Capture",
                    token_hash="hash",
                    scopes="capture:jobs",
                )
            )
            db.commit()

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.get("/admin")

        assert response.status_code == 200
        assert "Admin" in response.text
        assert "Users" in response.text
        assert "Jobs" in response.text
        assert "API tokens" in response.text
        assert "Create Capture Token" in response.text
        assert "Capture" in response.text
        assert "admin@example.com" in response.text
        assert 'href="/api/capture/bookmarklet"' in response.text
        assert 'href="/health"' in response.text
        assert 'href="/admin/backup"' in response.text
        assert "Restore dry-run" in response.text
        assert 'action="/admin/restore/validate"' in response.text
        assert "App version" in response.text
    finally:
        app.dependency_overrides.clear()


def test_admin_creates_capture_token_and_shows_secret_once(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="admin@example.com", password="password", is_admin=True)
            db.commit()

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.post(
            "/admin/api-tokens",
            data={"name": "Admin browser capture", "scope": "capture:jobs"},
        )

        assert response.status_code == 200
        assert "New admin token" in response.text
        assert "ats_" in response.text
        assert "Admin browser capture" in response.text
        assert "capture:jobs" in response.text

        with session_local() as db:
            api_token = db.scalar(select(ApiToken).where(ApiToken.name == "Admin browser capture"))

            assert api_token is not None
            assert api_token.owner.email == "admin@example.com"
    finally:
        app.dependency_overrides.clear()


def test_admin_revokes_any_user_token(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            admin = create_local_user(db, email="admin@example.com", password="password", is_admin=True)
            owner = create_local_user(db, email="owner@example.com", password="password")
            db.flush()
            api_token = ApiToken(
                owner_user_id=owner.id,
                name="Owner token",
                token_hash="owner-hash",
                scopes="capture:jobs",
            )
            db.add(api_token)
            db.commit()
            token_uuid = api_token.uuid
            assert admin.is_admin is True

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.post(f"/admin/api-tokens/{token_uuid}/revoke", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/admin"

        with session_local() as db:
            api_token = db.scalar(select(ApiToken).where(ApiToken.uuid == token_uuid))

            assert api_token is not None
            assert api_token.revoked_at is not None
    finally:
        app.dependency_overrides.clear()


def test_admin_backup_download_contains_database_and_artefacts(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    database_path = tmp_path / "app.db"
    artefact_root = tmp_path / "artefacts"
    artefact_path = artefact_root / "jobs" / "job-uuid" / "artefacts" / "resume.txt"
    artefact_path.parent.mkdir(parents=True)
    artefact_path.write_text("resume bytes")
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{database_path}")
    monkeypatch.setattr(settings, "local_storage_path", str(artefact_root))
    try:
        with session_local() as db:
            admin = create_local_user(db, email="admin@example.com", password="password", is_admin=True)
            db.add(Job(owner_user_id=admin.id, title="Backup role", status="saved"))
            db.commit()

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.get("/admin/backup")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert "application-tracker-backup-" in response.headers["content-disposition"]

        with ZipFile(BytesIO(response.content)) as archive:
            names = set(archive.namelist())

            assert "MANIFEST.txt" in names
            assert "database/app.db" in names
            assert "artefacts/jobs/job-uuid/artefacts/resume.txt" in names
            assert archive.read("artefacts/jobs/job-uuid/artefacts/resume.txt") == b"resume bytes"
            assert b"App version:" in archive.read("MANIFEST.txt")
    finally:
        app.dependency_overrides.clear()


def test_admin_restore_validate_reports_ready_archive(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    database_path = tmp_path / "app.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{database_path}")
    try:
        with session_local() as db:
            create_local_user(db, email="admin@example.com", password="password", is_admin=True)
            db.commit()

        sqlite_connection = sqlite3.connect(database_path)
        try:
            sqlite_connection.execute("create table example (id integer primary key)")
            sqlite_connection.commit()
        finally:
            sqlite_connection.close()

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "password"},
            follow_redirects=False,
        )

        backup_response = client.get("/admin/backup")
        assert backup_response.status_code == 200

        response = client.post(
            "/admin/restore/validate",
            files={"backup_file": ("application-tracker-backup.zip", backup_response.content, "application/zip")},
        )

        assert response.status_code == 200
        assert "Restore Dry-Run Result" in response.text
        assert "Ready for restore review" in response.text
        assert "application-tracker-backup.zip" in response.text
    finally:
        app.dependency_overrides.clear()


def test_admin_restore_validate_reports_invalid_archive(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="admin@example.com", password="password", is_admin=True)
            db.commit()

        client.post(
            "/login",
            data={"email": "admin@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.post(
            "/admin/restore/validate",
            files={"backup_file": ("not-a-backup.zip", b"plain text", "application/zip")},
        )

        assert response.status_code == 200
        assert "Restore validation failed" in response.text
        assert "Archive is not a valid ZIP file." in response.text
    finally:
        app.dependency_overrides.clear()


def test_settings_creates_capture_token_and_shows_secret_once(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        login_response = client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )
        assert login_response.status_code == 303

        response = client.post(
            "/settings/api-tokens",
            data={"name": "Browser bookmarklet", "scope": "capture:jobs"},
        )

        assert response.status_code == 200
        assert "New token" in response.text
        assert "ats_" in response.text
        assert "Browser bookmarklet" in response.text
        assert "capture:jobs" in response.text
        assert "Open Capture setup" in response.text

        settings_response = client.get("/settings")

        assert settings_response.status_code == 200
        assert "Browser bookmarklet" in settings_response.text
        assert "capture:jobs" in settings_response.text
        assert "New token" not in settings_response.text
    finally:
        app.dependency_overrides.clear()


def test_settings_revokes_owned_token(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        client.post(
            "/login",
            data={"email": "jobseeker@example.com", "password": "password"},
            follow_redirects=False,
        )
        create_response = client.post(
            "/settings/api-tokens",
            data={"name": "Browser bookmarklet", "scope": "capture:jobs"},
        )
        assert create_response.status_code == 200

        with session_local() as db:
            api_token = db.query(ApiToken).one()
            token_uuid = api_token.uuid

        revoke_response = client.post(
            f"/settings/api-tokens/{token_uuid}/revoke",
            follow_redirects=False,
        )

        assert revoke_response.status_code == 303
        assert revoke_response.headers["location"] == "/settings"

        with session_local() as db:
            api_token = db.query(ApiToken).one()

            assert api_token.revoked_at is not None
    finally:
        app.dependency_overrides.clear()


def test_settings_revoke_does_not_cross_user_boundaries(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            owner = create_local_user(db, email="owner@example.com", password="password")
            create_local_user(db, email="other@example.com", password="password")
            db.flush()
            api_token = ApiToken(
                owner_user_id=owner.id,
                name="Owner token",
                token_hash="hash",
                scopes="capture:jobs",
            )
            db.add(api_token)
            db.commit()
            token_uuid = api_token.uuid

        client.post(
            "/login",
            data={"email": "other@example.com", "password": "password"},
            follow_redirects=False,
        )

        response = client.post(f"/settings/api-tokens/{token_uuid}/revoke")

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
