from pathlib import Path

from sqlalchemy import func, select

from app.auth.users import create_local_user
from app.core.config import settings
from app.db.models.application import Application
from app.db.models.artefact import Artefact
from app.db.models.communication import Communication
from app.db.models.interview_event import InterviewEvent
from app.db.models.job import Job
from app.main import app
from tests.test_local_auth_routes import build_client


def login(client, email: str, password: str = "password") -> None:
    response = client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200


def create_user_with_jobs(session_local, *, email: str) -> list[str]:
    with session_local() as db:
        user = create_local_user(db, email=email, password="password")
        db.flush()
        jobs = [
            Job(
                owner_user_id=user.id,
                title="Saved role",
                company="Example Co",
                status="saved",
                board_position=2,
            ),
            Job(
                owner_user_id=user.id,
                title="Applied role",
                company="Other Co",
                status="applied",
                board_position=1,
            ),
            Job(
                owner_user_id=user.id,
                title="Archived role",
                company="Old Co",
                status="archived",
                board_position=0,
            ),
        ]
        db.add_all(jobs)
        db.commit()
        return [job.uuid for job in jobs]


def test_list_jobs_returns_current_users_non_archived_jobs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        create_user_with_jobs(session_local, email="other@example.com")
        login(client, "jobseeker@example.com")

        response = client.get("/api/jobs")

        assert response.status_code == 200
        titles = [job["title"] for job in response.json()]
        assert titles == ["Saved role", "Applied role"]
    finally:
        app.dependency_overrides.clear()


def test_list_jobs_can_include_archived_jobs(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.get("/api/jobs?include_archived=true")

        assert response.status_code == 200
        titles = {job["title"] for job in response.json()}
        assert titles == {"Saved role", "Applied role", "Archived role"}
    finally:
        app.dependency_overrides.clear()


def test_create_job_adds_manual_job_for_current_user(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.post(
            "/api/jobs",
            json={
                "title": "Manual role",
                "company": "Manual Co",
                "status": "interested",
                "source_url": "https://jobs.example.com/manual",
                "apply_url": "https://jobs.example.com/manual/apply",
                "location": "Remote",
                "remote_policy": "remote",
                "salary_min": "100000",
                "salary_max": "120000",
                "salary_currency": "GBP",
                "description_raw": "Build useful systems.",
                "initial_note": "Worth tracking.",
            },
        )

        assert response.status_code == 201
        assert response.json()["title"] == "Manual role"
        assert response.json()["status"] == "interested"
        assert response.json()["board_position"] == 0

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == response.json()["uuid"]))

            assert job is not None
            assert job.owner.email == "jobseeker@example.com"
            assert job.source == "manual"
            assert job.company == "Manual Co"
            assert job.description_raw == "Build useful systems."
            assert job.communications[0].subject == "Created manually"
    finally:
        app.dependency_overrides.clear()


