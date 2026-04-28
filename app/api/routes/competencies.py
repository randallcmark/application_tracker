from datetime import datetime
from html import escape
import re
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from app.api.deps import DbSession, get_current_user
from app.api.routes.ui import compact_content_rhythm_styles, render_shell_page
from app.db.models.ai_output import AiOutput
from app.db.models.artefact import Artefact
from app.db.models.competency_evidence import CompetencyEvidence
from app.db.models.job import Job
from app.db.models.user import User
from app.services.ai import AiExecutionError, generate_competency_star_shaping
from app.services.artefacts import get_user_artefact_by_uuid
from app.services.competency_evidence import (
    create_competency_evidence,
    get_user_competency_evidence_by_uuid,
    list_competency_evidence,
    update_competency_evidence,
)
from app.services.jobs import get_user_job_by_uuid
from app.services.profiles import get_user_profile

router = APIRouter(tags=["competencies"])


def _value(value: object) -> str:
    if value is None or value == "":
        return "Not set"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def _result_snippet(evidence: CompetencyEvidence) -> str:
    if evidence.result:
        return evidence.result
    if evidence.action:
        return evidence.action
    if evidence.situation:
        return evidence.situation
    return "Result not captured yet"


def _tag_list(tags: str | None) -> str:
    if not tags:
        return '<span class="muted">No tags</span>'
    items = [item.strip() for item in tags.split(",") if item.strip()]
    if not items:
        return '<span class="muted">No tags</span>'
    return "".join(f'<span class="tag">{escape(item)}</span>' for item in items)


def _source_signal(evidence: CompetencyEvidence) -> str:
    if evidence.source_job is not None:
        return f'Source role: <a href="/jobs/{escape(evidence.source_job.uuid, quote=True)}">{escape(evidence.source_job.title)}</a>'
    if evidence.source_artefact is not None:
        return f'Source artefact: <a href="/artefacts/{escape(evidence.source_artefact.uuid, quote=True)}/download">{escape(evidence.source_artefact.filename)}</a>'
    if evidence.source_ai_output is not None:
        return f"Source AI output #{evidence.source_ai_output.id}"
    return "Manual entry"


def _strength_options(current: str) -> str:
    return "".join(
        f'<option value="{value}"{" selected" if current == value else ""}>{label}</option>'
        for value, label in (
            ("seed", "Seed"),
            ("working", "Working"),
            ("strong", "Strong"),
        )
    )


def _render_inline_markdown(text: str) -> str:
    escaped = escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"<em>\1</em>", escaped)
    return escaped


def _render_markdown_blocks(text: str, *, class_name: str = "ai-markdown") -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("### "):
            blocks.append(f"<h4>{_render_inline_markdown(line[4:])}</h4>")
            i += 1
            continue
        if line.startswith("## "):
            blocks.append(f"<h3>{_render_inline_markdown(line[3:])}</h3>")
            i += 1
            continue
        if line.startswith("# "):
            blocks.append(f"<h2>{_render_inline_markdown(line[2:])}</h2>")
            i += 1
            continue
        if line.startswith(("* ", "- ")):
            items: list[str] = []
            while i < len(lines):
                bullet = lines[i].strip()
                if not bullet.startswith(("* ", "- ")):
                    break
                items.append(f"<li>{_render_inline_markdown(bullet[2:])}</li>")
                i += 1
            blocks.append("<ul>" + "".join(items) + "</ul>")
            continue
        paragraph_lines: list[str] = []
        while i < len(lines):
            paragraph = lines[i].strip()
            if not paragraph:
                break
            if paragraph.startswith(("# ", "## ", "### ", "* ", "- ")):
                break
            paragraph_lines.append(paragraph)
            i += 1
        blocks.append(f"<p>{_render_inline_markdown(' '.join(paragraph_lines))}</p>")
    return f'<div class="{escape(class_name, quote=True)}">' + "".join(blocks) + "</div>"


def _latest_competency_ai_outputs(
    db: DbSession,
    user: User,
) -> dict[str, AiOutput]:
    outputs = db.scalars(
        select(AiOutput)
        .where(
            AiOutput.owner_user_id == user.id,
            AiOutput.output_type == "competency_star_shaping",
            AiOutput.status == "active",
        )
        .order_by(AiOutput.updated_at.desc(), AiOutput.created_at.desc())
    )
    by_evidence_uuid: dict[str, AiOutput] = {}
    for output in outputs:
        source_context = output.source_context or {}
        evidence_uuid = source_context.get("competency_evidence_uuid")
        if isinstance(evidence_uuid, str) and evidence_uuid and evidence_uuid not in by_evidence_uuid:
            by_evidence_uuid[evidence_uuid] = output
    return by_evidence_uuid


