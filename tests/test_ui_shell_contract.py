from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.auth.users import create_local_user
from app.db.models.job import Job
from app.db.models.user_profile import UserProfile
from app.main import app
from tests.test_local_auth_routes import build_client


def login(client, email: str, password: str = "password") -> None:
    response = client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 200


def assert_primary_shell_contract(html: str) -> None:
    assert 'data-shell="rich-shell"' in html
    assert 'data-shell-topbar="protected"' in html
    assert 'data-shell-nav="primary"' in html
    assert 'data-shell-actions="primary"' in html
    assert 'href="/focus"' in html
    assert 'href="/inbox"' in html
    assert 'href="/board"' in html
    assert "<span>Focus</span>" in html
    assert "<span>Inbox</span>" in html
    assert "<span>Board</span>" in html
    assert 'aria-label="User menu"' in html
    assert 'class="shell-topbar-action"' in html
    assert 'class="user-menu"' in html
    assert 'class="user-menu-panel"' in html
    assert 'id="at-scheme-btn"' in html
    assert 'href="/competencies">Competency Evidence</a>' in html
    assert '.app-topbar[data-chip-state="hidden"] .header-context' in html
    assert 'requestAnimationFrame(refreshTopbar);' in html
    assert "localStorage.getItem('at-scheme')" in html
    assert "localStorage.getItem('at-theme')" in html


def test_focus_shell_contract_preserves_nav_with_context_chip(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            db.add(
                UserProfile(
                    owner_user_id=user.id,
                    target_roles="Technical Program Manager",
                    target_locations="Edinburgh",
                    salary_min=Decimal("100000"),
                    salary_currency="GBP",
                )
            )
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/focus")

        assert response.status_code == 200
        assert_primary_shell_contract(response.text)
        assert 'data-has-chip="true"' in response.text
        assert 'data-shell-chip="context"' in response.text
        assert 'data-shell-hero="shared"' not in response.text
        assert '<p class="page-kicker">' not in response.text
        assert '<p class="page-subtitle">' not in response.text
        assert "Technical Program Manager" in response.text
    finally:
        app.dependency_overrides.clear()


def test_inbox_shell_contract_keeps_shared_hero_without_chip_placeholder(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/inbox")

        assert response.status_code == 200
        assert_primary_shell_contract(response.text)
        assert 'data-has-chip="false"' in response.text
        assert 'data-shell-chip="context"' not in response.text
        assert 'data-shell-hero="shared"' not in response.text
        assert '<p class="page-kicker">' not in response.text
        assert '<p class="page-subtitle">' not in response.text
        assert "goal-chip-slot" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_board_shell_contract_keeps_nav_visible_with_workflow_chip(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            db.add(
                Job(
                    owner_user_id=user.id,
                    title="Applied role",
                    company="Example Co",
                    status="applied",
                    updated_at=datetime.now(UTC),
                )
            )
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/board")

        assert response.status_code == 200
        assert_primary_shell_contract(response.text)
        assert 'data-has-chip="true"' in response.text
        assert 'data-shell-chip="context"' in response.text
        assert 'data-shell-hero="shared"' not in response.text
        assert "Workflow:" in response.text
        assert '<p class="page-kicker">' not in response.text
        assert '<p class="page-subtitle">' not in response.text
    finally:
        app.dependency_overrides.clear()


def test_main_authenticated_pages_use_compact_headers(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="jobseeker@example.com", password="password")
            db.commit()
        login(client, "jobseeker@example.com")

        title_pages = {
            "/jobs/new": "Add job",
            "/inbox/email/new": "Paste email",
            "/settings": "Settings",
            "/artefacts": "Artefacts",
            "/competencies": "Competency Evidence",
        }
        for route, title in title_pages.items():
            response = client.get(route)

            assert response.status_code == 200
            assert f"<h1>{title}</h1>" in response.text
            assert '<p class="page-kicker">' not in response.text
            assert '<p class="page-subtitle">' not in response.text
        for route in ("/focus", "/inbox", "/board"):
            response = client.get(route)

            assert response.status_code == 200
            assert 'data-shell-hero="shared"' not in response.text
            assert '<p class="page-kicker">' not in response.text
            assert '<p class="page-subtitle">' not in response.text
    finally:
        app.dependency_overrides.clear()


def test_shell_responsive_contract_emits_protected_nav_rules(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            db.add(
                UserProfile(
                    owner_user_id=user.id,
                    target_roles="Technical Program Manager",
                    target_locations="Edinburgh",
                    salary_min=Decimal("100000"),
                    salary_currency="GBP",
                )
            )
            db.commit()
        login(client, "jobseeker@example.com")

        response = client.get("/focus")

        assert response.status_code == 200
        assert ".app-topbar[data-chip-state=\"hidden\"] .header-context" in response.text
        assert ".app-nav {" in response.text
        assert "overflow: hidden;" in response.text
        assert "@media (max-width: 860px)" in response.text
        assert "overflow-x: auto;" in response.text
        assert 'setState("hidden");' in response.text
    finally:
        app.dependency_overrides.clear()


def test_shell_desktop_contract_uses_internal_content_scroll_panes(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="scrollpane@example.com", password="password")
            db.commit()
        login(client, "scrollpane@example.com")

        response = client.get("/focus")

        assert response.status_code == 200
        html = response.text
        assert "@media (min-width: 861px)" in html
        assert "height: calc(100vh - 68px);" in html
        assert ".app-content-shell {" in html
        assert "flex: 1 1 auto;" in html
        assert "overflow: hidden;" in html
        assert ".page-main,\n      .page-aside {" in html
        assert "overscroll-behavior: contain;" in html
        assert "scrollbar-gutter: stable;" in html
    finally:
        app.dependency_overrides.clear()


def test_shell_contract_pins_user_menu_as_overlay(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            create_local_user(db, email="overlay@example.com", password="password")
            db.commit()
        login(client, "overlay@example.com")

        response = client.get("/inbox")

        assert response.status_code == 200
        html = response.text
        assert ".user-menu {" in html
        assert "position: relative;" in html
        assert ".user-menu-panel {" in html
        assert "position: absolute;" in html
        assert "top: 100%;" in html
        assert "right: 0;" in html
        assert "z-index: 50;" in html
    finally:
        app.dependency_overrides.clear()
