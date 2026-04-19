from html import escape

from app.db.models.user import User


NavLink = tuple[str, str, str]

PRIMARY_NAV: tuple[NavLink, ...] = (
    ("Focus", "/focus", "focus"),
    ("Inbox", "/inbox", "inbox"),
    ("Board", "/board", "board"),
    ("Artefacts", "/artefacts", "artefacts"),
    ("Capture", "/api/capture/bookmarklet", "capture"),
    ("Settings", "/settings", "settings"),
)


def app_shell_styles() -> str:
    return """
    .app-topbar {
      align-items: start;
      display: grid;
      gap: 16px;
      grid-template-columns: minmax(0, 1fr) auto;
      margin-bottom: 24px;
    }

    .app-brand {
      color: var(--accent-strong);
      display: inline-flex;
      font-size: 0.82rem;
      font-weight: 700;
      margin-bottom: 8px;
      text-decoration: none;
    }

    .app-subtitle {
      color: var(--muted);
      line-height: 1.45;
      margin-top: 6px;
    }

    .app-nav {
      align-items: center;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: end;
    }

    .app-nav a,
    .app-nav button {
      align-items: center;
      background: transparent;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--accent-strong);
      cursor: pointer;
      display: inline-flex;
      font: inherit;
      font-size: 0.92rem;
      font-weight: 600;
      min-height: 34px;
      padding: 0 10px;
      text-decoration: none;
      white-space: nowrap;
    }

    .app-nav a.active {
      background: var(--ink);
      border-color: var(--ink);
      color: #ffffff;
    }

    .app-nav a.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #ffffff;
    }

    @media (max-width: 760px) {
      .app-topbar {
        grid-template-columns: 1fr;
      }

      .app-nav {
        justify-content: start;
        overflow-x: auto;
        padding-bottom: 4px;
      }
    }
    """


def app_header(
    user: User,
    *,
    title: str,
    subtitle: str,
    active: str | None = None,
    actions: tuple[NavLink, ...] = (),
) -> str:
    links = _render_links(actions, active=active, primary=True)
    links.extend(_render_links(PRIMARY_NAV, active=active, primary=False))
    if user.is_admin:
        links.append(_render_link("Admin", "/admin", "admin", active=active, primary=False))

    return f"""
    <header class="app-topbar">
      <div>
        <a class="app-brand" href="/focus">Application Tracker</a>
        <h1>{escape(title)}</h1>
        <p class="app-subtitle">{escape(user.email)} · {escape(subtitle)}</p>
      </div>
      <nav class="app-nav" aria-label="Primary navigation">
        {"".join(links)}
      </nav>
    </header>
    """


def _render_links(
    links: tuple[NavLink, ...],
    *,
    active: str | None,
    primary: bool,
) -> list[str]:
    return [
        _render_link(label, href, key, active=active, primary=primary)
        for label, href, key in links
    ]


def _render_link(
    label: str,
    href: str,
    key: str,
    *,
    active: str | None,
    primary: bool,
) -> str:
    classes = []
    if primary:
        classes.append("primary")
    if active == key:
        classes.append("active")
    class_attr = f' class="{" ".join(classes)}"' if classes else ""
    escaped_href = escape(href, quote=True).replace("&amp;", "&")
    return f'<a{class_attr} href="{escaped_href}">{escape(label)}</a>'
