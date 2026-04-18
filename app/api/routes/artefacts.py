from datetime import datetime
from html import escape
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select

from app.api.deps import DbSession, get_current_user
from app.db.models.artefact import Artefact
from app.db.models.user import User
from app.services.artefacts import get_user_artefact_by_uuid
from app.storage.provider import get_storage_provider

router = APIRouter(tags=["artefacts"])


def _value(value: object) -> str:
    if value is None or value == "":
        return "Not set"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def _size(value: int | None) -> str:
    if value is None:
        return "Size not set"
    if value < 1024:
        return f"{value} bytes"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.1f} MB"


def _artefact_card(artefact: Artefact) -> str:
    job_link = (
        f'<a href="/jobs/{escape(artefact.job.uuid, quote=True)}">{escape(artefact.job.title)}</a>'
        if artefact.job
        else '<span class="muted">No linked job</span>'
    )
    company = artefact.job.company if artefact.job else None
    return f"""
    <article class="artefact-card">
      <div>
        <p class="eyebrow">{escape(artefact.kind)}</p>
        <h2>{escape(artefact.filename)}</h2>
        <p class="meta">{escape(_size(artefact.size_bytes))} · Updated {escape(_value(artefact.updated_at))}</p>
      </div>
      <dl>
        <div>
          <dt>Linked job</dt>
          <dd>{job_link}</dd>
        </div>
        <div>
          <dt>Company</dt>
          <dd>{escape(company or "Not set")}</dd>
        </div>
      </dl>
      <div class="actions">
        <a class="button" href="/artefacts/{escape(artefact.uuid, quote=True)}/download">Download</a>
        {f'<a class="button secondary" href="/jobs/{escape(artefact.job.uuid, quote=True)}">Open job</a>' if artefact.job else ""}
      </div>
    </article>
    """


def render_artefact_library(user: User, artefacts: list[Artefact]) -> HTMLResponse:
    cards = "\n".join(_artefact_card(artefact) for artefact in artefacts)
    if not cards:
        cards = """
        <section class="empty-state">
          <h2>No artefacts yet</h2>
          <p>Upload resumes, cover letters, notes, or prep files from a job workspace.</p>
          <a class="button" href="/board">Find a job workspace</a>
        </section>
        """
    return HTMLResponse(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Artefacts - Application Tracker</title>
  <style>
    :root {{
      color-scheme: light;
      --page: #f9f9f7;
      --panel: #ffffff;
      --ink: #111111;
      --muted: #5f5e5a;
      --line: rgba(0, 0, 0, 0.10);
      --accent: #4f67e4;
      --accent-strong: #2d3a9a;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      background: var(--page);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
    }}

    main {{
      margin: 0 auto;
      max-width: 1120px;
      min-height: 100vh;
      padding: 24px;
    }}

    .topbar {{
      align-items: center;
      display: flex;
      gap: 16px;
      justify-content: space-between;
      margin-bottom: 24px;
    }}

    nav {{
      align-items: center;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}

    h1, h2, p {{
      margin: 0;
    }}

    h1 {{
      font-size: 2rem;
      font-weight: 500;
      letter-spacing: -0.02em;
      line-height: 1.2;
    }}

    h2 {{
      font-size: 1rem;
      font-weight: 500;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }}

    a {{
      color: var(--accent-strong);
      font-weight: 500;
    }}

    .muted,
    .meta,
    .empty-state p {{
      color: var(--muted);
    }}

    .eyebrow,
    dt {{
      color: var(--muted);
      font-size: 0.76rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}

    .library-grid {{
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }}

    .artefact-card,
    .empty-state {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      display: grid;
      gap: 16px;
      padding: 18px;
    }}

    dl {{
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin: 0;
    }}

    dd {{
      margin: 3px 0 0;
      overflow-wrap: anywhere;
    }}

    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}

    .button,
    nav a {{
      border: 1px solid var(--line);
      border-radius: 8px;
      display: inline-flex;
      min-height: 36px;
      padding: 8px 10px;
      text-decoration: none;
    }}

    .button {{
      align-items: center;
      justify-content: center;
    }}

    .button:not(.secondary) {{
      background: var(--accent);
      border-color: var(--accent);
      color: #ffffff;
    }}

    @media (max-width: 760px) {{
      main {{
        padding: 16px;
      }}

      .topbar,
      .library-grid,
      dl {{
        align-items: start;
        display: grid;
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header class="topbar">
      <div>
        <h1>Artefacts</h1>
        <p class="muted">{escape(user.email)} · Resumes, cover letters, notes, and prep files</p>
      </div>
      <nav>
        <a href="/focus">Focus</a>
        <a href="/inbox">Inbox</a>
        <a href="/board">Board</a>
        <a href="/jobs/new">Add job</a>
      </nav>
    </header>

    <div class="library-grid">
      {cards}
    </div>
  </main>
</body>
</html>"""
    )


@router.get("/artefacts", response_class=HTMLResponse, include_in_schema=False)
def artefact_library(
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> HTMLResponse:
    artefacts = list(
        db.scalars(
            select(Artefact)
            .where(Artefact.owner_user_id == current_user.id)
            .order_by(Artefact.updated_at.desc(), Artefact.created_at.desc())
        )
    )
    return render_artefact_library(current_user, artefacts)


@router.get("/artefacts/{artefact_uuid}/download", include_in_schema=False)
def download_artefact(
    artefact_uuid: str,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    artefact = get_user_artefact_by_uuid(db, current_user, artefact_uuid)
    if artefact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    content = get_storage_provider().load(artefact.storage_key)
    filename = quote(artefact.filename)
    return Response(
        content=content,
        media_type=artefact.content_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
