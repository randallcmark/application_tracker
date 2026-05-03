from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.auth.users import create_local_user
from app.db.models.ai_output import AiOutput
from app.db.models.ai_provider_setting import AiProviderSetting
from app.db.models.artefact import Artefact
from app.db.models.communication import Communication
from app.db.models.interview_event import InterviewEvent
from app.db.models.job import Job
from app.db.models.user_profile import UserProfile
from app.main import app
from tests.test_local_auth_routes import build_client


def login(client, email: str, password: str = "password") -> None:
    response = client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200


def test_focus_requires_login(tmp_path: Path, monkeypatch) -> None:
    client, _ = build_client(tmp_path, monkeypatch)
    try:
        response = client.get("/focus")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_focus_empty_state_prompts_for_profile(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/focus")

        assert response.status_code == 200
        assert 'data-shell-hero="shared"' not in response.text
        assert "Complete your search profile" in response.text
        assert "No follow-ups due — all clear." in response.text
        assert "No stale jobs — everything is moving." in response.text
        assert "No interviews scheduled." in response.text
        assert "No new saved or interested jobs." in response.text
        assert "Need next action" in response.text
        assert 'id="at-recents-panel"' in response.text
        assert 'class="aside-nav-list recents-list"' in response.text
        assert "sessionStorage.getItem('at-recents')" in response.text
        assert 'href="/board"' in response.text
    finally:
        app.dependency_overrides.clear()


def test_focus_shows_owner_scoped_attention_items(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    now = datetime.now(UTC)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            other = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            db.add(
                UserProfile(
                    owner_user_id=user.id,
                    target_roles="Engineering Manager",
                )
            )
            stale_job = Job(
                owner_user_id=user.id,
                title="Stale applied role",
                company="Example Co",
                status="applied",
                updated_at=now - timedelta(days=10),
            )
            recent_job = Job(
                owner_user_id=user.id,
                title="Recent prospect",
                company="Prospect Co",
                status="saved",
            )
            archived_job = Job(
                owner_user_id=user.id,
                title="Archived follow-up role",
                status="archived",
            )
            other_job = Job(
                owner_user_id=other.id,
                title="Other user role",
                status="applied",
                updated_at=now - timedelta(days=10),
            )
            db.add_all([stale_job, recent_job, archived_job, other_job])
            db.flush()
            db.add_all(
                [
                    Artefact(
                        owner_user_id=user.id,
                        job_id=stale_job.id,
                        kind="resume",
                        purpose="Refresh before reuse",
                        filename="resume-v1.pdf",
                        storage_key="jobs/stale/artefacts/resume-v1.pdf",
                        follow_up_at=now - timedelta(days=1),
                    ),
                    Artefact(
                        owner_user_id=user.id,
                        job_id=recent_job.id,
                        kind="cover_letter",
                        filename="future-cover-letter.pdf",
                        storage_key="jobs/recent/artefacts/future-cover-letter.pdf",
                        follow_up_at=now + timedelta(days=1),
                    ),
                    Artefact(
                        owner_user_id=other.id,
                        job_id=other_job.id,
                        kind="resume",
                        filename="other-user-resume.pdf",
                        storage_key="jobs/other/artefacts/other-user-resume.pdf",
                        follow_up_at=now - timedelta(days=1),
                    ),
                    Communication(
                        job_id=stale_job.id,
                        owner_user_id=user.id,
                        event_type="note",
                        subject="Chase recruiter",
                        follow_up_at=now - timedelta(hours=1),
                    ),
                    Communication(
                        job_id=archived_job.id,
                        owner_user_id=user.id,
                        event_type="note",
                        subject="Hidden archived follow-up",
                        follow_up_at=now - timedelta(hours=1),
                    ),
                    InterviewEvent(
                        job_id=stale_job.id,
                        owner_user_id=user.id,
                        stage="technical",
                        scheduled_at=now + timedelta(days=2),
                        location="Video",
                    ),
                ]
            )
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/focus")

        assert response.status_code == 200
        assert "Complete your search profile" not in response.text
        assert "Chase recruiter" in response.text
        assert "resume-v1.pdf" in response.text
        assert "Refresh before reuse" in response.text
        assert "Stale applied role" in response.text
        assert "Recent prospect" in response.text
        assert "technical" in response.text
        assert "Video" in response.text
        assert "Need next action" in response.text
        assert "Other user role" not in response.text
        assert "other-user-resume.pdf" not in response.text
        assert "future-cover-letter.pdf" not in response.text
        assert "Hidden archived follow-up" not in response.text
        assert "Archived follow-up role" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_focus_goal_chip_formats_salary_as_rounded_thousands(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            db.add(
                UserProfile(
                    owner_user_id=user.id,
                    target_roles="Engineering Manager",
                    target_locations="Remote",
                    salary_min=Decimal("100000.00"),
                    salary_max=Decimal("125000.00"),
                    salary_currency="GBP",
                )
            )
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/focus")

        assert response.status_code == 200
        assert "GBP 100K" in response.text
        assert "GBP 125K" in response.text
        assert "100000.00" not in response.text
        assert "125000.00" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_focus_renders_visible_ai_nudge_for_priority_job(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    now = datetime.now(UTC)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(
                owner_user_id=user.id,
                title="Priority role",
                status="applied",
                updated_at=now - timedelta(days=8),
            )
            db.add(job)
            db.flush()
            db.add(
                AiOutput(
                    owner_user_id=user.id,
                    job_id=job.id,
                    output_type="recommendation",
                    title="AI next-step recommendation",
                    body="### Next step\n* **Email the recruiter today**",
                    provider="gemini",
                    model_name="gemini-flash-latest",
                    status="active",
                )
            )
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/focus")

        assert response.status_code == 200
        assert "AI nudge" in response.text
        assert "Priority role" in response.text
        assert "gemini-flash-latest" not in response.text
        assert "Email the recruiter today" in response.text
        assert "<strong>Email the recruiter today</strong>" in response.text
        assert 'action="/focus/ai-nudge"' in response.text
    finally:
        app.dependency_overrides.clear()


def test_focus_ai_nudge_requires_enabled_provider(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="AI focus target", status="saved")
            db.add(job)
            db.commit()
            job_uuid = job.uuid
        login(client, "jobseeker@example.com")

        response = client.post(
            "/focus/ai-nudge",
            data={"job_uuid": job_uuid},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert "ai_error=" in response.headers["location"]

        detail_response = client.get(response.headers["location"])
        assert "Enable an AI provider in Settings before generating AI output" in detail_response.text
    finally:
        app.dependency_overrides.clear()


def test_focus_ai_nudge_creates_visible_recommendation(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="AI focus success", status="saved")
            db.add(job)
            db.add(
                AiProviderSetting(
                    owner_user_id=user.id,
                    provider="gemini",
                    model_name="gemini-flash-latest",
                    api_key_encrypted="sealed",
                    api_key_hint="key...1234",
                    is_enabled=True,
                )
            )
            db.commit()
            job_uuid = job.uuid

        def fake_generate_job_ai_output(db, user, job, *, output_type, profile=None, surface="default"):
            output = AiOutput(
                owner_user_id=user.id,
                job_id=job.id,
                output_type=output_type,
                title="AI next-step recommendation",
                body="### Next step\n* **Prepare a tailored CV**",
                provider="gemini",
                model_name="gemini-flash-latest",
                status="active",
            )
            db.add(output)
            db.flush()
            assert surface == "focus"
            return output

        monkeypatch.setattr("app.api.routes.focus.generate_job_ai_output", fake_generate_job_ai_output)

        login(client, "jobseeker@example.com")

        response = client.post(
            "/focus/ai-nudge",
            data={"job_uuid": job_uuid},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert "ai_status=Next%20step%20suggestion%20generated%20for%20AI%20focus%20success" in response.headers["location"]

        detail_response = client.get(response.headers["location"])
        assert detail_response.status_code == 200
        assert "Next step suggestion generated for AI focus success" in detail_response.text

        with session_local() as db:
            output = db.scalar(select(AiOutput))
            assert output is not None
            assert output.output_type == "recommendation"
            assert "Prepare a tailored CV" in output.body
            assert output.job.uuid == job_uuid
    finally:
        app.dependency_overrides.clear()
