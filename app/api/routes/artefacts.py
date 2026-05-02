from datetime import UTC, date, datetime
from html import escape
import re
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.api.deps import DbSession, get_current_user
from app.api.routes.ui import compact_content_rhythm_styles, render_shell_page
from app.db.models.artefact import Artefact
from app.db.models.user import User
from app.services.artefacts import (
    get_user_artefact_by_uuid,
    get_artefact_markdown_access,
    list_user_artefacts,
    update_artefact_metadata,
)
from app.services.markdown import render_markdown_blocks
from app.storage.provider import get_storage_provider

router = APIRouter(tags=["artefacts"])

_DRAFT_OUTPUT_ID_RE = re.compile(r"Saved from AI draft output #(\d+)\.")
_BASELINE_UUID_RE = re.compile(r"Baseline artefact UUID: ([0-9a-f-]+)\.")
_GENERATION_BRIEF_RE = re.compile(r"Generation brief: (.+?)\.")


def _value(value: object) -> str:
    if value is None or value == "":
        return "Not set"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def _date_value(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.date().isoformat()


def _parse_follow_up_date(value: str) -> datetime | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        parsed = date.fromisoformat(cleaned)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Follow-up date must be a valid date",
        ) from exc
    return datetime(parsed.year, parsed.month, parsed.day, tzinfo=UTC)


def _size(value: int | None) -> str:
    if value is None:
        return "Size not set"
    if value < 1024:
        return f"{value} bytes"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.1f} MB"


def _artefact_provenance(artefact: Artefact, artefact_lookup: dict[str, Artefact]) -> str:
    notes = artefact.notes or ""
    if "Saved from AI draft output #" not in notes:
        return ""
    output_match = _DRAFT_OUTPUT_ID_RE.search(notes)
    baseline_match = _BASELINE_UUID_RE.search(notes)
    items: list[str] = []
    if output_match:
        items.append(f"<li>Saved from AI draft output #{escape(output_match.group(1))}</li>")
    if baseline_match:
        baseline_uuid = baseline_match.group(1)
        baseline = artefact_lookup.get(baseline_uuid)
        if baseline is not None:
            items.append(
                f'<li>Baseline artefact: <a href="/artefacts/{escape(baseline.uuid, quote=True)}/download">'
                f"{escape(baseline.filename)}</a></li>"
            )
        else:
            items.append(f"<li>Baseline artefact UUID: {escape(baseline_uuid)}</li>")
    brief_match = _GENERATION_BRIEF_RE.search(notes)
    if brief_match:
        items.append(f"<li>Generation brief: {escape(brief_match.group(1))}</li>")
    if not items:
        return ""
    return (
        '<div class="provenance-block">'
        '<p class="eyebrow">Provenance</p>'
        '<ul class="provenance-list">' + "".join(items) + "</ul>"
        "</div>"
    )