def _ai_shaping_panel(output: AiOutput | None) -> str:
    if output is None:
        return '<p class="muted">No STAR shaping output yet.</p>'
    provider = output.model_name or output.provider or "AI"
    return f"""
    <article class="ai-shaping-card" data-ui-component="competency-star-shaping-output">
      <div>
        <p class="eyebrow">AI shaping</p>
        <h3>{escape(output.title or "AI STAR shaping")}</h3>
        <p class="meta">From {escape(provider)} · Updated {escape(_value(output.updated_at))}</p>
      </div>
      {_render_markdown_blocks(output.body)}
    </article>
    """


def _evidence_card(evidence: CompetencyEvidence, ai_output: AiOutput | None = None) -> str:
    return f"""
    <article class="evidence-card" data-ui-component="competency-evidence-card">
      <div class="evidence-card-head">
        <div>
          <p class="eyebrow">{escape(evidence.competency or "Competency not set")}</p>
          <h2>{escape(evidence.title)}</h2>
        </div>
        <span class="strength-pill strength-{escape(evidence.strength)}">{escape(evidence.strength.title())}</span>
      </div>
      <p class="result-line">{escape(_result_snippet(evidence))}</p>
      <div class="tag-row">{_tag_list(evidence.tags)}</div>
      <p class="meta">{_source_signal(evidence)} · Updated {escape(_value(evidence.updated_at))}</p>
      <details>
        <summary>STAR detail</summary>
        <dl class="star-grid">
          <div><dt>Situation</dt><dd>{escape(evidence.situation or "Not captured")}</dd></div>
          <div><dt>Task</dt><dd>{escape(evidence.task or "Not captured")}</dd></div>
          <div><dt>Action</dt><dd>{escape(evidence.action or "Not captured")}</dd></div>
          <div><dt>Result</dt><dd>{escape(evidence.result or "Not captured")}</dd></div>
        </dl>
        {f'<p class="notes">{escape(evidence.evidence_notes)}</p>' if evidence.evidence_notes else ""}
      </details>
      <details>
        <summary>Refine with prompts</summary>
        <form class="evidence-form" method="post" action="/competencies/{escape(evidence.uuid, quote=True)}">
          {_evidence_form_fields(evidence)}
          <button type="submit">Save evidence</button>
        </form>
      </details>
      <details>
        <summary>Shape with AI</summary>
        <form class="inline-action-form" method="post" action="/competencies/{escape(evidence.uuid, quote=True)}/star-shaping">
          <button type="submit">Generate STAR shaping</button>
        </form>
        <p class="muted">AI creates visible guidance only. It does not edit this evidence.</p>
        {_ai_shaping_panel(ai_output)}
      </details>
    </article>
    """


def _prefill_from_source(source_job: Job | None, source_artefact: Artefact | None) -> dict[str, str]:
    if source_artefact is not None:
        return {
            "title": f"Evidence from {source_artefact.filename}",
            "competency": "",
            "evidence_notes": f"Source artefact: {source_artefact.filename}",
            "tags": "artefact evidence",
            "source_kind": "artefact",
            "source_artefact_uuid": source_artefact.uuid,
        }
    if source_job is not None:
        role = source_job.title or "role"
        company = f" at {source_job.company}" if source_job.company else ""
        return {
            "title": f"Evidence for {role}",
            "competency": "",
            "evidence_notes": f"Source role: {role}{company}",
            "tags": "role evidence",
            "source_kind": "job",
            "source_job_uuid": source_job.uuid,
        }
    return {}


def _source_prefill_panel(source_job: Job | None, source_artefact: Artefact | None) -> str:
    if source_artefact is not None:
        return (
            '<div class="source-prefill" data-ui-component="competency-source-prefill">'
            "<strong>Source context</strong>"
            f"<span>Artefact: {escape(source_artefact.filename)}</span>"
            "</div>"
        )
    if source_job is not None:
        company = f" · {escape(source_job.company)}" if source_job.company else ""
        return (
            '<div class="source-prefill" data-ui-component="competency-source-prefill">'
            "<strong>Source context</strong>"
            f"<span>Role: {escape(source_job.title)}{company}</span>"
            "</div>"
        )
    return ""


