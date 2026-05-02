from datetime import UTC, datetime
from pathlib import Path

from app.auth.users import create_local_user
from app.core.config import settings
from app.db.models.artefact import Artefact
from app.db.models.job import Job
from app.db.models.job_artefact_link import JobArtefactLink
from app.main import app
from tests.test_local_auth_routes import build_client


def login(client, email: str, password: str = "password") -> None:
    response = client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200


def test_artefact_library_requires_login(tmp_path: Path, monkeypatch) -> None:
    client, _ = build_client(tmp_path, monkeypatch)
    try:
        response = client.get("/artefacts")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_artefact_library_empty_state(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()

        login(client, "jobseeker@example.com")

        response = client.get("/artefacts")

        assert response.status_code == 200
        assert "<h1>Artefacts</h1>" in response.text
        assert "No artefacts yet" in response.text
        assert 'href="/board"' in response.text
    finally:
        app.dependency_overrides.clear()


def test_artefact_library_lists_owned_job_artefacts(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            other_user = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="Library role", company="Library Co")
            other_job = Job(owner_user_id=other_user.id, title="Other role", company="Other Co")
            db.add_all([job, other_job])
            db.flush()
            artefact = Artefact(
                owner_user_id=user.id,
                job_id=job.id,
                kind="resume",
                purpose="Tailored resume",
                version_label="v1",
                notes="Used for product roles.",
                filename="resume.txt",
                storage_key="jobs/library/artefacts/resume.txt",
                size_bytes=12,
                follow_up_at=datetime(2026, 5, 4, tzinfo=UTC),
            )
            other_artefact = Artefact(
                owner_user_id=other_user.id,
                job_id=other_job.id,
                kind="cover_letter",
                filename="other.txt",
                storage_key="jobs/other/artefacts/other.txt",
                size_bytes=10,
            )
            db.add_all([artefact, other_artefact])
            db.commit()
            job_uuid = job.uuid
            artefact_uuid = artefact.uuid

        login(client, "jobseeker@example.com")

        response = client.get("/artefacts")

        assert response.status_code == 200
        assert "resume.txt" in response.text
        assert "resume" in response.text
        assert "Tailored resume" in response.text
        assert "v1" in response.text
        assert "Used for product roles." in response.text
        assert "2026-05-04 00:00" in response.text
        assert "12 bytes" in response.text
        assert "Library role" in response.text
        assert "Library Co" in response.text
        assert f'href="/jobs/{job_uuid}"' in response.text
        assert f'href="/artefacts/{artefact_uuid}"' in response.text
        assert f'href="/artefacts/{artefact_uuid}/download"' in response.text
        assert "other.txt" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_artefact_library_shows_saved_draft_provenance(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="Draft source role", company="Library Co")
            db.add(job)
            db.flush()
            baseline = Artefact(
                owner_user_id=user.id,
                job_id=job.id,
                kind="resume",
                filename="baseline.md",
                storage_key="jobs/library/artefacts/baseline.md",
                size_bytes=12,
            )
            db.add(baseline)
            db.flush()
            saved = Artefact(
                owner_user_id=user.id,
                job_id=job.id,
                kind="cover_letter",
                purpose="AI cover letter draft",
                version_label="ai-draft-v1",
                notes=(
                    f"Saved from AI draft output #7. Baseline artefact UUID: {baseline.uuid}. "
                    "Generation brief: Focus areas=Platform migrations | Tone or positioning=concise."
                ),
                outcome_context="Generated from visible AI draft output.",
                filename="cover-letter-draft.md",
                storage_key="jobs/library/artefacts/cover-letter-draft.md",
                size_bytes=20,
            )
            db.add(saved)
            db.commit()

        login(client, "jobseeker@example.com")

        response = client.get("/artefacts")

        assert response.status_code == 200
        assert "Provenance" in response.text
        assert "Saved from AI draft output #7" in response.text
        assert "Baseline artefact" in response.text
        assert "baseline.md" in response.text
        assert "Generation brief" in response.text
        assert "Platform migrations" in response.text
    finally:
        app.dependency_overrides.clear()


def test_artefact_library_updates_metadata(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            other_user = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            artefact = Artefact(
                owner_user_id=user.id,
                kind="resume",
                filename="resume.txt",
                storage_key="jobs/library/artefacts/resume.txt",
                follow_up_at=datetime(2026, 4, 30, tzinfo=UTC),
            )
            other_artefact = Artefact(
                owner_user_id=other_user.id,
                kind="resume",
                filename="hidden.txt",
                storage_key="jobs/hidden/artefacts/hidden.txt",
            )
            db.add_all([artefact, other_artefact])
            db.commit()
            artefact_id = artefact.id
            artefact_uuid = artefact.uuid
            other_artefact_uuid = other_artefact.uuid

        login(client, "jobseeker@example.com")

        response = client.post(
            f"/artefacts/{artefact_uuid}/metadata",
            data={
                "kind": "cover_letter",
                "purpose": "Narrative draft",
                "version_label": "v2",
                "notes": "Strong opener.",
                "outcome_context": "interview invite",
                "follow_up_at": "2026-05-02",
            },
            follow_redirects=False,
        )
        hidden_response = client.post(
            f"/artefacts/{other_artefact_uuid}/metadata",
            data={"kind": "cover_letter"},
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/artefacts"
        assert hidden_response.status_code == 404

        with session_local() as db:
            stored = db.get(Artefact, artefact_id)

            assert stored is not None
            assert stored.kind == "cover_letter"
            assert stored.purpose == "Narrative draft"
            assert stored.version_label == "v2"
            assert stored.notes == "Strong opener."
            assert stored.outcome_context == "interview invite"
            assert stored.follow_up_at == datetime(2026, 5, 2)

        clear_response = client.post(
            f"/artefacts/{artefact_uuid}/metadata",
            data={
                "kind": "cover_letter",
                "purpose": "Narrative draft",
                "version_label": "v2",
                "notes": "Strong opener.",
                "outcome_context": "interview invite",
                "follow_up_at": "",
            },
            follow_redirects=False,
        )

        assert clear_response.status_code == 303

        with session_local() as db:
            stored = db.get(Artefact, artefact_id)

            assert stored is not None
            assert stored.follow_up_at is None
    finally:
        app.dependency_overrides.clear()


def test_artefact_library_download_is_owner_scoped(tmp_path: Path, monkeypatch) -> None:
    artefact_root = tmp_path / "artefacts"
    monkeypatch.setattr(settings, "local_storage_path", str(artefact_root))
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            other_user = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="Download role")
            other_job = Job(owner_user_id=other_user.id, title="Hidden role")
            db.add_all([job, other_job])
            db.flush()
            storage_key = "jobs/download/artefacts/resume.txt"
            other_storage_key = "jobs/hidden/artefacts/hidden.txt"
            (artefact_root / storage_key).parent.mkdir(parents=True)
            (artefact_root / storage_key).write_bytes(b"resume bytes")
            (artefact_root / other_storage_key).parent.mkdir(parents=True)
            (artefact_root / other_storage_key).write_bytes(b"hidden bytes")
            artefact = Artefact(
                owner_user_id=user.id,
                job_id=job.id,
                kind="resume",
                filename="resume.txt",
                storage_key=storage_key,
                content_type="text/plain",
                size_bytes=12,
            )
            other_artefact = Artefact(
                owner_user_id=other_user.id,
                job_id=other_job.id,
                kind="resume",
                filename="hidden.txt",
                storage_key=other_storage_key,
                content_type="text/plain",
                size_bytes=12,
            )
            db.add_all([artefact, other_artefact])
            db.commit()
            artefact_uuid = artefact.uuid
            other_artefact_uuid = other_artefact.uuid

        login(client, "jobseeker@example.com")

        response = client.get(f"/artefacts/{artefact_uuid}/download")
        hidden_response = client.get(f"/artefacts/{other_artefact_uuid}/download")

        assert response.status_code == 200
        assert response.content == b"resume bytes"
        assert response.headers["content-disposition"].endswith("resume.txt")
        assert hidden_response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_artefact_detail_renders_markdown_preview_for_source_markdown(tmp_path: Path, monkeypatch) -> None:
    artefact_root = tmp_path / "artefacts"
    monkeypatch.setattr(settings, "local_storage_path", str(artefact_root))
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            storage_key = "jobs/detail/artefacts/resume.md"
            (artefact_root / storage_key).parent.mkdir(parents=True)
            (artefact_root / storage_key).write_text("### Summary\n* **Delivery**", encoding="utf-8")
            artefact = Artefact(
                owner_user_id=user.id,
                kind="resume",
                filename="resume.md",
                storage_key=storage_key,
                content_type="text/markdown",
                size_bytes=24,
            )
            db.add(artefact)
            db.commit()
            artefact_uuid = artefact.uuid

        login(client, "jobseeker@example.com")

        response = client.get(f"/artefacts/{artefact_uuid}")

        assert response.status_code == 200
        assert 'data-ui-component="artefact-source-card"' in response.text
        assert 'data-ui-component="artefact-preview"' in response.text
        assert "Source remains canonical" in response.text
        assert "Source Markdown" in response.text
        assert "<h4>Summary</h4>" in response.text
        assert "<strong>Delivery</strong>" in response.text
        assert f'href="/artefacts/{artefact_uuid}/download"' in response.text
    finally:
        app.dependency_overrides.clear()


def test_artefact_detail_is_owner_scoped_and_shows_unavailable_preview_for_binary_source(
    tmp_path: Path, monkeypatch
) -> None:
    artefact_root = tmp_path / "artefacts"
    monkeypatch.setattr(settings, "local_storage_path", str(artefact_root))
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            other_user = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            storage_key = "jobs/detail/artefacts/resume.bin"
            (artefact_root / storage_key).parent.mkdir(parents=True)
            (artefact_root / storage_key).write_bytes(b"\x00\x01")
            artefact = Artefact(
                owner_user_id=user.id,
                kind="resume",
                filename="resume.bin",
                storage_key=storage_key,
                content_type="application/octet-stream",
            )
            hidden = Artefact(
                owner_user_id=other_user.id,
                kind="resume",
                filename="hidden.md",
                storage_key="jobs/detail/artefacts/hidden.md",
                content_type="text/markdown",
            )
            db.add_all([artefact, hidden])
            db.commit()
            artefact_uuid = artefact.uuid
            hidden_uuid = hidden.uuid

        login(client, "jobseeker@example.com")

        response = client.get(f"/artefacts/{artefact_uuid}")
        hidden_response = client.get(f"/artefacts/{hidden_uuid}")

        assert response.status_code == 200
        assert 'data-ui-component="artefact-preview-unavailable"' in response.text
        assert "No internal text preview yet" in response.text
        assert hidden_response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_job_workspace_attaches_existing_artefact(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            other_user = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="Attach target")
            source_job = Job(owner_user_id=user.id, title="Source job")
            other_job = Job(owner_user_id=other_user.id, title="Hidden job")
            db.add_all([job, source_job, other_job])
            db.flush()
            artefact = Artefact(
                owner_user_id=user.id,
                job_id=source_job.id,
                kind="resume",
                filename="reuse.txt",
                storage_key="jobs/source/artefacts/reuse.txt",
            )
            other_artefact = Artefact(
                owner_user_id=other_user.id,
                job_id=other_job.id,
                kind="resume",
                filename="hidden.txt",
                storage_key="jobs/hidden/artefacts/hidden.txt",
            )
            db.add_all([artefact, other_artefact])
            db.commit()
            job_uuid = job.uuid
            artefact_uuid = artefact.uuid
            other_artefact_uuid = other_artefact.uuid

        login(client, "jobseeker@example.com")

        detail_response = client.get(f"/jobs/{job_uuid}?section=documents")
        response = client.post(
            f"/jobs/{job_uuid}/artefact-links",
            data={"artefact_uuid": artefact_uuid},
            follow_redirects=False,
        )
        hidden_response = client.post(
            f"/jobs/{job_uuid}/artefact-links",
            data={"artefact_uuid": other_artefact_uuid},
        )

        assert detail_response.status_code == 200
        assert "reuse.txt" in detail_response.text
        assert response.status_code == 303
        assert response.headers["location"] == f"/jobs/{job_uuid}?section=documents"
        assert hidden_response.status_code == 404

        with session_local() as db:
            links = db.query(JobArtefactLink).all()

            assert len(links) == 1
            assert links[0].job.title == "Attach target"
            assert links[0].artefact.filename == "reuse.txt"
    finally:
        app.dependency_overrides.clear()