def test_create_job_rejects_archived_status(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.post("/api/jobs", json={"title": "Old role", "status": "archived"})

        assert response.status_code == 400
        assert response.json()["detail"] == "New job status must be an active board status"
    finally:
        app.dependency_overrides.clear()


def test_get_job_hides_cross_user_job_as_not_found(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        other_job_uuid = create_user_with_jobs(session_local, email="other@example.com")[0]
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.get(f"/api/jobs/{other_job_uuid}")

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_update_job_edits_fields_and_journals_status_change(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.patch(
            f"/api/jobs/{job_uuid}",
            json={
                "title": "Corrected role",
                "company": "Corrected Co",
                "status": "preparing",
                "source": "manual",
                "source_url": None,
                "apply_url": "https://jobs.example.com/apply",
                "location": "Hybrid",
                "remote_policy": "hybrid",
                "salary_min": "95000",
                "salary_max": "120000",
                "salary_currency": "GBP",
                "description_raw": "Corrected description.",
            },
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Corrected role"
        assert response.json()["status"] == "preparing"
        assert response.json()["source_url"] is None

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))

            assert job is not None
            assert job.company == "Corrected Co"
            assert job.salary_min == 95000
            assert job.description_clean == "Corrected description."
            event = db.scalar(
                select(Communication).where(
                    Communication.job_id == job.id,
                    Communication.event_type == "stage_change",
                )
            )
            assert event is not None
            assert event.subject == "Status changed from saved to preparing"
            edit_event = db.scalar(
                select(Communication).where(
                    Communication.job_id == job.id,
                    Communication.subject == "Job edited",
                )
            )
            assert edit_event is not None
            assert edit_event.notes == (
                "Updated fields: title, company, source, apply URL, location, remote policy, "
                "salary minimum, salary maximum, salary currency, description."
            )
    finally:
        app.dependency_overrides.clear()


def test_update_job_journals_field_edits_without_status_change(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.patch(
            f"/api/jobs/{job_uuid}",
            json={"location": "Remote", "salary_currency": "GBP"},
        )

        assert response.status_code == 200

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))

            assert job is not None
            event = db.scalar(
                select(Communication).where(
                    Communication.job_id == job.id,
                    Communication.subject == "Job edited",
                )
            )
            assert event is not None
            assert event.event_type == "note"
            assert event.notes == "Updated fields: location, salary currency."
    finally:
        app.dependency_overrides.clear()


def test_update_job_does_not_journal_unchanged_fields(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.patch(f"/api/jobs/{job_uuid}", json={"company": "Example Co"})

        assert response.status_code == 200

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))

            assert job is not None
            event_count = db.scalar(
                select(func.count(Communication.id)).where(
                    Communication.job_id == job.id,
                    Communication.subject == "Job edited",
                )
            )
            assert event_count == 0
    finally:
        app.dependency_overrides.clear()