def _evidence_form_fields(
    evidence: CompetencyEvidence | None = None,
    *,
    defaults: dict[str, str] | None = None,
) -> str:
    defaults = defaults or {}
    title = evidence.title if evidence is not None else ""
    competency = evidence.competency if evidence is not None else ""
    strength = evidence.strength if evidence is not None else "seed"
    situation = evidence.situation if evidence is not None else ""
    task = evidence.task if evidence is not None else ""
    action = evidence.action if evidence is not None else ""
    result = evidence.result if evidence is not None else ""
    evidence_notes = evidence.evidence_notes if evidence is not None else ""
    tags = evidence.tags if evidence is not None else ""
    source_kind = defaults.get("source_kind", "")
    source_job_uuid = defaults.get("source_job_uuid", "")
    source_artefact_uuid = defaults.get("source_artefact_uuid", "")
    if evidence is None:
        title = defaults.get("title", title or "")
        competency = defaults.get("competency", competency or "")
        evidence_notes = defaults.get("evidence_notes", evidence_notes or "")
        tags = defaults.get("tags", tags or "")
    return f"""
    <input type="hidden" name="source_kind" value="{escape(source_kind, quote=True)}">
    <input type="hidden" name="source_job_uuid" value="{escape(source_job_uuid, quote=True)}">
    <input type="hidden" name="source_artefact_uuid" value="{escape(source_artefact_uuid, quote=True)}">
    <fieldset class="prompt-group" data-ui-component="competency-prompt-theme">
      <legend>1. Theme</legend>
      <label>What competency or theme does this example demonstrate?
        <input name="competency" value="{escape(competency or "", quote=True)}" maxlength="200" placeholder="Delivery leadership">
      </label>
      <label>What short title will help you find it again?
        <input name="title" value="{escape(title or "", quote=True)}" maxlength="200" required placeholder="Platform migration recovery">
      </label>
    </fieldset>
    <fieldset class="prompt-group" data-ui-component="competency-prompt-star">
      <legend>2. STAR evidence</legend>
      <label>What was the situation?
        <textarea name="situation" rows="2">{escape(situation or "")}</textarea>
      </label>
      <label>What were you responsible for?
        <textarea name="task" rows="2">{escape(task or "")}</textarea>
      </label>
      <label>What did you do?
        <textarea name="action" rows="3">{escape(action or "")}</textarea>
      </label>
      <label>What changed as a result?
        <textarea name="result" rows="2">{escape(result or "")}</textarea>
      </label>
    </fieldset>
    <fieldset class="prompt-group" data-ui-component="competency-prompt-credibility">
      <legend>3. Credibility</legend>
      <label>What makes this credible?
        <textarea name="evidence_notes" rows="2">{escape(evidence_notes or "")}</textarea>
      </label>
      <label>How ready is this example?
        <select name="strength">{_strength_options(strength or "seed")}</select>
      </label>
    </fieldset>
    <fieldset class="prompt-group" data-ui-component="competency-prompt-reuse">
      <legend>4. Reuse</legend>
      <label>Where is this most useful?
        <input name="tags" value="{escape(tags or "", quote=True)}" placeholder="leadership, platform, stakeholders">
      </label>
    </fieldset>
    """


def _flash_message(message: str, *, tone: str) -> str:
    return f'<div class="flash {escape(tone, quote=True)}">{escape(message)}</div>'


