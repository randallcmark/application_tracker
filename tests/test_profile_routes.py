from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.auth.users import create_local_user
from app.db.models.user_profile import UserProfile
from app.main import app
from tests.test_local_auth_routes import build_client


def login(client, email: str, password: str = "password") -> None:
    response = client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200


def create_user(session_local, *, email: str) -> None:
    with session_local() as db:
        create_local_user(db, email=email, password="password")
        db.commit()


def test_get_profile_returns_empty_profile_for_new_user(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        create_user(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        response = client.get("/api/profile")

        assert response.status_code == 200
        assert response.json() == {
            "uuid": None,
            "target_roles": None,
            "target_locations": None,
            "remote_preference": None,
            "salary_min": None,
            "salary_max": None,
            "salary_currency": None,
            "preferred_industries": None,
            "excluded_industries": None,
            "constraints": None,
            "urgency": None,
            "positioning_notes": None,
        }
    finally:
        app.dependency_overrides.clear()


def test_put_profile_creates_owner_scoped_profile(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        create_user(session_local, email="jobseeker@example.com")
        create_user(session_local, email="other@example.com")
        login(client, "jobseeker@example.com")

        response = client.put(
            "/api/profile",
            json={
                "target_roles": "Engineering Manager\nProduct Engineering Lead",
                "target_locations": "London\nRemote",
                "remote_preference": "hybrid",
                "salary_min": "90000",
                "salary_max": "125000",
                "salary_currency": "gbp",
                "preferred_industries": "Developer tools\nAI infrastructure",
                "excluded_industries": "Gambling",
                "constraints": "No full-time office work.",
                "urgency": "actively searching",
                "positioning_notes": "Hands-on technical leader.",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["uuid"]
        assert body["target_roles"] == "Engineering Manager\nProduct Engineering Lead"
        assert body["salary_currency"] == "GBP"
        assert body["salary_min"] == "90000.00"

        with session_local() as db:
            profiles = db.scalars(select(UserProfile)).all()

            assert len(profiles) == 1
            assert profiles[0].owner.email == "jobseeker@example.com"
            assert profiles[0].salary_max == Decimal("125000.00")
    finally:
        app.dependency_overrides.clear()


def test_put_profile_updates_existing_profile_without_duplicate(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        create_user(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        first = client.put("/api/profile", json={"target_roles": "First", "salary_currency": "gbp"})
        second = client.put("/api/profile", json={"target_roles": "Second", "salary_currency": ""})

        assert first.status_code == 200
        assert second.status_code == 200
        assert second.json()["target_roles"] == "Second"
        assert second.json()["salary_currency"] is None

        with session_local() as db:
            profiles = db.scalars(select(UserProfile)).all()

            assert len(profiles) == 1
    finally:
        app.dependency_overrides.clear()


def test_profile_requires_login(tmp_path: Path, monkeypatch) -> None:
    client, _ = build_client(tmp_path, monkeypatch)
    try:
        response = client.get("/api/profile")

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_settings_profile_form_persists_profile(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        create_user(session_local, email="jobseeker@example.com")
        login(client, "jobseeker@example.com")

        page_response = client.get("/settings")
        assert page_response.status_code == 200
        assert "Job-search profile" in page_response.text

        response = client.post(
            "/settings/profile",
            data={
                "target_roles": "Product Engineering Lead",
                "target_locations": "London",
                "remote_preference": "flexible",
                "salary_min": "100000",
                "salary_max": "130000",
                "salary_currency": "gbp",
                "preferred_industries": "Developer tools",
                "excluded_industries": "Adtech",
                "constraints": "No frequent travel.",
                "urgency": "open",
                "positioning_notes": "Platform and product delivery.",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/settings#profile"

        with session_local() as db:
            profile = db.scalar(select(UserProfile))

            assert profile is not None
            assert profile.owner.email == "jobseeker@example.com"
            assert profile.target_roles == "Product Engineering Lead"
            assert profile.salary_currency == "GBP"
    finally:
        app.dependency_overrides.clear()
