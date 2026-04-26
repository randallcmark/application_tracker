from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.auth.users import create_local_user
from app.db.models.ai_output import AiOutput
from app.db.models.artefact import Artefact
from app.db.models.job import Job
from app.main import app
from app.services.competency_evidence import (
    create_competency_evidence,
    get_user_competency_evidence_by_uuid,
    list_competency_evidence,
    update_competency_evidence,
)
from tests.test_local_auth_routes import build_client


def test_competency_evidence_create_list_and_get_are_owner_scoped(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            other_user = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="Source role")
            artefact = Artefact(
                owner_user_id=user.id,
                kind="resume",
                filename="baseline.md",
                storage_key="artefacts/baseline.md",
            )
            db.add_all([job, artefact])
            db.flush()
            ai_output = AiOutput(
                owner_user_id=user.id,
                job_id=job.id,
                artefact_id=artefact.id,
                output_type="draft",
                title="AI supporting statement draft",
                body="### Evidence\nPlatform migration",
            )
            db.add(ai_output)
            db.flush()

            evidence = create_competency_evidence(
                db,
                user,
                title="Platform migration recovery",
                competency="Delivery leadership",
                situation="A migration was at risk.",
                task="Stabilise delivery.",
                action="Reset governance and supplier cadence.",
                result="Recovered launch readiness.",
                evidence_notes="Used as a supporting statement seed.",
                strength="working",
                tags=["delivery", "platform", "stakeholders"],
                source_kind="artefact",
                source_job=job,
                source_artefact=artefact,
                source_ai_output=ai_output,
            )
            other_evidence = create_competency_evidence(
                db,
                other_user,
                title="Hidden evidence",
                competency="Leadership",
            )
            db.commit()
            evidence_uuid = evidence.uuid
            other_uuid = other_evidence.uuid

        with session_local() as db:
            user = db.query(type(user)).filter_by(email="jobseeker@example.com").one()
            items = list_competency_evidence(db, user)
            found = get_user_competency_evidence_by_uuid(db, user, evidence_uuid)
            hidden = get_user_competency_evidence_by_uuid(db, user, other_uuid)

            assert [item.title for item in items] == ["Platform migration recovery"]
            assert found is not None
            assert found.competency == "Delivery leadership"
            assert found.strength == "working"
            assert found.tags == "delivery, platform, stakeholders"
            assert found.source_kind == "artefact"
            assert found.source_job.title == "Source role"
            assert found.source_artefact.filename == "baseline.md"
            assert found.source_ai_output.title == "AI supporting statement draft"
            assert hidden is None
    finally:
        app.dependency_overrides.clear()


def test_competency_evidence_rejects_foreign_sources(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            other_user = create_local_user(db, email="other@example.com", password="password")
            db.flush()
            foreign_job = Job(owner_user_id=other_user.id, title="Foreign role")
            db.add(foreign_job)
            db.flush()

            with pytest.raises(ValueError, match="same user"):
                create_competency_evidence(
                    db,
                    user,
                    title="Invalid source",
                    source_kind="job",
                    source_job=foreign_job,
                )
    finally:
        app.dependency_overrides.clear()


def test_update_competency_evidence_preserves_structure_and_validates_strength(
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
                title="Rough stakeholder example",
                competency="Stakeholder management",
            )

            update_competency_evidence(
                evidence,
                title="Executive stakeholder recovery",
                action="Aligned directors around a smaller launch path.",
                result="Restored confidence before steering group.",
                strength="strong",
                tags="leadership, stakeholders",
                last_used_at=datetime(2026, 4, 26, 12, 0, tzinfo=UTC),
            )
            db.commit()

            assert evidence.title == "Executive stakeholder recovery"
            assert evidence.action == "Aligned directors around a smaller launch path."
            assert evidence.result == "Restored confidence before steering group."
            assert evidence.strength == "strong"
            assert evidence.tags == "leadership, stakeholders"
            assert evidence.last_used_at is not None

            with pytest.raises(ValueError, match="strength"):
                update_competency_evidence(evidence, strength="excellent")
    finally:
        app.dependency_overrides.clear()
