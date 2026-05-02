from pathlib import Path

from sqlalchemy import select

from app.auth.users import create_local_user
from app.db.models.ai_output import AiOutput
from app.db.models.email_intake import EmailIntake
from app.db.models.job import Job
from app.main import app
from tests.test_capture_routes import create_capture_token
from tests.test_local_auth_routes import build_client


def login(client, email: str, password: str = "password") -> None:
    response = client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200


def test_inbox_requires_login(tmp_path: Path, monkeypatch) -> None:
    client, _ = build_client(tmp_path, monkeypatch)
    try:
        response = client.get("/inbox")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_inbox_empty_state(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/inbox")

        assert response.status_code == 200
        assert "<h1>Inbox</h1>" in response.text
        assert "Inbox is clear" in response.text
        assert 'href="/focus"' in response.text
        assert 'data-has-chip="false"' in response.text
        assert 'data-shell-chip="context"' not in response.text
        assert ">Board</a>" in response.text
    finally:
        app.dependency_overrides.clear()


def test_capture_job_lands_in_inbox_and_is_hidden_from_board(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        token = create_capture_token(client, session_local)

        response = client.post(
            "/api/capture/jobs",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "source_url": "https://jobs.example.com/inbox-role",
                "title": "Inbox role",
                "company": "Capture Co",
                "raw_extraction_metadata": {"extractor": "firefox_extension"},
            },
        )

        assert response.status_code == 201
        inbox_response = client.get("/inbox")
        board_response = client.get("/board?workflow=prospects")

        assert "Inbox role" in inbox_response.text
        assert '<div class="inbox-card-main">' in inbox_response.text
        assert '<div class="inbox-card-actions">' in inbox_response.text
        assert '<div class="queue-count"><strong>1</strong><span>queued</span></div>' in inbox_response.text
        assert "jobs.example.com" in inbox_response.text
        assert "medium confidence" in inbox_response.text
        assert "Open source" in inbox_response.text
        assert "Review before effort" not in inbox_response.text
        assert "Triage" not in inbox_response.text
        assert inbox_response.text.count('href="/inbox/email/new"') == 1
        assert 'class="source-url"' not in inbox_response.text
        assert "Inbox role" not in board_response.text

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == response.json()["uuid"]))

            assert job is not None
            assert job.intake_source == "browser_capture"
            assert job.intake_state == "needs_review"
    finally:
        app.dependency_overrides.clear()


def test_accept_inbox_job_moves_to_interested(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        token = create_capture_token(client, session_local)
        captured = client.post(
            "/api/capture/jobs",
            headers={"Authorization": f"Bearer {token}"},
            json={"source_url": "https://jobs.example.com/accept", "title": "Accept role"},
        )
        job_uuid = captured.json()["uuid"]

        response = client.post(f"/inbox/{job_uuid}/accept", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/inbox"

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))

            assert job is not None
            assert job.status == "interested"
            assert job.intake_state == "accepted"
            assert job.communications[-1].subject == "Inbox accepted"
    finally:
        app.dependency_overrides.clear()


def test_dismiss_inbox_job_archives_and_hides_it(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        token = create_capture_token(client, session_local)
        captured = client.post(
            "/api/capture/jobs",
            headers={"Authorization": f"Bearer {token}"},
            json={"source_url": "https://jobs.example.com/dismiss", "title": "Dismiss role"},
        )
        job_uuid = captured.json()["uuid"]

        response = client.post(f"/inbox/{job_uuid}/dismiss", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/inbox"
        assert "Dismiss role" not in client.get("/inbox").text

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))

            assert job is not None
            assert job.status == "archived"
            assert job.archived_at is not None
            assert job.intake_state == "dismissed"
            assert job.communications[-1].subject == "Inbox dismissed"
    finally:
        app.dependency_overrides.clear()