def render_competency_library(
    user: User,
    evidence_items: list[CompetencyEvidence],
    *,
    ai_outputs_by_evidence_uuid: dict[str, AiOutput] | None = None,
    ai_error: str | None = None,
    ai_status: str | None = None,
    source_job: Job | None = None,
    source_artefact: Artefact | None = None,
) -> HTMLResponse:
    ai_outputs_by_evidence_uuid = ai_outputs_by_evidence_uuid or {}
    cards = "\n".join(
        _evidence_card(evidence, ai_outputs_by_evidence_uuid.get(evidence.uuid))
        for evidence in evidence_items
    )
    if not cards:
        cards = """
        <section class="empty-state">
          <h2>No competency evidence yet</h2>
          <p>Capture reusable STAR examples for interviews and written applications.</p>
        </section>
        """
    extra_styles = compact_content_rhythm_styles() + """
    h2 { overflow-wrap: anywhere; }
    .muted, .meta, .empty-state p { color: var(--muted); }
    .flash {
      border: 0.5px solid var(--line);
      border-radius: 8px;
      margin-bottom: 12px;
      padding: 10px 12px;
    }
    .flash.success { background: var(--success-soft); color: var(--success); }
    .flash.error { background: var(--danger-soft); color: var(--danger); }
    .source-prefill {
      background: var(--accent-soft);
      border: 0.5px solid var(--line);
      border-radius: 8px;
      color: var(--accent-strong);
      display: grid;
      gap: 4px;
      padding: 10px;
    }
    .source-prefill span { color: var(--muted); }
    .eyebrow, dt {
      color: var(--muted);
      font-size: 0.76rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .evidence-layout {
      align-items: start;
      display: grid;
      gap: 14px;
      grid-template-columns: minmax(0, 1fr) 360px;
    }
    .evidence-grid {
      align-items: start;
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .evidence-card, .empty-state, .create-panel, .ai-shaping-card {
      background: var(--panel);
      border: 0.5px solid var(--line);
      border-radius: 8px;
      display: grid;
      gap: 14px;
      padding: 16px;
    }
    .evidence-card-head {
      align-items: start;
      display: flex;
      gap: 12px;
      justify-content: space-between;
    }
    .result-line {
      color: var(--ink);
      line-height: 1.45;
    }
    .strength-pill, .tag {
      align-items: center;
      border-radius: 999px;
      display: inline-flex;
      font-size: 0.78rem;
      min-height: 24px;
      padding: 0 9px;
    }
    .strength-pill { background: var(--accent-soft); color: var(--accent-strong); font-weight: 600; }
    .strength-strong { background: var(--success-soft); color: var(--success); }
    .strength-working { background: var(--amber-soft); color: var(--amber); }
    .tag-row { display: flex; flex-wrap: wrap; gap: 6px; }
    .tag { background: var(--surface-muted); color: var(--muted); }
    details { border-top: 0.5px solid var(--line); padding-top: 10px; }
    summary { color: var(--accent-strong); cursor: pointer; font-weight: 500; }
    .star-grid {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin: 12px 0 0;
    }
    dd { margin: 3px 0 0; overflow-wrap: anywhere; }
    .notes { color: var(--muted); margin-top: 12px; }
    .evidence-form { display: grid; gap: 12px; }
    .prompt-group {
      border: 0.5px solid var(--line);
      border-radius: 8px;
      display: grid;
      gap: 10px;
      margin: 0;
      padding: 10px;
    }
    legend {
      color: var(--accent-strong);
      font-size: 0.82rem;
      font-weight: 600;
      padding: 0 4px;
    }
    label { color: var(--muted); display: grid; font-size: 0.86rem; gap: 6px; }
    input, select, textarea {
      border: 0.5px solid var(--line);
      border-radius: 8px;
      color: var(--ink);
      font: inherit;
      padding: 8px 10px;
      width: 100%;
    }
    button {
      background: var(--accent);
      border: 0.5px solid var(--accent);
      border-radius: 8px;
      color: #ffffff;
      cursor: pointer;
      font: inherit;
      font-weight: 500;
      min-height: 36px;
      padding: 8px 10px;
    }
    .inline-action-form { margin: 10px 0; }
    .ai-markdown { display: grid; gap: 8px; }
    .ai-markdown h2, .ai-markdown h3, .ai-markdown h4,
    .ai-markdown p, .ai-markdown ul { margin: 0; }
    .ai-markdown ul { padding-left: 18px; }
    @media (max-width: 980px) {
      .evidence-layout, .evidence-grid, .star-grid { grid-template-columns: 1fr; }
    }
    """
    flash = ""
    if ai_error:
        flash = _flash_message(ai_error, tone="error")
    elif ai_status:
        flash = _flash_message(ai_status, tone="success")
    body = f"""
    {flash}
    <div class="evidence-layout" data-ui-component="competency-evidence-library">
      <section class="evidence-grid">
        {cards}
      </section>
      <aside class="create-panel" data-ui-component="competency-evidence-create">
        <div>
          <p class="eyebrow">New evidence</p>
          <h2>Add competency evidence</h2>
        </div>
        {_source_prefill_panel(source_job, source_artefact)}
        <form class="evidence-form" method="post" action="/competencies">
          {_evidence_form_fields(defaults=_prefill_from_source(source_job, source_artefact))}
          <button type="submit">Add evidence</button>
        </form>
      </aside>
    </div>
    """
    return HTMLResponse(
        render_shell_page(
            user,
            page_title="Competency Evidence",
            title="Competency Evidence",
            subtitle="Reusable STAR examples for interviews and written applications",
            active="competencies",
            actions=(("Artefacts", "/artefacts", "artefacts"),),
            body=body,
            kicker="Evidence library",
            container="wide",
            extra_styles=extra_styles,
        )
    )