def _artefact_card(artefact: Artefact, artefact_lookup: dict[str, Artefact]) -> str:
    linked_jobs = {link.job.id: link.job for link in artefact.job_links}
    if artefact.job:
        linked_jobs[artefact.job.id] = artefact.job
    job_links = "\n".join(
        f'<li><a href="/jobs/{escape(job.uuid, quote=True)}">{escape(job.title)}</a>'
        f'<span>{escape(job.company or "Company not set")}</span></li>'
        for job in sorted(linked_jobs.values(), key=lambda item: item.title.lower())
    )
    if not job_links:
        job_links = '<li><span class="muted">No linked jobs</span></li>'
    purpose = artefact.purpose or "Purpose not set"
    version = artefact.version_label or "Version not set"
    follow_up = _value(artefact.follow_up_at) if artefact.follow_up_at else "No follow-up scheduled"
    notes = f"<p>{escape(artefact.notes)}</p>" if artefact.notes else ""
    provenance = _artefact_provenance(artefact, artefact_lookup)
    return f"""
    <article class="artefact-card">
      <div>
        <p class="eyebrow">{escape(artefact.kind)}</p>
        <h2><a href="/artefacts/{escape(artefact.uuid, quote=True)}">{escape(artefact.filename)}</a></h2>
        <p class="meta">{escape(_size(artefact.size_bytes))} · Updated {escape(_value(artefact.updated_at))}</p>
      </div>
      <dl>
        <div>
          <dt>Purpose</dt>
          <dd>{escape(purpose)}</dd>
        </div>
        <div>
          <dt>Version</dt>
          <dd>{escape(version)}</dd>
        </div>
        <div>
          <dt>Follow-up</dt>
          <dd>{escape(follow_up)}</dd>
        </div>
      </dl>
      {notes}
      {provenance}
      <div>
        <p class="eyebrow">Linked jobs</p>
        <ol class="linked-jobs">{job_links}</ol>
      </div>
      <details>
        <summary>Edit metadata</summary>
        <form class="metadata-form" method="post" action="/artefacts/{escape(artefact.uuid, quote=True)}/metadata">
          <label>
            Kind
            <input name="kind" value="{escape(artefact.kind, quote=True)}" maxlength="100">
          </label>
          <label>
            Purpose
            <input name="purpose" value="{escape(artefact.purpose or "", quote=True)}" maxlength="300" placeholder="Tailored resume, cover letter, interview prep">
          </label>
          <label>
            Version label
            <input name="version_label" value="{escape(artefact.version_label or "", quote=True)}" maxlength="100" placeholder="Product roles v2">
          </label>
          <label>
            Outcome context
            <input name="outcome_context" value="{escape(artefact.outcome_context or "", quote=True)}" maxlength="300" placeholder="Used for interview invite, rejected, offer">
          </label>
          <label>
            Follow-up date
            <input name="follow_up_at" type="date" value="{escape(_date_value(artefact.follow_up_at), quote=True)}">
          </label>
          <label>
            Notes
            <textarea name="notes" rows="3">{escape(artefact.notes or "")}</textarea>
          </label>
          <button type="submit">Save metadata</button>
        </form>
      </details>
      <div class="actions">
        <a class="button secondary" href="/artefacts/{escape(artefact.uuid, quote=True)}">Open</a>
        <a class="button" href="/artefacts/{escape(artefact.uuid, quote=True)}/download">Download</a>
      </div>
    </article>
    """


def _artefact_preview_panel(artefact: Artefact) -> str:
    access = get_artefact_markdown_access(artefact)
    if access.markdown_text is None:
        return """
        <section class="artefact-preview empty-state" data-ui-component="artefact-preview-unavailable">
          <h2>No internal text preview yet</h2>
          <p>Download the source file to inspect the original document. A Markdown preview is only available for supported text and extracted-document types.</p>
        </section>
        """

    warning = f'<p class="warning">{escape(access.warning)}</p>' if access.warning else ""
    return f"""
    <section class="artefact-preview" data-ui-component="artefact-preview">
      <div class="panel-header">
        <div>
          <p class="panel-micro">{escape(access.source_label)}</p>
          <h2>Markdown view</h2>
        </div>
        <span class="status-pill accent">{escape(access.confidence_label)}</span>
      </div>
      {warning}
      {render_markdown_blocks(access.markdown_text, class_name="artefact-markdown")}
    </section>
    """


def _artefact_detail_context(artefact: Artefact) -> str:
    linked_jobs = {link.job.id: link.job for link in artefact.job_links}
    if artefact.job:
        linked_jobs[artefact.job.id] = artefact.job
    linked_jobs_html = "".join(
        f'<li><a href="/jobs/{escape(job.uuid, quote=True)}">{escape(job.title)}</a>'
        f' <span>{escape(job.company or "Company not set")}</span></li>'
        for job in sorted(linked_jobs.values(), key=lambda item: item.title.lower())
    )
    if not linked_jobs_html:
        linked_jobs_html = '<li><span class="muted">No linked jobs</span></li>'
    return f"""
    <section class="artefact-context" data-ui-component="artefact-detail-meta">
      <div class="context-grid">
        <div><dt>Kind</dt><dd>{escape(artefact.kind)}</dd></div>
        <div><dt>Source file</dt><dd>{escape(artefact.filename)}</dd></div>
        <div><dt>Content type</dt><dd>{escape(artefact.content_type or "Not set")}</dd></div>
        <div><dt>Size</dt><dd>{escape(_size(artefact.size_bytes))}</dd></div>
        <div><dt>Purpose</dt><dd>{escape(artefact.purpose or "Not set")}</dd></div>
        <div><dt>Version</dt><dd>{escape(artefact.version_label or "Not set")}</dd></div>
      </div>
      <div class="context-block">
        <p class="eyebrow">Notes</p>
        <p>{escape(artefact.notes or "No notes")}</p>
      </div>
      <div class="context-block">
        <p class="eyebrow">Linked jobs</p>
        <ol class="linked-jobs">{linked_jobs_html}</ol>
      </div>
    </section>
    """