def test_inbox_hides_other_users_jobs(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            other = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            db.add_all(
                [
                    Job(
                        owner_user_id=user.id,
                        title="Visible inbox role",
                        status="saved",
                        intake_source="api_capture",
                        intake_confidence="medium",
                        intake_state="needs_review",
                    ),
                    Job(
                        owner_user_id=other.id,
                        title="Other inbox role",
                        status="saved",
                        intake_source="api_capture",
                        intake_confidence="medium",
                        intake_state="needs_review",
                    ),
                ]
            )
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/inbox")

        assert response.status_code == 200
        assert "Visible inbox role" in response.text
        assert "Other inbox role" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_email_capture_form_requires_login(tmp_path: Path, monkeypatch) -> None:
    client, _ = build_client(tmp_path, monkeypatch)
    try:
        response = client.get("/inbox/email/new")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_email_capture_form_renders(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/inbox/email/new")

        assert response.status_code == 200
        assert '<form method="post" action="/inbox/email">' in response.text
        assert 'name="subject"' in response.text
        assert 'name="body_text"' in response.text
    finally:
        app.dependency_overrides.clear()


def test_email_capture_api_requires_login(tmp_path: Path, monkeypatch) -> None:
    client, _ = build_client(tmp_path, monkeypatch)
    try:
        response = client.post(
            "/api/inbox/email-captures",
            json={"subject": "Role", "body_text": "https://jobs.example.com/role"},
        )

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_email_capture_api_creates_inbox_job_with_provenance(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.post(
            "/api/inbox/email-captures",
            json={
                "subject": "Senior Platform Role",
                "sender": "alerts@example.com",
                "received_at": "2026-04-18T09:30:00Z",
                "body_text": (
                    "View role https://jobs.example.com/platform "
                    "unsubscribe https://jobs.example.com/unsubscribe"
                ),
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["created"] is True
        assert body["intake_state"] == "needs_review"
        assert body["candidate_count"] == 1
        assert body["created_count"] == 1
        assert body["job_uuids"] == [body["job_uuid"]]

        with session_local() as db:
            email_intake = db.scalar(
                select(EmailIntake).where(EmailIntake.uuid == body["email_intake_uuid"])
            )
            job = db.scalar(select(Job).where(Job.uuid == body["job_uuid"]))

            assert email_intake is not None
            assert email_intake.subject == "Senior Platform Role"
            assert email_intake.sender == "alerts@example.com"
            assert email_intake.source_provider == "manual_paste"
            assert job is not None
            assert job.email_intake_id == email_intake.id
            assert job.title == "Senior Platform Role"
            assert job.source_url == "https://jobs.example.com/platform"
            assert job.apply_url == "https://jobs.example.com/platform"
            assert job.intake_source == "email_capture"
            assert job.intake_confidence == "unknown"
            assert job.intake_state == "needs_review"
            assert job.structured_data["email_capture"]["all_urls"] == [
                "https://jobs.example.com/platform",
                "https://jobs.example.com/unsubscribe",
            ]
            assert (
                job.structured_data["email_capture"]["selected_source_url"]
                == "https://jobs.example.com/platform"
            )
            assert job.structured_data["email_capture"]["candidate_index"] == 1
            assert job.structured_data["email_capture"]["candidate_count"] == 1
    finally:
        app.dependency_overrides.clear()


def test_email_capture_api_creates_multiple_candidates_for_job_board_alert(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.post(
            "/api/inbox/email-captures",
            json={
                "subject": "Platform jobs alert",
                "sender": "alerts@example.com",
                "body_text": (
                    "Role one https://jobs.example.com/platform-one\n"
                    "Role two https://jobs.example.com/platform-two\n"
                    "Manage alerts https://jobs.example.com/preferences"
                ),
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["created"] is True
        assert body["candidate_count"] == 2
        assert body["created_count"] == 2
        assert len(body["job_uuids"]) == 2
        assert body["job_uuid"] == body["job_uuids"][0]

        inbox_response = client.get("/inbox")
        assert "Platform jobs alert (jobs.example.com)" in inbox_response.text
        assert "platform-one" in inbox_response.text
        assert "platform-two" in inbox_response.text
        assert "Platform jobs alert" not in client.get("/board?workflow=prospects").text

        with session_local() as db:
            email_intake = db.scalar(
                select(EmailIntake).where(EmailIntake.uuid == body["email_intake_uuid"])
            )
            jobs = list(
                db.scalars(select(Job).where(Job.uuid.in_(body["job_uuids"])).order_by(Job.id))
            )

            assert email_intake is not None
            assert len(jobs) == 2
            assert {job.source_url for job in jobs} == {
                "https://jobs.example.com/platform-one",
                "https://jobs.example.com/platform-two",
            }
            assert all(job.email_intake_id == email_intake.id for job in jobs)
            assert all(job.intake_state == "needs_review" for job in jobs)
            assert [job.structured_data["email_capture"]["candidate_index"] for job in jobs] == [1, 2]
            assert all(job.structured_data["email_capture"]["candidate_count"] == 2 for job in jobs)
    finally:
        app.dependency_overrides.clear()


def test_email_capture_api_links_existing_candidate_and_creates_new_candidate(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            existing_job = Job(
                owner_user_id=user.id,
                title="Existing alert role",
                status="interested",
                source_url="https://jobs.example.com/existing-alert",
                intake_state="accepted",
            )
            db.add(existing_job)
            db.commit()
            existing_uuid = existing_job.uuid
        login(client, "jobseeker@example.com")

        response = client.post(
            "/api/inbox/email-captures",
            json={
                "subject": "Mixed jobs alert",
                "body_text": (
                    "Existing https://jobs.example.com/existing-alert\n"
                    "New https://jobs.example.com/new-alert"
                ),
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["created"] is True
        assert body["candidate_count"] == 2
        assert body["created_count"] == 1
        assert existing_uuid in body["job_uuids"]

        with session_local() as db:
            jobs = db.scalars(select(Job).order_by(Job.id)).all()
            existing = db.scalar(select(Job).where(Job.uuid == existing_uuid))
            created = db.scalar(select(Job).where(Job.source_url == "https://jobs.example.com/new-alert"))

            assert len(jobs) == 2
            assert existing is not None
            assert existing.intake_state == "accepted"
            assert existing.communications[-1].subject == "Email captured"
            assert created is not None
            assert created.intake_state == "needs_review"
            assert created.title == "Mixed jobs alert (jobs.example.com)"
    finally:
        app.dependency_overrides.clear()


def test_email_capture_api_extracts_linkedin_direct_role_candidates_from_text(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.post(
            "/api/inbox/email-captures",
            json={
                "subject": "Hiring trends for Staff Technical Program Manager roles",
                "sender": "linkedin@example.com",
                "body_text": (
                    "Hiring trends for Staff Technical Program Manager roles\n"
                    "20% drop in the United Kingdom job market in the past week, but new jobs are still available.\n"
                    "View job openings\n"
                    "People with similar roles applied to these jobs\n"
                    "Wise\n"
                    "Technical Project Director, Global Product, Servicing\n"
                    "Wise · London\n"
                    "View\n"
                    "Mapbox\n"
                    "Senior Leader, Technical Program Management\n"
                    "Mapbox · London (Remote)\n"
                    "View\n"
                    "Companies with the most job openings in your role\n"
                    "Deliveroo\n"
                    "Deliveroo\n"
                    "1 job opening\n"
                    "View jobs\n"
                    "Personio\n"
                    "Personio\n"
                    "1 job opening\n"
                    "View jobs\n"
                    "Improve your recommendations\n"
                    "Update profile"
                ),
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["candidate_count"] == 2
        assert body["created_count"] == 2

        with session_local() as db:
            jobs = list(
                db.scalars(select(Job).where(Job.uuid.in_(body["job_uuids"])).order_by(Job.id))
            )

            assert [job.title for job in jobs] == [
                "Technical Project Director, Global Product, Servicing",
                "Senior Leader, Technical Program Management",
            ]
            assert [job.company for job in jobs] == ["Wise", "Mapbox"]
            assert [job.location for job in jobs] == ["London", "London (Remote)"]
            assert all(job.source_url is None for job in jobs)
            assert all("Deliveroo" not in (job.description_raw or "") for job in jobs)
            assert all("Update profile" not in (job.description_raw or "") for job in jobs)
            assert jobs[0].structured_data["email_capture"]["extraction"]["method"] == (
                "deterministic_linkedin_direct_roles"
            )
    finally:
        app.dependency_overrides.clear()


def test_email_capture_api_extracts_indeed_saved_alert_candidates_from_text(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.post(
            "/api/inbox/email-captures",
            json={
                "subject": "12 new technical program manager jobs in Edinburgh",
                "sender": "jobalerts-noreply@indeed.com",
                "body_text": (
                    "12 new technical program manager jobs in Edinburgh, City of Edinburgh\n"
                    "These job ads match your saved job alert ¹\n"
                    "Financial Transformation Manager - Insurance (Finance, Data & Systems)\n"
                    "KPMG\t3.9\t3.9/5 rating\n"
                    "Edinburgh\n"
                    "Financial Transformation Manager - Insurance (Finance, Data & Systems) (107902). "
                    "As an insurance-focused Solution Architect, you'll lead and deliver complex…\n"
                    "Just posted\n"
                    "Engineering Manager\n"
                    "MRD Recruitment\n"
                    "Falkirk\n"
                    "£85,000 a year\n"
                    "Easily apply to this job\n"
                    "MRD Recruitment is seeking an experienced Engineering Manager on behalf of a "
                    "leading manufacturing client based in Falkirk.\n"
                    "Just posted\n"
                    "Projects Manager - Fire Systems\n"
                    "Equans\t3.2\t3.2/5 rating\n"
                    "Edinburgh\n"
                    "This is a full-time role working 37.5 hours per week. On offer is a competitive "
                    "salary, company vehicle or allowance, bonus and benefits package.\n"
                    "Just posted\n"
                    "Transfer Agency UK, Associate 2\n"
                    "State Street\t3.4\t3.4/5 rating\n"
                    "Edinburgh\n"
                    "A Transfer Agency specialist, at Associate 2 level to join our Transfer Agency team. "
                    "You will be responsible for collecting and processing complex data,…\n"
                    "Just posted\n"
                    "Director of HR\n"
                    "Barclays\t3.9\t3.9/5 rating\n"
                    "Livingston\n"
                    "Employee Relations Workforce Change & Restructuring manages the global change and "
                    "restructuring portfolios across all employing entities;…\n"
                    "7 days ago\n"
                    "Senior IAM Developer (One Identity)\n"
                    "Sky\t3.3\t3.3/5 rating\n"
                    "Linlithgow\n"
                    "You will be an authentication and access management specialist who will be comfortable "
                    "developing, implementing, and maintaining secure and efficient IAM…\n"
                    "1 day ago\n"
                    "Senior IAM Developer (One Identity)\n"
                    "Sky\t3.3\t3.3/5 rating\n"
                    "Queensferry\n"
                    "You will be an authentication and access management specialist who will be comfortable "
                    "developing, implementing, and maintaining secure and efficient IAM…\n"
                    "1 day ago\n"
                    "Senior IAM Developer (One Identity)\n"
                    "Sky\t3.3\t3.3/5 rating\n"
                    "Falkirk\n"
                    "You will be an authentication and access management specialist who will be comfortable "
                    "developing, implementing, and maintaining secure and efficient IAM…\n"
                    "1 day ago\n"
                    "Account Executive - SaaS\n"
                    "Marmion\n"
                    "Edinburgh\n"
                    "£28,500 - £30,000 a year\n"
                    "Easily apply to this job\n"
                    "Hybrid working (3 days per week in the office). Employee Stock Purchase Program, "
                    "Paid Volunteer Days, Healthcare Policy, Custom Learning Experience.\n"
                    "3 days ago\n"
                    "Senior IAM Developer (One Identity)\n"
                    "Sky\t3.3\t3.3/5 rating\n"
                    "Scotland\n"
                    "You will be an authentication and access management specialist who will be comfortable "
                    "developing, implementing, and maintaining secure and efficient IAM…\n"
                    "1 day ago\n"
                    "Learning Technologist\n"
                    "APPRENTIFY GROUP\n"
                    "United Kingdom\n"
                    "£32,000 a year\n"
                    "Easily apply to this job\n"
                    "In this mid-level role, you will take a leading role in building, and maintaining "
                    "high-quality digital learning content within our Learning Management System (…\n"
                    "3 days ago\n"
                    "HCT Technical Support Engineer\n"
                    "Hitachi Construction Machinery (UK) Ltd\t3.7\t3.7/5 rating\n"
                    "United Kingdom\n"
                    "Easily apply to this job\n"
                    "The successful candidate will play a crucial role in providing technical assistance "
                    "and support to our customers, ensuring optimal performance and satisfaction…"
                ),
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["candidate_count"] == 12
        assert body["created_count"] == 12

        with session_local() as db:
            jobs = list(
                db.scalars(select(Job).where(Job.uuid.in_(body["job_uuids"])).order_by(Job.id))
            )

            assert len(jobs) == 12
            assert [job.title for job in jobs[:3]] == [
                "Financial Transformation Manager - Insurance (Finance, Data & Systems)",
                "Engineering Manager",
                "Projects Manager - Fire Systems",
            ]
            assert [job.company for job in jobs[:3]] == ["KPMG", "MRD Recruitment", "Equans"]
            assert jobs[-1].title == "HCT Technical Support Engineer"
            assert jobs[-1].company == "Hitachi Construction Machinery (UK) Ltd"
            assert jobs[-1].location == "United Kingdom"
            assert all(job.source_url is None for job in jobs)
            assert all(job.intake_state == "needs_review" for job in jobs)
            assert [job.structured_data["email_capture"]["candidate_index"] for job in jobs] == list(
                range(1, 13)
            )
            assert all(job.structured_data["email_capture"]["candidate_count"] == 12 for job in jobs)
            assert jobs[0].structured_data["email_capture"]["extraction"]["method"] == (
                "deterministic_indeed_saved_alert"
            )
            assert "12 new technical program manager jobs" not in (jobs[0].description_raw or "")
    finally:
        app.dependency_overrides.clear()


def test_email_capture_api_prefers_linkedin_direct_roles_over_html_action_links(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.post(
            "/api/inbox/email-captures",
            json={
                "subject": "LinkedIn jobs alert",
                "sender": "jobs-listings@linkedin.com",
                "body_html": """
                  <p>People with similar roles applied to these jobs</p>
                  <p>Wise</p>
                  <p>Technical Project Director, Global Product, Servicing</p>
                  <p>Wise · London</p>
                  <a href="https://www.linkedin.com/comm/jobs/view/111">View</a>
                  <p>Mapbox</p>
                  <p>Senior Leader, Technical Program Management</p>
                  <p>Mapbox · London (Remote)</p>
                  <a href="https://www.linkedin.com/comm/jobs/view/222">View</a>
                  <p>Companies with the most job openings in your role</p>
                  <a href="https://www.linkedin.com/jobs/search/?currentJobId=333">View jobs</a>
                  <a href="https://www.linkedin.com/help/linkedin">Help</a>
                  <a href="https://www.linkedin.com/psettings/email">Unsubscribe</a>
                """,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["candidate_count"] == 2
        assert body["created_count"] == 2

        with session_local() as db:
            jobs = list(db.scalars(select(Job).where(Job.uuid.in_(body["job_uuids"]))))

            assert {job.title for job in jobs} == {
                "Technical Project Director, Global Product, Servicing",
                "Senior Leader, Technical Program Management",
            }
            assert all(job.source_url is None for job in jobs)
            assert all(job.structured_data["email_capture"]["candidate_count"] == 2 for job in jobs)
    finally:
        app.dependency_overrides.clear()


def test_email_capture_api_uses_html_body_when_text_is_empty(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.post(
            "/api/inbox/email-captures",
            json={
                "subject": "HTML role",
                "body_html": "<p>Apply at <a href='https://jobs.example.com/html'>role</a></p>",
            },
        )

        assert response.status_code == 200
        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == response.json()["job_uuid"]))

            assert job is not None
            assert job.description_raw == "Apply at role"
            assert job.source_url == "https://jobs.example.com/html"
    finally:
        app.dependency_overrides.clear()


def test_email_capture_api_deduplicates_existing_owned_job(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            existing_job = Job(
                owner_user_id=user.id,
                title="Existing role",
                status="interested",
                source_url="https://jobs.example.com/existing",
                intake_state="accepted",
            )
            db.add(existing_job)
            db.commit()
            existing_uuid = existing_job.uuid
        login(client, "jobseeker@example.com")

        response = client.post(
            "/api/inbox/email-captures",
            json={
                "subject": "Existing role from email",
                "body_text": "See https://jobs.example.com/existing",
            },
        )

        assert response.status_code == 200
        assert response.json()["created"] is False
        assert response.json()["job_uuid"] == existing_uuid
        assert response.json()["intake_state"] == "accepted"

        with session_local() as db:
            jobs = db.scalars(select(Job)).all()
            email_intakes = db.scalars(select(EmailIntake)).all()
            job = db.scalar(select(Job).where(Job.uuid == existing_uuid))

            assert len(jobs) == 1
            assert len(email_intakes) == 1
            assert job is not None
            assert job.status == "interested"
            assert job.intake_state == "accepted"
            assert job.email_intake_id == email_intakes[0].id
            assert job.communications[-1].subject == "Email captured"
    finally:
        app.dependency_overrides.clear()


def test_email_capture_form_creates_inbox_job(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.post(
            "/inbox/email",
            data={
                "subject": "Pasted role",
                "sender": "alerts@example.com",
                "received_at": "2026-04-18T10:15",
                "body_text": "Apply at https://jobs.example.com/pasted",
                "body_html": "",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/inbox"
        assert "Pasted role" in client.get("/inbox").text
        assert "Pasted role" not in client.get("/board?workflow=prospects").text
    finally:
        app.dependency_overrides.clear()


def test_inbox_review_page_renders_for_owned_inbox_job(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        token = create_capture_token(client, session_local)
        captured = client.post(
            "/api/capture/jobs",
            headers={"Authorization": f"Bearer {token}"},
                json={
                    "source_url": "https://jobs.example.com/review",
                    "title": "Review role",
                    "company": "Capture Co",
                    "location": "Remote",
                    "description": "Reviewable role description.",
                },
            )
        job_uuid = captured.json()["uuid"]

        response = client.get(f"/inbox/{job_uuid}/review")

        assert response.status_code == 200
        assert "Review Inbox Item" in response.text
        assert 'action="/inbox/' in response.text
        assert "Capture Co" in response.text
        assert "https://jobs.example.com/review" in response.text
        assert "Captured context" in response.text
        assert 'data-ui-component="review-readiness"' in response.text
        assert "Ready for decision" in response.text
    finally:
        app.dependency_overrides.clear()


def test_inbox_review_page_flags_partial_low_confidence_candidate(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="partial@example.com", password="password")
            db.flush()
            job = Job(
                owner_user_id=user.id,
                title="Partial capture",
                status="saved",
                intake_source="api_capture",
                intake_confidence="low",
                intake_state="needs_review",
            )
            db.add(job)
            db.commit()
            job_uuid = job.uuid
        login(client, "partial@example.com")

        response = client.get(f"/inbox/{job_uuid}/review")

        assert response.status_code == 200
        assert "Needs cleanup before accept" in response.text
        assert "Company missing" in response.text
        assert "Location missing" in response.text
        assert "Source link missing" in response.text
        assert "Description missing" in response.text
        assert "Low confidence" in response.text
        assert "cleanup checks" in client.get("/inbox").text
    finally:
        app.dependency_overrides.clear()


def test_inbox_review_update_saves_changes_and_creates_note(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        token = create_capture_token(client, session_local)
        captured = client.post(
            "/api/capture/jobs",
            headers={"Authorization": f"Bearer {token}"},
            json={"source_url": "https://jobs.example.com/original", "title": "Original title"},
        )
        job_uuid = captured.json()["uuid"]

        response = client.post(
            f"/inbox/{job_uuid}/review",
            data={
                "title": " Updated title ",
                "company": "  New Co  ",
                "location": " Remote ",
                "source": " Email ",
                "source_url": " https://jobs.example.com/updated ",
                "description_raw": " Tailored description ",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == f"/inbox/{job_uuid}/review"

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))

            assert job is not None
            assert job.title == "Updated title"
            assert job.company == "New Co"
            assert job.location == "Remote"
            assert job.source == "Email"
            assert job.source_url == "https://jobs.example.com/updated"
            assert job.apply_url == "https://jobs.example.com/updated"
            assert job.description_raw == "Tailored description"
            assert job.description_clean == "Tailored description"
            assert job.communications[-1].subject == "Inbox enriched"
            assert "title" in (job.communications[-1].notes or "")
    finally:
        app.dependency_overrides.clear()


def test_inbox_review_update_rejects_blank_title(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        token = create_capture_token(client, session_local)
        captured = client.post(
            "/api/capture/jobs",
            headers={"Authorization": f"Bearer {token}"},
            json={"source_url": "https://jobs.example.com/blank-title", "title": "Role"},
        )
        job_uuid = captured.json()["uuid"]

        response = client.post(
            f"/inbox/{job_uuid}/review",
            data={"title": "   "},
        )

        assert response.status_code == 200
        assert "Title is required" in response.text

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))

            assert job is not None
            assert job.title == "Role"
            assert all(note.subject != "Inbox enriched" for note in job.communications)
    finally:
        app.dependency_overrides.clear()


def test_inbox_review_page_is_owner_scoped(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="owner@example.com", password="password")
            other = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            job = Job(
                owner_user_id=other.id,
                title="Other inbox role",
                status="saved",
                intake_source="api_capture",
                intake_confidence="medium",
                intake_state="needs_review",
            )
            db.add(job)
            db.commit()
            job_uuid = job.uuid

        login(client, "owner@example.com")

        response = client.get(f"/inbox/{job_uuid}/review")

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_inbox_review_page_renders_ai_support(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        token = create_capture_token(client, session_local)
        captured = client.post(
            "/api/capture/jobs",
            headers={"Authorization": f"Bearer {token}"},
            json={"source_url": "https://jobs.example.com/ai-review", "title": "Role"},
        )
        job_uuid = captured.json()["uuid"]

        response = client.get(f"/inbox/{job_uuid}/review")

        assert response.status_code == 200
        assert "Visible AI output" in response.text
        assert "Generate fit summary" in response.text
        assert "Suggest next step" in response.text
        assert 'action="/inbox/' in response.text
        assert 'name="output_type" value="fit_summary"' in response.text
    finally:
        app.dependency_overrides.clear()


def test_inbox_review_ai_generation_requires_enabled_provider(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        token = create_capture_token(client, session_local)
        captured = client.post(
            "/api/capture/jobs",
            headers={"Authorization": f"Bearer {token}"},
            json={"source_url": "https://jobs.example.com/ai-missing-provider", "title": "Role"},
        )
        job_uuid = captured.json()["uuid"]

        response = client.post(
            f"/inbox/{job_uuid}/ai-outputs",
            data={"output_type": "fit_summary"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert "ai_error=" in response.headers["location"]

        detail_response = client.get(response.headers["location"])
        assert "Enable an AI provider in Settings before generating AI output" in detail_response.text
    finally:
        app.dependency_overrides.clear()


def test_inbox_review_ai_generation_creates_visible_output(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        token = create_capture_token(client, session_local)
        captured = client.post(
            "/api/capture/jobs",
            headers={"Authorization": f"Bearer {token}"},
            json={"source_url": "https://jobs.example.com/ai-success", "title": "Role"},
        )
        job_uuid = captured.json()["uuid"]

        def fake_generate_job_ai_output(db, user, job, *, output_type, profile=None):
            output = AiOutput(
                owner_user_id=user.id,
                job_id=job.id,
                output_type=output_type,
                title="AI fit summary",
                body="### Strengths\n* **Clear relevance**",
                provider="gemini",
                model_name="gemini-flash-latest",
            )
            db.add(output)
            db.flush()
            return output

        monkeypatch.setattr("app.api.routes.inbox.generate_job_ai_output", fake_generate_job_ai_output)

        response = client.post(
            f"/inbox/{job_uuid}/ai-outputs",
            data={"output_type": "fit_summary"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert "ai_status=AI%20output%20generated" in response.headers["location"]

        detail_response = client.get(response.headers["location"])
        assert detail_response.status_code == 200
        assert "AI output generated" in detail_response.text
        assert "AI fit summary" in detail_response.text
        assert "Clear relevance" in detail_response.text
        assert "<strong>Clear relevance</strong>" in detail_response.text

        with session_local() as db:
            outputs = db.scalars(select(AiOutput)).all()
            assert len(outputs) == 1
            assert outputs[0].job.uuid == job_uuid
            assert outputs[0].output_type == "fit_summary"
    finally:
        app.dependency_overrides.clear()
