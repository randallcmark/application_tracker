from pathlib import Path

from sqlalchemy import select

from app.auth.users import create_local_user
from app.db.models.ai_output import AiOutput
from app.db.models.artefact import Artefact
from app.db.models.competency_evidence import CompetencyEvidence
from app.db.models.job import Job
from app.main import app
from app.services.competency_evidence import create_competency_evidence
from tests.test_local_auth_routes import build_client


def login(client, email: str, password: str = "password") -> None:
    response = client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200


def test_competency_library_requires_authentication(tmp_path: Path, monkeypatch) -> None:
    client, _ = build_client(tmp_path, monkeypatch)
    try:
        response = client.get("/competencies")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_competency_library_renders_empty_state_and_shell_entry(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/competencies")

        assert response.status_code == 200
        assert 'data-ui-component="competency-evidence-library"' in response.text
        assert 'data-ui-component="competency-evidence-create"' in response.text
        assert 'data-ui-component="competency-prompt-theme"' in response.text
        assert 'data-ui-component="competency-prompt-star"' in response.text
        assert 'data-ui-component="competency-prompt-credibility"' in response.text
        assert 'data-ui-component="competency-prompt-reuse"' in response.text
        assert "What competency or theme does this example demonstrate?" in response.text
        assert "What changed as a result?" in response.text
        assert "No competency evidence yet" in response.text
        assert "Competency Evidence" in response.text
        assert '<a class="active" href="/competencies">Competency Evidence</a>' in response.text
    finally:
        app.dependency_overrides.clear()


def test_competency_library_lists_only_owned_evidence(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            other_user = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="Staff TPM role")
            db.add(job)
            db.flush()
            create_competency_evidence(
                db,
                user,
                title="Platform migration recovery",
                competency="Delivery leadership",
                situation="A migration was blocked.",
                task="Recover executive confidence.",
                action="Reset governance and supplier cadence.",
                result="Recovered launch readiness.",
                strength="strong",
                tags=["platform", "leadership"],
                source_kind="job",
                source_job=job,
            )
            create_competency_evidence(
                db,
                other_user,
                title="Hidden foreign evidence",
                competency="Leadership",
            )
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/competencies")

        assert response.status_code == 200
        assert 'data-ui-component="competency-evidence-card"' in response.text
        assert "Platform migration recovery" in response.text
        assert "Delivery leadership" in response.text
        assert "Recovered launch readiness." in response.text
        assert "platform" in response.text
        assert "Source role:" in response.text
        assert "Staff TPM role" in response.text
        assert "Refine with prompts" in response.text
        assert "What makes this credible?" in response.text
        assert "Hidden foreign evidence" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_competency_library_renders_latest_star_shaping_output(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            evidence = create_competency_evidence(
                db,
                user,
                title="Platform migration recovery",
                competency="Delivery leadership",
            )
            hidden = create_competency_evidence(
                db,
                user,
                title="Unshaped evidence",
                competency="Stakeholder management",
            )
            db.add_all(
                [
                    AiOutput(
                        owner_user_id=user.id,
                        output_type="competency_star_shaping",
                        title="AI STAR shaping",
                        body="### STAR response\n* **Situation:** A migration was blocked.",
                        provider="gemini",
                        model_name="gemini-flash-latest",
                        source_context={
                            "competency_evidence_uuid": evidence.uuid,
                            "prompt_contract": "competency_star_shaping_v1",
                        },
                    ),
                    AiOutput(
                        owner_user_id=user.id,
                        output_type="competency_star_shaping",
                        title="Hidden shaping",
                        body="### STAR response\n* Hidden",
                        provider="gemini",
                        source_context={
                            "competency_evidence_uuid": "foreign-or-deleted",
                            "prompt_contract": "competency_star_shaping_v1",
                        },
                    ),
                ]
            )
            db.commit()
            hidden_uuid = hidden.uuid
        login(client, "jobseeker@example.com")

        response = client.get("/competencies")

        assert response.status_code == 200
        assert 'data-ui-component="competency-star-shaping-output"' in response.text
        assert "AI STAR shaping" in response.text
        assert "<strong>Situation:</strong>" in response.text
        assert "Hidden shaping" not in response.text
        assert hidden_uuid in response.text
    finally:
        app.dependency_overrides.clear()


def test_competency_library_prefills_source_job_without_persisting(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            other_user = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="Staff TPM", company="Example Co", status="saved")
            foreign_job = Job(owner_user_id=other_user.id, title="Hidden role", status="saved")
            db.add_all([job, foreign_job])
            db.commit()
            job_uuid = job.uuid
            foreign_uuid = foreign_job.uuid
        login(client, "jobseeker@example.com")

        response = client.get(f"/competencies?source_job_uuid={job_uuid}")
        foreign_response = client.get(f"/competencies?source_job_uuid={foreign_uuid}")

        assert response.status_code == 200
        assert 'data-ui-component="competency-source-prefill"' in response.text
        assert "Role: Staff TPM" in response.text
        assert 'name="source_kind" value="job"' in response.text
        assert f'name="source_job_uuid" value="{job_uuid}"' in response.text
        assert "Evidence for Staff TPM" in response.text
        assert foreign_response.status_code == 200
        assert "Hidden role" not in foreign_response.text
        with session_local() as db:
            assert db.query(CompetencyEvidence).count() == 0
    finally:
        app.dependency_overrides.clear()


def test_competency_create_persists_source_artefact_context(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            artefact = Artefact(
                owner_user_id=user.id,
                kind="resume",
                filename="baseline.md",
                storage_key="artefacts/baseline.md",
            )
            db.add(artefact)
            db.commit()
            artefact_uuid = artefact.uuid
        login(client, "jobseeker@example.com")

        response = client.post(
            "/competencies",
            data={
                "title": "Evidence from baseline resume",
                "competency": "Delivery leadership",
                "result": "Recovered launch readiness.",
                "strength": "working",
                "source_kind": "artefact",
                "source_artefact_uuid": artefact_uuid,
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        with session_local() as db:
            evidence = db.query(CompetencyEvidence).one()
            assert evidence.source_kind == "artefact"
            assert evidence.source_artefact is not None
            assert evidence.source_artefact.uuid == artefact_uuid
            assert evidence.source_job is None
    finally:
        app.dependency_overrides.clear()


def test_competency_evidence_can_be_created_from_form(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.post(
            "/competencies",
            data={
                "title": "Executive stakeholder recovery",
                "competency": "Stakeholder management",
                "situation": "A launch path was contested.",
                "task": "Align directors on a smaller first release.",
                "action": "Built a trade-off narrative and reset cadence.",
                "result": "Agreement reached before steering group.",
                "evidence_notes": "Useful for senior stakeholder questions.",
                "strength": "working",
                "tags": "leadership, stakeholders",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/competencies"
        with session_local() as db:
            evidence = db.query(CompetencyEvidence).one()
            assert evidence.title == "Executive stakeholder recovery"
            assert evidence.competency == "Stakeholder management"
            assert evidence.strength == "working"
            assert evidence.tags == "leadership, stakeholders"
            assert evidence.source_kind == "manual"
    finally:
        app.dependency_overrides.clear()


def test_competency_star_shaping_route_creates_visible_output_without_mutating_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            evidence = create_competency_evidence(
                db,
                user,
                title="Executive stakeholder recovery",
                competency="Stakeholder management",
                result="Agreement reached before steering group.",
                strength="working",
            )
            db.commit()
            evidence_uuid = evidence.uuid
        login(client, "jobseeker@example.com")

        def fake_generate_competency_star_shaping(db, user, evidence, *, profile=None):
            output = AiOutput(
                owner_user_id=user.id,
                output_type="competency_star_shaping",
                title="AI STAR shaping",
                body="### STAR response\n* Shaped response",
                provider="system",
                source_context={
                    "surface": "competency_library",
                    "competency_evidence_uuid": evidence.uuid,
                    "prompt_contract": "competency_star_shaping_v1",
                },
            )
            db.add(output)
            db.flush()
            return output

        monkeypatch.setattr(
            "app.api.routes.competencies.generate_competency_star_shaping",
            fake_generate_competency_star_shaping,
        )

        response = client.post(f"/competencies/{evidence_uuid}/star-shaping", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/competencies?ai_status=STAR%20shaping%20generated"
        with session_local() as db:
            evidence = db.query(CompetencyEvidence).filter_by(uuid=evidence_uuid).one()
            output = db.scalar(select(AiOutput).where(AiOutput.output_type == "competency_star_shaping"))
            assert evidence.title == "Executive stakeholder recovery"
            assert evidence.result == "Agreement reached before steering group."
            assert output is not None
            assert output.source_context["competency_evidence_uuid"] == evidence_uuid
    finally:
        app.dependency_overrides.clear()


def test_competency_evidence_update_is_owner_scoped(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            other_user = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            owned = create_competency_evidence(
                db,
                user,
                title="Rough delivery example",
                competency="Delivery",
            )
            foreign = create_competency_evidence(
                db,
                other_user,
                title="Foreign example",
                competency="Leadership",
            )
            db.commit()
            owned_uuid = owned.uuid
            foreign_uuid = foreign.uuid
        login(client, "jobseeker@example.com")

        response = client.post(
            f"/competencies/{owned_uuid}",
            data={
                "title": "Polished delivery example",
                "competency": "Delivery leadership",
                "situation": "A delivery was blocked.",
                "task": "Create a recoverable path.",
                "action": "Cut scope and rebuilt the plan.",
                "result": "Released on the revised date.",
                "strength": "strong",
                "tags": "delivery, recovery",
            },
            follow_redirects=False,
        )
        foreign_response = client.post(
            f"/competencies/{foreign_uuid}",
            data={"title": "Should not update", "strength": "strong"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert foreign_response.status_code == 404
        with session_local() as db:
            owned_evidence = db.query(CompetencyEvidence).filter_by(uuid=owned_uuid).one()
            foreign_evidence = db.query(CompetencyEvidence).filter_by(uuid=foreign_uuid).one()
            assert owned_evidence.title == "Polished delivery example"
            assert owned_evidence.strength == "strong"
            assert owned_evidence.tags == "delivery, recovery"
            assert foreign_evidence.title == "Foreign example"
    finally:
        app.dependency_overrides.clear()