@router.get("/competencies", response_class=HTMLResponse, include_in_schema=False)
def competency_library(
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    ai_error: Annotated[str | None, Query()] = None,
    ai_status: Annotated[str | None, Query()] = None,
    source_job_uuid: Annotated[str | None, Query()] = None,
    source_artefact_uuid: Annotated[str | None, Query()] = None,
) -> HTMLResponse:
    source_job = get_user_job_by_uuid(db, current_user, source_job_uuid) if source_job_uuid else None
    source_artefact = (
        get_user_artefact_by_uuid(db, current_user, source_artefact_uuid)
        if source_artefact_uuid
        else None
    )
    return render_competency_library(
        current_user,
        list_competency_evidence(db, current_user),
        ai_outputs_by_evidence_uuid=_latest_competency_ai_outputs(db, current_user),
        ai_error=ai_error,
        ai_status=ai_status,
        source_job=source_job,
        source_artefact=source_artefact,
    )


@router.post("/competencies", include_in_schema=False)
def create_competency_evidence_form(
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    title: Annotated[str, Form()] = "",
    competency: Annotated[str, Form()] = "",
    situation: Annotated[str, Form()] = "",
    task: Annotated[str, Form()] = "",
    action: Annotated[str, Form()] = "",
    result: Annotated[str, Form()] = "",
    evidence_notes: Annotated[str, Form()] = "",
    strength: Annotated[str, Form()] = "seed",
    tags: Annotated[str, Form()] = "",
    source_kind: Annotated[str, Form()] = "",
    source_job_uuid: Annotated[str, Form()] = "",
    source_artefact_uuid: Annotated[str, Form()] = "",
) -> RedirectResponse:
    source_job = get_user_job_by_uuid(db, current_user, source_job_uuid.strip()) if source_job_uuid.strip() else None
    source_artefact = (
        get_user_artefact_by_uuid(db, current_user, source_artefact_uuid.strip())
        if source_artefact_uuid.strip()
        else None
    )
    cleaned_source_kind = source_kind.strip() if source_kind.strip() in {"job", "artefact"} else "manual"
    if cleaned_source_kind == "job" and source_job is None:
        raise HTTPException(status_code=404, detail="Source job not found")
    if cleaned_source_kind == "artefact" and source_artefact is None:
        raise HTTPException(status_code=404, detail="Source artefact not found")
    try:
        create_competency_evidence(
            db,
            current_user,
            title=title,
            competency=competency,
            situation=situation,
            task=task,
            action=action,
            result=result,
            evidence_notes=evidence_notes,
            strength=strength,
            tags=tags,
            source_kind=cleaned_source_kind,
            source_job=source_job if cleaned_source_kind == "job" else None,
            source_artefact=source_artefact if cleaned_source_kind == "artefact" else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return RedirectResponse(url="/competencies", status_code=303)


@router.post("/competencies/{evidence_uuid}/star-shaping", include_in_schema=False)
def create_competency_star_shaping_route(
    evidence_uuid: str,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> RedirectResponse:
    evidence = get_user_competency_evidence_by_uuid(db, current_user, evidence_uuid)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Competency evidence not found")
    try:
        generate_competency_star_shaping(
            db,
            current_user,
            evidence,
            profile=get_user_profile(db, current_user),
        )
    except AiExecutionError as exc:
        db.rollback()
        return RedirectResponse(
            url=f"/competencies?ai_error={quote(str(exc))}",
            status_code=303,
        )
    db.commit()
    return RedirectResponse(
        url="/competencies?ai_status=STAR%20shaping%20generated",
        status_code=303,
    )


@router.post("/competencies/{evidence_uuid}", include_in_schema=False)
def update_competency_evidence_form(
    evidence_uuid: str,
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    title: Annotated[str, Form()] = "",
    competency: Annotated[str, Form()] = "",
    situation: Annotated[str, Form()] = "",
    task: Annotated[str, Form()] = "",
    action: Annotated[str, Form()] = "",
    result: Annotated[str, Form()] = "",
    evidence_notes: Annotated[str, Form()] = "",
    strength: Annotated[str, Form()] = "seed",
    tags: Annotated[str, Form()] = "",
) -> RedirectResponse:
    evidence = get_user_competency_evidence_by_uuid(db, current_user, evidence_uuid)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Competency evidence not found")
    try:
        update_competency_evidence(
            evidence,
            title=title,
            competency=competency,
            situation=situation,
            task=task,
            action=action,
            result=result,
            evidence_notes=evidence_notes,
            strength=strength,
            tags=tags,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return RedirectResponse(url="/competencies", status_code=303)