def render_artefact_library(user: User, artefacts: list[Artefact]) -> HTMLResponse:
    artefact_lookup = {artefact.uuid: artefact for artefact in artefacts}
    cards = "\n".join(_artefact_card(artefact, artefact_lookup) for artefact in artefacts)
    if not cards:
        cards = """
        <section class="empty-state">
          <h2>No artefacts yet</h2>
          <p>Upload resumes, cover letters, notes, or prep files from a job workspace.</p>
          <a class="button" href="/board">Find a job workspace</a>
        </section>
        """
    extra_styles = compact_content_rhythm_styles() + """
    h2 { overflow-wrap: anywhere; }
    .muted, .meta, .empty-state p { color: var(--muted); }
    .eyebrow, dt {
      color: var(--muted);
      font-size: 0.76rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .library-grid {
      align-items: start;
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .artefact-card, .empty-state {
      background: var(--panel);
      border: 0.5px solid var(--line);
      border-radius: 14px;
      display: grid;
      gap: 16px;
      padding: 18px;
    }
    dl {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin: 0;
    }
    dd { margin: 3px 0 0; overflow-wrap: anywhere; }
    details { border-top: 0.5px solid var(--line); padding-top: 12px; }
    summary { color: var(--accent-strong); cursor: pointer; font-weight: 500; }
    .metadata-form { gap: 8px; }
    label { color: var(--muted); font-size: 0.86rem; }
    input, textarea {
      border: 0.5px solid var(--line);
      border-radius: 10px;
      color: var(--ink);
      font: inherit;
      padding: 8px 10px;
      width: 100%;
    }
    .linked-jobs {
      display: grid;
      gap: 8px;
      list-style: none;
      margin: 8px 0 0;
      padding: 0;
    }
    .linked-jobs li { display: grid; gap: 2px; }
    .linked-jobs span { color: var(--muted); }
    .provenance-block {
      border-top: 0.5px solid var(--line);
      display: grid;
      gap: 8px;
      padding-top: 12px;
    }
    .provenance-list {
      display: grid;
      gap: 6px;
      list-style: none;
      margin: 0;
      padding: 0;
    }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; }
    .button, button {
      border: 0.5px solid var(--line);
      border-radius: 10px;
      display: inline-flex;
      font: inherit;
      font-weight: 500;
      min-height: 36px;
      padding: 8px 10px;
      text-decoration: none;
    }
    .button, button { align-items: center; cursor: pointer; justify-content: center; }
    .button:not(.secondary), button {
      background: var(--accent);
      border-color: var(--accent);
      color: #ffffff;
    }
    @media (max-width: 760px) {
      .library-grid, dl { grid-template-columns: 1fr; }
      .actions, .actions .button { width: 100%; }
    }
    """
    body = f"""
    <div class="library-grid">
      {cards}
    </div>
    """
    return HTMLResponse(
        render_shell_page(
            user,
            page_title="Artefacts",
            title="Artefacts",
            subtitle="",
            active="artefacts",
            actions=(("Add job", "/jobs/new", "add-job"),),
            body=body,
            container="wide",
            extra_styles=extra_styles,
        )
    )


