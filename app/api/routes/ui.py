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
      display: grid;
      gap: 12px;
      grid-template-columns: 1fr;
      margin-bottom: 24px;
    }

    .app-topbar > div {
      min-width: 0;
    }

    .app-topbar h1 {
      font-size: 1.5rem;
      font-weight: 500;
      letter-spacing: -0.01em;
      line-height: 1.3;
    }

    .app-brand {
      align-items: center;
      color: var(--accent-strong);
      display: inline-flex;
      gap: 8px;
      font-size: 0.82rem;
      font-weight: 500;
      margin-bottom: 8px;
      text-decoration: none;
    }

    .app-brand-mark {
      border-radius: 6px;
      display: block;
      height: 18px;
      width: 18px;
    }

    .app-subtitle {
      color: var(--muted);
      display: block;
      line-height: 1.45;
      margin-top: 6px;
      max-width: 80ch;
      overflow-wrap: anywhere;
    }

    .app-nav {
      align-items: center;
      display: flex;
      flex-wrap: nowrap;
      gap: 8px;
      justify-content: start;
      max-width: 100%;
      overflow-x: auto;
      padding-bottom: 4px;
      -webkit-overflow-scrolling: touch;
    }

    .app-nav a,
    .app-nav button {
      align-items: center;
      background: transparent;
      border: 0.5px solid var(--line);
      border-radius: 10px;
      color: var(--accent-strong);
      cursor: pointer;
      display: inline-flex;
      font: inherit;
      font-size: 0.92rem;
      font-weight: 500;
      min-height: 34px;
      padding: 0 10px;
      text-decoration: none;
      white-space: nowrap;
    }

    .app-nav form {
      flex: 0 0 auto;
      margin: 0;
    }

    .app-nav a.active {
      background: #E8EBF8;
      border-color: #C3CCF0;
      color: var(--accent);
    }

    .app-nav a.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #ffffff;
    }

    .app-nav a:hover,
    .app-nav button:hover {
      border-color: rgba(0, 0, 0, 0.22);
    }

    @media (max-width: 760px) {
      .app-subtitle {
        max-width: none;
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
        <a class="app-brand" href="/focus">
          <img class="app-brand-mark" src="/favicon.svg" alt="" aria-hidden="true">
          <span>Application Tracker</span>
        </a>
        <h1>{escape(title)}</h1>
        <p class="app-subtitle">{escape(user.email)} · {escape(subtitle)}</p>
      </div>
      <nav class="app-nav" aria-label="Primary navigation">
        {"".join(links)}
        <form method="post" action="/logout">
          <button type="submit">Sign out</button>
        </form>
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
