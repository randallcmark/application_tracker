from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select

from app.api.deps import DbSession, get_current_user
from app.api.routes.ui import compact_content_rhythm_styles, render_shell_page
from app.db.models.ai_output import AiOutput
from app.db.models.communication import Communication
from app.db.models.interview_event import InterviewEvent
from app.db.models.job import Job
from app.db.models.user import User
from app.db.models.user_profile import UserProfile
from app.services.ai import AiExecutionError, generate_job_ai_output
from app.services.profiles import get_user_profile

router = APIRouter(tags=["focus"])

ACTIVE_STATUSES = ("interested", "preparing", "applied", "interviewing", "offer")


def _value(value: object) -> str:
    if value is None or value == "":
        return "Not set"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def _profile_is_empty(profile: UserProfile | None) -> bool:
    if profile is None:
        return True
    return not any(
        (
            profile.target_roles,
            profile.target_locations,
            profile.remote_preference,
            profile.salary_min,
            profile.salary_max,
            profile.preferred_industries,
            profile.excluded_industries,
            profile.constraints,
            profile.urgency,
            profile.positioning_notes,
        )
    )


def _format_salary_goal(value: Decimal | None, currency: str | None) -> str:
    if value is None:
        return ""
    rounded_thousands = int((value / Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    amount = f"{rounded_thousands}K"
    if currency:
        return f"{currency} {amount}"
    return amount


def _list_due_followups(db: DbSession, user: User, *, now: datetime) -> list[Communication]:
    return list(
        db.scalars(
            select(Communication)
            .join(Job)
            .where(
                Communication.owner_user_id == user.id,
                Communication.follow_up_at.is_not(None),
                Communication.follow_up_at <= now,
                Job.status != "archived",
            )
            .order_by(Communication.follow_up_at, Communication.created_at)
            .limit(6)
        )
    )


def _list_stale_jobs(db: DbSession, user: User, *, now: datetime) -> list[Job]:
    stale_before = now - timedelta(days=7)
    return list(
        db.scalars(
            select(Job)
            .where(
                Job.owner_user_id == user.id,
                Job.status.in_(ACTIVE_STATUSES),
                Job.updated_at <= stale_before,
            )
            .order_by(Job.updated_at, Job.created_at)
            .limit(6)
        )
    )


def _list_recent_jobs(db: DbSession, user: User) -> list[Job]:
    return list(
        db.scalars(
            select(Job)
            .where(
                Job.owner_user_id == user.id,
                Job.intake_state != "needs_review",
                Job.status.in_(("saved", "interested")),
            )
            .order_by(Job.created_at.desc())
            .limit(6)
        )
    )


def _list_upcoming_interviews(db: DbSession, user: User, *, now: datetime) -> list[InterviewEvent]:
    return list(
        db.scalars(
            select(InterviewEvent)
            .join(Job)
            .where(
                InterviewEvent.owner_user_id == user.id,
                InterviewEvent.scheduled_at.is_not(None),
                InterviewEvent.scheduled_at >= now,
                Job.status != "archived",
            )
            .order_by(InterviewEvent.scheduled_at, InterviewEvent.created_at)
            .limit(6)
        )
    )


def _count_active_jobs(db: DbSession, user: User) -> int:
    return (
        db.scalar(
            select(func.count(Job.id)).where(
                Job.owner_user_id == user.id,
                Job.status.in_(ACTIVE_STATUSES),
            )
        )
        or 0
    )


def _job_link(job: Job) -> str:
    return f'<a href="/jobs/{escape(job.uuid, quote=True)}">{escape(job.title)}</a>'


def _empty(message: str) -> str:
    return f'<p class="empty">{escape(message)}</p>'


def _followup_item(event: Communication) -> str:
    return f"""
    <li>
      <strong>{_job_link(event.job)}</strong>
      <span>{escape(_value(event.follow_up_at))}</span>
      <p>{escape(event.subject or event.notes or "Follow up")}</p>
    </li>
    """


def _job_item(job: Job, *, detail: str) -> str:
    return f"""
    <li>
      <strong>{_job_link(job)}</strong>
      <span>{escape(detail)}</span>
      <p>{escape(job.company or "Company not set")} · {escape(job.status)}</p>
    </li>
    """


def _interview_item(interview: InterviewEvent) -> str:
    return f"""
    <li>
      <strong>{_job_link(interview.job)}</strong>
      <span>{escape(_value(interview.scheduled_at))}</span>
      <p>{escape(interview.stage)} · {escape(interview.location or "Location not set")}</p>
    </li>
    """


def _section(title: str, body: str) -> str:
    return f"""
    <article class="focus-card">
      <div class="card-header">
        <div>
          <p class="panel-micro">Focus queue</p>
          <h2>{escape(title)}</h2>
        </div>
        <span class="status-pill accent">Now</span>
      </div>
      {body}
    </article>
    """


def _list(items: list[str], empty_message: str) -> str:
    if not items:
        return _empty(empty_message)
    return '<ul class="focus-list">' + "\n".join(items) + "</ul>"


def _focus_ai_target(
    due_followups: list[Communication],
    stale_jobs: list[Job],
    recent_jobs: list[Job],
) -> Job | None:
    if due_followups:
        return due_followups[0].job
    if stale_jobs:
        return stale_jobs[0]
    if recent_jobs:
        return recent_jobs[0]
    return None


def _render_inline_markdown(text: str) -> str:
    escaped = escape(text)
    escaped = escaped.replace("**", "\u0000")
    parts = escaped.split("\u0000")
    if len(parts) > 1:
        rebuilt: list[str] = []
        for index, part in enumerate(parts):
            if index % 2 == 1:
                rebuilt.append(f"<strong>{part}</strong>")
            else:
                rebuilt.append(part)
        escaped = "".join(rebuilt)
    return escaped


def _render_markdown_blocks(text: str, *, class_name: str) -> str:
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
            if not paragraph or paragraph.startswith(("# ", "## ", "### ", "* ", "- ")):
                break
            paragraph_lines.append(paragraph)
            i += 1
        blocks.append(f"<p>{_render_inline_markdown(' '.join(paragraph_lines))}</p>")
    return f'<div class="{escape(class_name, quote=True)}">' + "".join(blocks) + "</div>"


def _flash_message(message: str, *, tone: str) -> str:
    return f'<section class="page-panel flash flash-{escape(tone, quote=True)}"><p>{escape(message)}</p></section>'


def _focus_redirect(*, ai_status: str | None = None, ai_error: str | None = None) -> str:
    params = []
    if ai_status:
        params.append(f"ai_status={quote(ai_status)}")
    if ai_error:
        params.append(f"ai_error={quote(ai_error)}")
    if not params:
        return "/focus"
    return "/focus?" + "&".join(params)


def _focus_ai_output(output: AiOutput | None, job: Job | None) -> str:
    if output is None or job is None:
        return '<p class="meta">No AI nudge yet. Generate one when you want a quick steer on the next useful move.</p>'
    provider = output.model_name or output.provider or "AI provider"
    return f"""
    <article class="focus-ai-card">
      <div class="panel-header">
        <div>
          <p class="panel-micro">Visible AI output</p>
          <h2>AI nudge</h2>
        </div>
        <span class="status-pill accent">Optional</span>
      </div>
      <p class="meta">For <a href="/jobs/{escape(job.uuid, quote=True)}">{escape(job.title)}</a> · From {escape(provider)}</p>
      {_render_markdown_blocks(output.body, class_name="ai-markdown")}
    </article>
    """


def _focus_ai_panel(job: Job | None) -> str:
    if job is None:
        return """
        <section class="page-panel soft">
          <div class="panel-header">
            <div>
              <p class="panel-micro">AI nudge</p>
              <h2>No current target</h2>
            </div>
          </div>
          <p>No due follow-up, stale active job, or recent prospect is available for a Focus suggestion right now.</p>
        </section>
        """
    return f"""
    <section class="page-panel ai">
      <div class="panel-header">
        <div>
          <p class="panel-micro">AI nudge</p>
          <h2>Suggest the next useful move</h2>
        </div>
        <span class="status-pill accent">Manual</span>
      </div>
      <p class="meta">Targeting <a href="/jobs/{escape(job.uuid, quote=True)}">{escape(job.title)}</a>. Focus uses one explicit recommendation at a time.</p>
      <form method="post" action="/focus/ai-nudge">
        <input type="hidden" name="job_uuid" value="{escape(job.uuid, quote=True)}">
        <button type="submit">Suggest next step</button>
      </form>
      <p class="meta">AI only creates a visible note. It does not move status, add artefacts, or update workflow state.</p>
    </section>
    """


def render_focus(
    user: User,
    *,
    profile: UserProfile | None,
    due_followups: list[Communication],
    stale_jobs: list[Job],
    recent_jobs: list[Job],
    interviews: list[InterviewEvent],
    active_count: int,
    ai_output: AiOutput | None = None,
    ai_target_job: Job | None = None,
    ai_status: str | None = None,
    ai_error: str | None = None,
) -> HTMLResponse:
    goal = None
    if profile and (profile.target_roles or profile.target_locations or profile.salary_min or profile.salary_max):
        goal_bits = ['<span class="goal-chip-label">Target:</span>']
        if profile.target_roles:
            goal_bits.append(f'<strong class="goal-chip-primary">{escape(profile.target_roles)}</strong>')
        if profile.target_locations:
            goal_bits.append('<span class="goal-chip-sep secondary">|</span>')
            goal_bits.append(f'<span class="goal-chip-secondary">{escape(profile.target_locations)}</span>')
        if profile.salary_min or profile.salary_max:
            salary = " / ".join(
                part
                for part in (
                    _format_salary_goal(profile.salary_min, profile.salary_currency),
                    _format_salary_goal(profile.salary_max, profile.salary_currency),
                )
                if part
            )
            if salary:
                goal_bits.append('<span class="goal-chip-sep tertiary">|</span>')
                goal_bits.append(f'<span class="goal-chip-tertiary">{escape(salary)}</span>')
        goal = "".join(goal_bits)

    profile_prompt = (
        """
        <section class="page-panel ai prompt">
          <div class="panel-header">
            <div>
              <p class="panel-micro">Profile signal</p>
              <h2>Complete your job-search profile</h2>
            </div>
            <span class="status-pill accent">Useful next</span>
          </div>
          <p>Focus will become more useful when it knows your target roles, locations, constraints, and positioning notes.</p>
          <a class="button" href="/settings#profile">Add profile</a>
        </section>
        """
        if _profile_is_empty(profile)
        else ""
    )
    due_items = [_followup_item(event) for event in due_followups]
    stale_items = [_job_item(job, detail=f"Updated {_value(job.updated_at)}") for job in stale_jobs]
    recent_items = [_job_item(job, detail=f"Added {_value(job.created_at)}") for job in recent_jobs]
    interview_items = [_interview_item(interview) for interview in interviews]
    extra_styles = compact_content_rhythm_styles() + """
    .focus-summary {
      margin-bottom: 18px;
    }
    .focus-grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .focus-card {
      background: linear-gradient(180deg, rgba(255,255,255,1), rgba(249,251,253,0.98));
      border: 1px solid var(--line-soft);
      border-radius: var(--radius-xl);
      box-shadow: var(--shadow-md);
      display: grid;
      gap: 14px;
      padding: 18px;
    }
    .focus-list {
      display: grid;
      gap: 10px;
      list-style: none;
      margin: 0;
      padding: 0;
    }
    .focus-list li {
      background: rgba(247,249,252,0.92);
      border: 1px solid var(--line-soft);
      border-radius: var(--radius-lg);
      display: grid;
      gap: 4px;
      padding: 14px;
    }
    .focus-list li strong { font-size: 1rem; }
    .focus-list li span,
    .focus-list li p,
    .empty { color: var(--muted); }
    .focus-aside {
      display: grid;
      gap: 18px;
    }
    .tip-list {
      display: grid;
      gap: 10px;
      list-style: none;
      margin: 0;
      padding: 0;
    }
    .tip-list li {
      border-left: 3px solid rgba(255,255,255,0.28);
      padding-left: 10px;
    }
    .empty {
      background: rgba(247,249,252,0.92);
      border: 1px dashed var(--line);
      border-radius: var(--radius-lg);
      padding: 14px;
    }
    .flash { padding: 14px 18px; }
    .flash-success {
      background: rgba(59, 167, 134, 0.10);
      border-color: rgba(59, 167, 134, 0.28);
    }
    .flash-error {
      background: rgba(226, 91, 76, 0.10);
      border-color: rgba(226, 91, 76, 0.28);
    }
    .focus-ai-card {
      background: rgba(232, 239, 255, 0.72);
      border: 1px solid var(--ai-line);
      border-radius: var(--radius-xl);
      display: grid;
      gap: 12px;
      padding: 18px;
    }
    .focus-aside form { display: grid; gap: 10px; }
    .ai-markdown { display: grid; gap: 10px; }
    .ai-markdown h2, .ai-markdown h3, .ai-markdown h4 { font-size: 1rem; margin: 0; }
    .ai-markdown p, .ai-markdown ul { margin: 0; }
    .ai-markdown ul { padding-left: 18px; }
    @media (max-width: 760px) {
      .focus-grid { grid-template-columns: 1fr; }
    }
    """
    flash_parts = []
    if ai_status:
        flash_parts.append(_flash_message(ai_status, tone="success"))
    if ai_error:
        flash_parts.append(_flash_message(ai_error, tone="error"))
    aside = f"""
    <div class="focus-aside">
      {' '.join(flash_parts)}
      {_focus_ai_panel(ai_target_job)}
      {_focus_ai_output(ai_output, ai_target_job)}
      <section class="page-panel soft">
        <div class="panel-header">
          <div>
            <p class="panel-micro">Resume</p>
            <h2>Where to resume</h2>
          </div>
          <a class="secondary" href="/board">Board</a>
        </div>
        <p>Use Focus for the next decision, then jump into Board or Job Workspace to keep the application moving.</p>
        <div class="mobile-stack">
          <span class="status-pill accent">{len(due_followups)} due follow-ups</span>
          <span class="status-pill warn">{len(stale_jobs)} stale jobs</span>
          <span class="status-pill success">{len(interviews)} interviews</span>
        </div>
      </section>
      <section class="page-panel emphasis">
        <div class="panel-header">
          <div>
            <p class="panel-micro">Daily rhythm</p>
            <h2>Keep the loop tight</h2>
          </div>
        </div>
        <p>Start with follow-ups, review what has gone stale, and end by deciding whether new prospects belong in the workflow.</p>
        <ul class="tip-list">
          <li>Review Inbox before adding new manual jobs.</li>
          <li>Use Job Workspace when a role needs execution, not just status movement.</li>
          <li>Record return notes after external actions so Focus stays trustworthy.</li>
        </ul>
      </section>
    </div>
    """
    body = f"""
    {profile_prompt}
    <div class="metric-grid focus-summary" aria-label="Focus summary">
      <div class="metric-card"><strong>{len(due_followups)}</strong><span>Due follow-ups</span></div>
      <div class="metric-card"><strong>{len(stale_jobs)}</strong><span>Stale jobs</span></div>
      <div class="metric-card"><strong>{len(interviews)}</strong><span>Upcoming interviews</span></div>
      <div class="metric-card"><strong>{active_count}</strong><span>Active jobs</span></div>
    </div>
    <div class="focus-grid">
      {_section("Due follow-ups", _list(due_items, "No due follow-ups."))}
      {_section("Stale active jobs", _list(stale_items, "No stale active jobs."))}
      {_section("Upcoming interviews", _list(interview_items, "No upcoming interviews."))}
      {_section("Recent prospects", _list(recent_items, "No recent saved or interested jobs."))}
    </div>
    """
    return HTMLResponse(
        render_shell_page(
            user,
            page_title="Focus",
            title="Focus",
            subtitle="What needs attention now",
            active="focus",
            actions=(("Add job", "/jobs/new", "add-job"),),
            body=body,
            aside=aside,
            goal=goal,
            kicker="Daily command surface",
            container="split",
            extra_styles=extra_styles,
        )
    )


@router.get("/focus", response_class=HTMLResponse, include_in_schema=False)
def focus(
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    ai_status: Annotated[str | None, Query()] = None,
    ai_error: Annotated[str | None, Query()] = None,
) -> HTMLResponse:
    now = datetime.now(UTC)
    profile = get_user_profile(db, current_user)
    due_followups = _list_due_followups(db, current_user, now=now)
    stale_jobs = _list_stale_jobs(db, current_user, now=now)
    recent_jobs = _list_recent_jobs(db, current_user)
    ai_target_job = _focus_ai_target(due_followups, stale_jobs, recent_jobs)
    ai_output = None
    if ai_target_job is not None:
        ai_output = db.scalar(
            select(AiOutput)
            .where(
                AiOutput.owner_user_id == current_user.id,
                AiOutput.job_id == ai_target_job.id,
                AiOutput.output_type == "recommendation",
                AiOutput.status == "active",
            )
            .order_by(AiOutput.updated_at.desc(), AiOutput.created_at.desc())
        )
    return render_focus(
        current_user,
        profile=profile,
        due_followups=due_followups,
        stale_jobs=stale_jobs,
        recent_jobs=recent_jobs,
        interviews=_list_upcoming_interviews(db, current_user, now=now),
        active_count=_count_active_jobs(db, current_user),
        ai_output=ai_output,
        ai_target_job=ai_target_job,
        ai_status=ai_status,
        ai_error=ai_error,
    )


@router.post("/focus/ai-nudge", include_in_schema=False)
def create_focus_ai_nudge(
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
    job_uuid: Annotated[str, Form()] = "",
) -> RedirectResponse:
    job = db.scalar(
        select(Job).where(
            Job.uuid == job_uuid,
            Job.owner_user_id == current_user.id,
        )
    )
    if job is None:
        return RedirectResponse(
            url=_focus_redirect(ai_error="Focus target was not found"),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    try:
        generate_job_ai_output(
            db,
            current_user,
            job,
            output_type="recommendation",
            profile=get_user_profile(db, current_user),
            surface="focus",
        )
    except AiExecutionError as exc:
        db.rollback()
        return RedirectResponse(
            url=_focus_redirect(ai_error=str(exc)),
            status_code=status.HTTP_303_SEE_OTHER,
        )
    db.commit()
    return RedirectResponse(
        url=_focus_redirect(ai_status="AI nudge generated"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