@router.get("/artefacts", response_class=HTMLResponse, include_in_schema=False)
def artefact_library(
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> HTMLResponse:
    return render_artefact_library(current_user, list_user_artefacts(db, current_user))


@router.get("/artefacts/{artefact_uuid}", response_class=HTMLResponse, include_in_schema=False)
def artefact_detail(
    artefact_uuid: str,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> HTMLResponse:
    artefact = get_user_artefact_by_uuid(db, current_user, artefact_uuid)
    if artefact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    artefact_lookup = {artefact.uuid: artefact}
    provenance = _artefact_provenance(artefact, artefact_lookup)
    body = f"""
    <div class="artefact-detail-layout">
      <section class="artefact-source-card" data-ui-component="artefact-source-card">
        <div class="panel-header">
          <div>
            <p class="panel-micro">Source remains canonical</p>
            <h2>{escape(artefact.filename)}</h2>
          </div>
          <span class="status-pill accent">{escape(artefact.kind)}</span>
        </div>
        <p class="meta">Download the original file whenever you need the exact source document.</p>
        <div class="actions">
          <a class="button" href="/artefacts/{escape(artefact.uuid, quote=True)}/download">Download source</a>
          <a class="button secondary" href="/artefacts">Back to library</a>
        </div>
        {provenance}
      </section>
      {_artefact_detail_context(artefact)}
      {_artefact_preview_panel(artefact)}
    </div>
    """
    extra_styles = compact_content_rhythm_styles() + """
    .muted, .meta { color: var(--muted); }
    .artefact-detail-layout {
      display: grid;
      gap: 16px;
    }
    .artefact-source-card, .artefact-context, .artefact-preview, .empty-state {
      background: var(--panel);
      border: 0.5px solid var(--line);
      border-radius: 14px;
      display: grid;
      gap: 14px;
      padding: 18px;
    }
    .context-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .context-grid dt, .context-block .eyebrow {
      color: var(--muted);
      font-size: 0.76rem;
      letter-spacing: 0.04em;
      margin: 0 0 4px;
      text-transform: uppercase;
    }
    .context-grid dd { margin: 0; overflow-wrap: anywhere; }
    .context-block { display: grid; gap: 6px; }
    .warning {
      background: color-mix(in srgb, var(--warning-soft) 40%, white);
      border: 0.5px solid color-mix(in srgb, var(--warning) 28%, var(--line));
      border-radius: 10px;
      margin: 0;
      padding: 10px 12px;
    }
    .artefact-markdown {
      display: grid;
      gap: 10px;
    }
    .artefact-markdown h2, .artefact-markdown h3, .artefact-markdown h4,
    .artefact-markdown p, .artefact-markdown ul { margin: 0; }
    .artefact-markdown ul { padding-left: 18px; }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; }
    .button.secondary {
      background: transparent;
      border-color: var(--line);
      color: var(--ink);
    }
    @media (max-width: 760px) {
      .context-grid { grid-template-columns: 1fr; }
      .actions, .actions .button { width: 100%; }
    }
    """
    return HTMLResponse(
        render_shell_page(
            current_user,
            page_title=artefact.filename,
            title=artefact.filename,
            subtitle="",
            active="artefacts",
            actions=(("Back to artefacts", "/artefacts", "artefacts"),),
            body=body,
            container="wide",
            extra_styles=extra_styles,
        )
    )


@router.post("/artefacts/{artefact_uuid}/metadata", include_in_schema=False)
def update_artefact_metadata_form(
    artefact_uuid: str,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    kind: Annotated[str, Form()] = "other",
    purpose: Annotated[str, Form()] = "",
    version_label: Annotated[str, Form()] = "",
    notes: Annotated[str, Form()] = "",
    outcome_context: Annotated[str, Form()] = "",
    follow_up_at: Annotated[str, Form()] = "",
) -> RedirectResponse:
    artefact = get_user_artefact_by_uuid(db, current_user, artefact_uuid)
    if artefact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    update_artefact_metadata(
        artefact,
        kind=kind,
        purpose=purpose,
        version_label=version_label,
        notes=notes,
        outcome_context=outcome_context,
        follow_up_at=_parse_follow_up_date(follow_up_at),
        update_follow_up=True,
    )
    db.commit()
    return RedirectResponse(url="/artefacts", status_code=status.HTTP_303_SEE_OTHER)


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