def test_update_job_rejects_blank_title(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.patch(f"/api/jobs/{job_uuid}", json={"title": "   "})

        assert response.status_code == 400
        assert response.json()["detail"] == "Job title is required"
    finally:
        app.dependency_overrides.clear()


def test_update_job_hides_cross_user_job(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        other_job_uuid = create_user_with_jobs(session_local, email="other@example.com")[0]
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.patch(f"/api/jobs/{other_job_uuid}", json={"title": "Nope"})

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_update_job_board_persists_status_and_position(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.patch(
            f"/api/jobs/{job_uuid}/board",
            json={"status": "interviewing", "board_position": 4},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "interviewing"
        assert response.json()["board_position"] == 4

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))

            assert job is not None
            assert job.status == "interviewing"
            assert job.board_position == 4
            assert job.archived_at is None

            event = db.scalar(
                select(Communication).where(
                    Communication.job_id == job.id,
                    Communication.event_type == "stage_change",
                )
            )
            assert event is not None
            assert event.owner_user_id == job.owner_user_id
            assert event.subject == "Status changed from saved to interviewing"
            assert event.notes == "Job status changed from saved to interviewing."
    finally:
        app.dependency_overrides.clear()


def test_update_job_board_sets_archive_timestamp(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.patch(f"/api/jobs/{job_uuid}/board", json={"status": "archived"})

        assert response.status_code == 200
        assert response.json()["status"] == "archived"

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))

            assert job is not None
            assert job.archived_at is not None
    finally:
        app.dependency_overrides.clear()


def test_update_job_board_rejects_unknown_status(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.patch(f"/api/jobs/{job_uuid}/board", json={"status": "wishlist"})

        assert response.status_code == 400
        assert "Unsupported job status" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_update_job_board_position_only_does_not_create_stage_event(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.patch(f"/api/jobs/{job_uuid}/board", json={"board_position": 9})

        assert response.status_code == 200

        with session_local() as db:
            events = db.scalars(select(Communication)).all()

            assert events == []
    finally:
        app.dependency_overrides.clear()


def test_bulk_board_update_persists_statuses_and_positions(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        saved_uuid, applied_uuid, _ = create_user_with_jobs(
            session_local,
            email="jobseeker@example.com",
        )
        login(client, "jobseeker@example.com")

        response = client.patch(
            "/api/jobs/board",
            json={
                "columns": {
                    "saved": [applied_uuid],
                    "interested": [],
                    "preparing": [],
                    "applied": [saved_uuid],
                    "interviewing": [],
                    "offer": [],
                    "rejected": [],
                }
            },
        )

        assert response.status_code == 200

        with session_local() as db:
            saved_job = db.scalar(select(Job).where(Job.uuid == saved_uuid))
            applied_job = db.scalar(select(Job).where(Job.uuid == applied_uuid))

            assert saved_job is not None
            assert applied_job is not None
            assert saved_job.status == "applied"
            assert saved_job.board_position == 0
            assert applied_job.status == "saved"
            assert applied_job.board_position == 0

            events = db.scalars(
                select(Communication).order_by(Communication.subject)
            ).all()
            assert [event.subject for event in events] == [
                "Status changed from applied to saved",
                "Status changed from saved to applied",
            ]
    finally:
        app.dependency_overrides.clear()


def test_bulk_board_update_rejects_cross_user_job(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        other_uuid = create_user_with_jobs(session_local, email="other@example.com")[0]
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.patch(
            "/api/jobs/board",
            json={
                "columns": {
                    "saved": [other_uuid],
                    "interested": [],
                    "preparing": [],
                    "applied": [],
                    "interviewing": [],
                    "offer": [],
                    "rejected": [],
                }
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Board update contains unknown jobs"
    finally:
        app.dependency_overrides.clear()


def test_bulk_board_update_rejects_duplicate_job_uuid(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.patch(
            "/api/jobs/board",
            json={
                "columns": {
                    "saved": [job_uuid],
                    "interested": [job_uuid],
                    "preparing": [],
                    "applied": [],
                    "interviewing": [],
                    "offer": [],
                    "rejected": [],
                }
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "A job can appear only once in a board update"
    finally:
        app.dependency_overrides.clear()


def test_job_timeline_lists_stage_change_events(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")
        update_response = client.patch(
            f"/api/jobs/{job_uuid}/board",
            json={"status": "interviewing"},
        )
        assert update_response.status_code == 200

        response = client.get(f"/api/jobs/{job_uuid}/timeline")

        assert response.status_code == 200
        assert response.json()[0]["event_type"] == "stage_change"
        assert response.json()[0]["subject"] == "Status changed from saved to interviewing"
    finally:
        app.dependency_overrides.clear()


def test_create_job_timeline_note_adds_owned_note(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.post(
            f"/api/jobs/{job_uuid}/timeline",
            json={
                "subject": "Recruiter call",
                "notes": "Follow up next week.",
                "follow_up_at": "2026-04-12T09:00:00Z",
            },
        )

        assert response.status_code == 201
        assert response.json()["event_type"] == "note"
        assert response.json()["subject"] == "Recruiter call"
        assert response.json()["notes"] == "Follow up next week."
        assert response.json()["follow_up_at"] == "2026-04-12T09:00:00"

        timeline_response = client.get(f"/api/jobs/{job_uuid}/timeline")

        assert timeline_response.status_code == 200
        assert timeline_response.json()[0]["event_type"] == "note"
        assert timeline_response.json()[0]["follow_up_at"] == "2026-04-12T09:00:00"
    finally:
        app.dependency_overrides.clear()


def test_create_job_timeline_note_rejects_blank_note(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.post(
            f"/api/jobs/{job_uuid}/timeline",
            json={"subject": "Empty", "notes": "   "},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Note text is required"
    finally:
        app.dependency_overrides.clear()


def test_create_job_timeline_note_hides_cross_user_job(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        other_job_uuid = create_user_with_jobs(session_local, email="other@example.com")[0]
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.post(
            f"/api/jobs/{other_job_uuid}/timeline",
            json={"subject": "Nope", "notes": "Cannot see this."},
        )

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_upload_job_artefact_stores_file_and_journals_note(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "local_storage_path", str(tmp_path / "artefacts"))
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.post(
            f"/api/jobs/{job_uuid}/artefacts",
            data={"kind": "resume"},
            files={"file": ("../Resume Final.pdf", b"resume bytes", "application/pdf")},
        )

        assert response.status_code == 201
        assert response.json()["kind"] == "resume"
        assert response.json()["filename"] == "Resume Final.pdf"
        assert response.json()["size_bytes"] == len(b"resume bytes")

        with session_local() as db:
            artefact = db.scalar(select(Artefact))
            event = db.scalar(select(Communication).where(Communication.subject == "Artefact uploaded"))

            assert artefact is not None
            assert artefact.job.uuid == job_uuid
            assert artefact.owner.email == "jobseeker@example.com"
            assert (tmp_path / "artefacts" / artefact.storage_key).read_bytes() == b"resume bytes"
            assert event is not None
            assert event.notes == "Uploaded Resume Final.pdf."
    finally:
        app.dependency_overrides.clear()


def test_upload_job_artefact_hides_cross_user_job(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "local_storage_path", str(tmp_path / "artefacts"))
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        other_job_uuid = create_user_with_jobs(session_local, email="other@example.com")[0]
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.post(
            f"/api/jobs/{other_job_uuid}/artefacts",
            data={"kind": "resume"},
            files={"file": ("resume.pdf", b"resume bytes", "application/pdf")},
        )

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_job_timeline_hides_cross_user_job(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        other_job_uuid = create_user_with_jobs(session_local, email="other@example.com")[0]
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.get(f"/api/jobs/{other_job_uuid}/timeline")

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_mark_applied_creates_application_and_journal_events(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.post(
            f"/api/jobs/{job_uuid}/mark-applied",
            json={"channel": "company_site", "notes": "Used tailored resume."},
        )

        assert response.status_code == 201
        assert response.json()["created"] is True
        assert response.json()["status"] == "applied"
        assert response.json()["channel"] == "company_site"

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))

            assert job is not None
            assert job.status == "applied"
            assert len(job.applications) == 1
            assert job.applications[0].notes == "Used tailored resume."

            event_subjects = [
                event.subject
                for event in db.scalars(
                    select(Communication).order_by(Communication.subject)
                ).all()
            ]
            assert event_subjects == [
                "Marked applied",
                "Status changed from saved to applied",
            ]
    finally:
        app.dependency_overrides.clear()


def test_mark_applied_reuses_existing_application(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        first = client.post(
            f"/api/jobs/{job_uuid}/mark-applied",
            json={"channel": "company_site", "notes": "First submission."},
        )
        second = client.post(
            f"/api/jobs/{job_uuid}/mark-applied",
            json={"channel": "referral", "notes": "Updated channel."},
        )

        assert first.status_code == 201
        assert second.status_code == 200
        assert second.json()["created"] is False
        assert second.json()["channel"] == "referral"

        with session_local() as db:
            applications = db.scalars(select(Application)).all()

            assert len(applications) == 1
    finally:
        app.dependency_overrides.clear()


def test_mark_applied_hides_cross_user_job(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        other_job_uuid = create_user_with_jobs(session_local, email="other@example.com")[0]
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.post(
            f"/api/jobs/{other_job_uuid}/mark-applied",
            json={"channel": "company_site"},
        )

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_archive_job_moves_to_archived_and_journals_status_change(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.post(f"/api/jobs/{job_uuid}/archive", json={})

        assert response.status_code == 200
        assert response.json()["status"] == "archived"
        assert response.json()["archived_at"] is not None

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))

            assert job is not None
            assert job.status == "archived"
            assert job.archived_at is not None
            events = db.scalars(select(Communication)).all()
            assert [event.subject for event in events] == [
                "Status changed from saved to archived"
            ]
    finally:
        app.dependency_overrides.clear()


def test_archive_job_can_add_archive_note(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.post(
            f"/api/jobs/{job_uuid}/archive",
            json={"notes": "Role closed before applying."},
        )

        assert response.status_code == 200

        timeline_response = client.get(f"/api/jobs/{job_uuid}/timeline")
        subjects = [event["subject"] for event in timeline_response.json()]

        assert "Archived" in subjects
        assert "Status changed from saved to archived" in subjects
    finally:
        app.dependency_overrides.clear()


def test_archive_job_hides_cross_user_job(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        other_job_uuid = create_user_with_jobs(session_local, email="other@example.com")[0]
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.post(f"/api/jobs/{other_job_uuid}/archive", json={})

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_unarchive_job_restores_active_status_and_journals_status_change(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")
        archive_response = client.post(f"/api/jobs/{job_uuid}/archive", json={})
        assert archive_response.status_code == 200

        response = client.post(
            f"/api/jobs/{job_uuid}/unarchive",
            json={"target_status": "interested", "notes": "Back in scope."},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "interested"
        assert response.json()["archived_at"] is None

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))

            assert job is not None
            assert job.status == "interested"
            assert job.archived_at is None
            event_subjects = [
                event.subject
                for event in db.scalars(
                    select(Communication).order_by(Communication.subject)
                ).all()
            ]
            assert event_subjects == [
                "Status changed from archived to interested",
                "Status changed from saved to archived",
                "Unarchived",
            ]
    finally:
        app.dependency_overrides.clear()


def test_unarchive_job_defaults_to_saved(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        archived_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[2]
        login(client, "jobseeker@example.com")

        response = client.post(f"/api/jobs/{archived_uuid}/unarchive", json={})

        assert response.status_code == 200
        assert response.json()["status"] == "saved"
    finally:
        app.dependency_overrides.clear()


def test_unarchive_job_rejects_archived_target_status(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        archived_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[2]
        login(client, "jobseeker@example.com")

        response = client.post(
            f"/api/jobs/{archived_uuid}/unarchive",
            json={"target_status": "archived"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Unarchive target status cannot be archived"
    finally:
        app.dependency_overrides.clear()


def test_unarchive_job_hides_cross_user_job(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        other_job_uuid = create_user_with_jobs(session_local, email="other@example.com")[2]
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.post(f"/api/jobs/{other_job_uuid}/unarchive", json={})

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_schedule_interview_creates_event_moves_job_and_journals(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.post(
            f"/api/jobs/{job_uuid}/interviews",
            json={
                "stage": "Recruiter screen",
                "scheduled_at": "2026-04-12T18:30:00Z",
                "location": "Video call",
                "participants": "Recruiter",
                "notes": "Prepare salary range.",
            },
        )

        assert response.status_code == 201
        assert response.json()["stage"] == "Recruiter screen"
        assert response.json()["location"] == "Video call"

        with session_local() as db:
            job = db.scalar(select(Job).where(Job.uuid == job_uuid))
            interview = db.scalar(select(InterviewEvent))
            event_subjects = [
                event.subject
                for event in db.scalars(
                    select(Communication).order_by(Communication.subject)
                ).all()
            ]

            assert job is not None
            assert job.status == "interviewing"
            assert interview is not None
            assert interview.stage == "Recruiter screen"
            assert interview.notes == "Prepare salary range."
            assert event_subjects == [
                "Interview scheduled: Recruiter screen",
                "Status changed from saved to interviewing",
            ]
    finally:
        app.dependency_overrides.clear()


def test_schedule_interview_requires_stage(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        job_uuid = create_user_with_jobs(session_local, email="jobseeker@example.com")[0]
        login(client, "jobseeker@example.com")

        response = client.post(f"/api/jobs/{job_uuid}/interviews", json={"stage": "   "})

        assert response.status_code == 400
        assert response.json()["detail"] == "Interview stage is required"
    finally:
        app.dependency_overrides.clear()


def test_schedule_interview_hides_cross_user_job(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        other_job_uuid = create_user_with_jobs(session_local, email="other@example.com")[0]
        create_user_with_jobs(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.post(
            f"/api/jobs/{other_job_uuid}/interviews",
            json={"stage": "Recruiter screen"},
        )

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
