from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError

from sqlalchemy import select

from app.auth.users import create_local_user
from app.db.models.ai_output import AiOutput
from app.db.models.competency_evidence import CompetencyEvidence
from app.db.models.job import Job
from app.db.models.ai_provider_setting import AiProviderSetting
from app.db.models.user_profile import UserProfile
from app.db.models.artefact import Artefact
from app.db.models.user import User
from app.main import app
from app.services.ai import (
    _ai_debug_summary,
    _call_gemini,
    _build_artefact_analysis_prompt,
    _build_artefact_draft_prompt,
    _build_artefact_tailoring_prompt,
    _build_competency_star_shaping_prompt,
    _build_artefact_suggestion_prompt,
    _build_job_prompt,
    _execute_prompt,
    _http_error_message,
    _provider_timeout_seconds,
    _timeout_error_message,
    _url_error_message,
    AiExecutionError,
    build_job_artefact_analysis,
    generate_job_artefact_analysis,
    generate_job_artefact_draft,
    generate_job_artefact_tailoring_guidance,
    generate_job_artefact_suggestion,
    generate_competency_star_shaping,
)
from app.services.artefacts import load_artefact_text_excerpt
from app.services.competency_evidence import create_competency_evidence
from tests.test_local_auth_routes import build_client


def _candidate(summary_text: str, outcome_text: str = "strongest signal interview-linked, evidence moderate"):
    return type(
        "Candidate",
        (),
        {
            "summary_text": summary_text,
            "artefact_uuid": "artefact-1",
            "outcome_signal_summary": type("OutcomeSummary", (), {"summary_text": outcome_text})(),
        },
    )()


def _setting(provider: str, *, base_url: str | None = None) -> AiProviderSetting:
    return AiProviderSetting(provider=provider, base_url=base_url)


def _http_error(code: int, body: str, *, reason: str = "error") -> HTTPError:
    return HTTPError(
        url="https://example.test",
        code=code,
        msg=reason,
        hdrs=None,
        fp=BytesIO(body.encode("utf-8")),
    )


def test_http_error_message_maps_openai_quota_errors() -> None:
    setting = _setting("openai")
    exc = _http_error(
        429,
        '{"error":{"message":"You exceeded your current quota, please check your plan and billing details.","type":"insufficient_quota","code":"insufficient_quota"}}',
        reason="Too Many Requests",
    )

    message = _http_error_message(setting, exc)

    assert "OpenAI accepted the key" in message
    assert "no available API quota" in message


def test_http_error_message_maps_gemini_model_not_found() -> None:
    setting = _setting("gemini")
    exc = _http_error(
        404,
        '{"error":{"code":404,"message":"models/gemini-missing is not found for API version v1beta, or is not supported for generateContent.","status":"NOT_FOUND"}}',
        reason="Not Found",
    )

    message = _http_error_message(setting, exc)

    assert "Google Gemini could not find that model" in message
    assert "model name in Settings" in message


def test_http_error_message_maps_endpoint_not_found() -> None:
    setting = _setting("gemini", base_url="https://generativelanguage.googleapis.com/v1beta/models")
    exc = _http_error(404, "Not Found", reason="Not Found")

    message = _http_error_message(setting, exc)

    assert "endpoint was not found" in message
    assert "Base URL in Settings" in message


def test_http_error_message_maps_auth_errors() -> None:
    setting = _setting("gemini")
    exc = _http_error(401, '{"error":{"message":"Request had invalid authentication credentials."}}', reason="Unauthorized")

    message = _http_error_message(setting, exc)

    assert "rejected the API key" in message


def test_url_error_message_maps_tls_certificate_failures() -> None:
    setting = _setting("openai")
    exc = URLError("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")

    message = _url_error_message(setting, exc)

    assert "TLS certificate validation failed" in message


def test_url_error_message_maps_generic_connectivity_failures() -> None:
    setting = _setting("openai_compatible")
    exc = URLError("Connection refused")

    message = _url_error_message(setting, exc)

    assert "Could not reach OpenAI-compatible provider" in message
    assert "Base URL in Settings" in message


def test_timeout_error_message_maps_provider_timeouts() -> None:
    setting = _setting("gemini")

    message = _timeout_error_message(setting)

    assert "Google Gemini timed out before returning a response" in message
    assert "reduce the request size" in message


def test_provider_timeout_seconds_are_provider_and_payload_aware() -> None:
    assert _provider_timeout_seconds(_setting("openai")) == 20
    assert _provider_timeout_seconds(_setting("openai_compatible")) == 20
    assert _provider_timeout_seconds(_setting("gemini")) == 30
    assert _provider_timeout_seconds(_setting("gemini"), document_attached=True) == 60


def test_build_job_prompt_uses_focus_specific_recommendation_instruction() -> None:
    profile = UserProfile(target_roles="Technical Program Manager", target_locations="Remote UK")
    job = Job(
        title="Staff TPM",
        company="Example Co",
        status="applied",
        location="Remote",
        description_raw="Lead cross-functional delivery.",
    )

    title, prompt = _build_job_prompt(
        "recommendation",
        profile=profile,
        job=job,
        surface="focus",
    )

    assert title == "AI next-step recommendation"
    assert "This recommendation is for the Focus surface" in prompt
    assert "Recommend exactly one concrete next action" in prompt
    assert "Why this now" in prompt
    assert "Do not suggest status changes or multiple parallel tasks" in prompt
    assert "Target roles: Technical Program Manager" in prompt
    assert "Title: Staff TPM" in prompt


def test_build_job_prompt_keeps_default_recommendation_instruction_for_non_focus_surfaces() -> None:
    job = Job(title="Generalist role", status="saved")

    _, prompt = _build_job_prompt(
        "recommendation",
        profile=None,
        job=job,
    )

    assert "This recommendation is for the Focus surface" not in prompt
    assert "Why now" in prompt
    assert "No user profile is configured." in prompt


def test_build_artefact_suggestion_prompt_includes_candidate_summaries() -> None:
    profile = UserProfile(target_roles="Technical Program Manager")
    job = Job(title="Staff TPM", status="saved", description_raw="Lead cross-functional delivery.")
    candidate = _candidate("Kind: resume | Filename: tpm-resume.pdf | Linked jobs: 2")
    analysis = AiOutput(
        body="### How well this fits the vacancy\n* Strong platform alignment",
        source_context={"artefact_uuid": "artefact-1"},
    )

    title, prompt = _build_artefact_suggestion_prompt(
        profile=profile,
        job=job,
        candidates=[candidate],
        candidate_analyses=[analysis],
    )

    assert title == "AI artefact suggestion"
    assert "Best starting artefact" in prompt
    assert "Candidate 1:" in prompt
    assert "Kind: resume | Filename: tpm-resume.pdf" in prompt
    assert "Outcome signals:" in prompt
    assert "Candidate analysis 1:" in prompt
    assert "How well this fits the vacancy" in prompt
    assert "strongest signal interview-linked, evidence moderate" in prompt
    assert "Target roles: Technical Program Manager" in prompt
    assert "Title: Staff TPM" in prompt


def test_build_artefact_suggestion_prompt_handles_empty_candidate_list() -> None:
    job = Job(title="No artefacts role", status="saved")

    _, prompt = _build_artefact_suggestion_prompt(
        profile=None,
        job=job,
        candidates=[],
    )

    assert "No existing artefacts are available for this user." in prompt
    assert "Prefer 'no suitable artefact' over weak guesses." in prompt


def test_build_artefact_analysis_prompt_includes_requirement_and_content_mode_context() -> None:
    profile = UserProfile(target_roles="Technical Program Manager")
    job = Job(
        title="Staff TPM",
        status="saved",
        description_raw="Please provide a cover letter and supporting statement.",
    )
    candidate = _candidate("Kind: resume | Filename: tpm-resume.pdf | Metadata quality: strong")

    title, prompt = _build_artefact_analysis_prompt(
        profile=profile,
        job=job,
        artefact_summary=candidate,
        content_mode="metadata_only",
        requirement_summary="Required or explicitly requested: cover letter, supporting statement",
        structured_index={
            "detected_sections": ["summary", "experience", "skills"],
            "accomplishment_density": "moderate",
            "seniority_indicators": ["staff", "lead"],
            "tooling_or_domain_mentions": ["aws", "platform"],
            "requirement_coverage_hints": ["job requests additional artefacts beyond this baseline: cover letter, supporting statement"],
        },
    )

    assert title == "AI artefact analysis"
    assert "Artefact type and structure" in prompt
    assert "Inferred artefact requirements:" in prompt
    assert "cover letter, supporting statement" in prompt
    assert "Outcome signals:" in prompt
    assert "Content mode: metadata_only" in prompt
    assert "Precomputed structured signals:" in prompt
    assert "Detected sections: summary, experience, skills" in prompt
    assert "reasoning from metadata and job context only" in prompt.lower()


def test_generate_job_artefact_suggestion_stores_visible_output(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="Staff TPM", status="saved")
            artefact = Artefact(
                owner_user_id=user.id,
                job_id=job.id,
                kind="resume",
                purpose="TPM resume",
                version_label="v3",
                notes="Used for senior platform roles.",
                outcome_context="Helped reach interview loop.",
                filename="tpm-resume.pdf",
                storage_key="artefacts/tpm-resume.pdf",
            )
            setting = AiProviderSetting(
                owner_user_id=user.id,
                provider="gemini",
                model_name="gemini-flash-latest",
                api_key_encrypted="sealed",
                api_key_hint="key...1234",
                is_enabled=True,
            )
            db.add_all([job, artefact, setting])
            db.commit()
            user_id = user.id
            job_id = job.id
            artefact_uuid = artefact.uuid

        monkeypatch.setattr(
            "app.services.ai.build_job_artefact_analysis",
            lambda *args, **kwargs: AiOutput(
                body="### How well this fits the vacancy\n* Strong platform alignment",
                source_context={
                    "artefact_uuid": artefact_uuid,
                    "detected_sections": ["experience", "skills"],
                    "accomplishment_density": "high",
                    "tooling_or_domain_mentions": ["aws", "platform"],
                    "requirement_coverage_hints": ["job requests additional artefacts beyond this baseline: cover letter"],
                },
            ),
        )

        def fake_execute_prompt(setting, prompt, **kwargs):
            assert "Candidate artefacts:" in prompt
            assert "tpm-resume.pdf" in prompt
            assert "Candidate analysis 1:" in prompt
            assert "Candidate analysis index 1:" in prompt
            assert "Detected sections: experience, skills" in prompt
            return "### Best starting artefact\n* **tpm-resume.pdf**"

        monkeypatch.setattr("app.services.ai._execute_prompt", fake_execute_prompt)

        with session_local() as db:
            user = db.get(User, user_id)
            job = db.get(Job, job_id)

            output = generate_job_artefact_suggestion(db, user, job)
            db.commit()

            assert output.output_type == "artefact_suggestion"
            assert output.title == "AI artefact suggestion"
            assert output.source_context["surface"] == "job_workspace"
            assert output.source_context["prompt_contract"] == "artefact_suggestion_v1"
            assert len(output.source_context["shortlisted_artefact_uuids"]) == 1

            stored = db.get(AiOutput, output.id)
            assert stored is not None
            assert stored.body == "### Best starting artefact\n* **tpm-resume.pdf**"
    finally:
        app.dependency_overrides.clear()


def test_build_job_artefact_analysis_can_run_without_persisting_output(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(
                owner_user_id=user.id,
                title="Analysis helper target",
                status="saved",
                description_raw="Please include a cover letter.",
            )
            artefact = Artefact(
                owner_user_id=user.id,
                job_id=job.id,
                kind="resume",
                purpose="TPM resume",
                filename="baseline.md",
                content_type="text/markdown",
                storage_key="artefacts/baseline.md",
            )
            setting = AiProviderSetting(
                owner_user_id=user.id,
                provider="gemini",
                model_name="gemini-flash-latest",
                api_key_encrypted="sealed",
                api_key_hint="key...1234",
                is_enabled=True,
            )
            db.add_all([job, artefact, setting])
            db.commit()
            user_id = user.id
            job_id = job.id
            artefact_id = artefact.id
            artefact_uuid = artefact.uuid
            artefact_uuid = artefact.uuid

        monkeypatch.setattr(
            "app.services.ai.load_artefact_text_excerpt",
            lambda artefact: "# Resume\n\nPlatform delivery evidence",
        )

        def fake_execute_prompt(setting, prompt, *, document=None, **kwargs):
            assert "Inferred artefact requirements:" in prompt
            assert "cover letter" in prompt
            return "### Artefact type and structure\n* Resume baseline"

        monkeypatch.setattr("app.services.ai._execute_prompt", fake_execute_prompt)

        with session_local() as db:
            user = db.get(User, user_id)
            job = db.get(Job, job_id)
            artefact = db.get(Artefact, artefact_id)

            output = build_job_artefact_analysis(
                db,
                user,
                job,
                artefact,
                persist=False,
            )

            assert output.output_type == "artefact_analysis"
            assert output.source_context["prompt_contract"] == "artefact_analysis_v1"
            assert output.source_context["used_extracted_text"] is True
            assert "cover letter" in output.source_context["inferred_requirement_summary"]
            assert output.source_context["structured_analysis_v"] == 1
            assert output.source_context["accomplishment_density"] in {"low", "moderate", "high"}
            assert isinstance(output.source_context["detected_sections"], list)
            assert isinstance(output.source_context["requirement_coverage_hints"], list)
            stored = db.scalars(select(AiOutput).where(AiOutput.output_type == "artefact_analysis")).all()
            assert stored == []
    finally:
        app.dependency_overrides.clear()


def test_generate_job_artefact_analysis_stores_visible_output(tmp_path: Path, monkeypatch) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(
                owner_user_id=user.id,
                title="Analysis target",
                status="saved",
                description_raw="A writing sample is required.",
            )
            artefact = Artefact(
                owner_user_id=user.id,
                job_id=job.id,
                kind="resume",
                filename="baseline.pdf",
                content_type="application/pdf",
                storage_key="artefacts/baseline.pdf",
            )
            setting = AiProviderSetting(
                owner_user_id=user.id,
                provider="gemini",
                model_name="gemini-flash-latest",
                api_key_encrypted="sealed",
                api_key_hint="key...1234",
                is_enabled=True,
            )
            db.add_all([job, artefact, setting])
            db.commit()
            user_id = user.id
            job_id = job.id
            artefact_id = artefact.id

        monkeypatch.setattr("app.services.ai.load_artefact_text_excerpt", lambda artefact: None)
        monkeypatch.setattr(
            "app.services.ai.load_artefact_document_payload",
            lambda artefact: ("application/pdf", b"%PDF-sample"),
        )

        def fake_execute_prompt(setting, prompt, *, document=None, **kwargs):
            assert "Content mode: provider_document" in prompt
            assert "writing sample" in prompt
            assert document is not None
            return "### Artefact type and structure\n* Resume-like PDF"

        monkeypatch.setattr("app.services.ai._execute_prompt", fake_execute_prompt)

        with session_local() as db:
            user = db.get(User, user_id)
            job = db.get(Job, job_id)
            artefact = db.get(Artefact, artefact_id)

            output = generate_job_artefact_analysis(db, user, job, artefact)
            db.commit()

            assert output.output_type == "artefact_analysis"
            assert output.title == "AI artefact analysis"
            assert output.source_context["prompt_contract"] == "artefact_analysis_v1"
            assert output.source_context["content_mode"] == "provider_document"
            assert "writing sample" in output.source_context["inferred_requirement_summary"]
            assert output.source_context["structured_analysis_v"] == 1
            assert isinstance(output.source_context["requirement_coverage_hints"], list)

            stored = db.get(AiOutput, output.id)
            assert stored is not None
            assert stored.body == "### Artefact type and structure\n* Resume-like PDF"
    finally:
        app.dependency_overrides.clear()


def test_generate_job_artefact_suggestion_uses_local_fallback_when_no_candidates(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(
                owner_user_id=user.id,
                title="No artefacts role",
                status="saved",
                description_raw="Please submit a cover letter and supporting statement.",
            )
            db.add(job)
            db.commit()
            user_id = user.id
            job_id = job.id

        with session_local() as db:
            user = db.get(User, user_id)
            job = db.get(Job, job_id)

            output = generate_job_artefact_suggestion(db, user, job)
            db.commit()

            assert output.output_type == "artefact_suggestion"
            assert output.provider == "system"
            assert output.source_context["local_fallback"] is True
            assert output.source_context["shortlisted_artefact_uuids"] == []
            assert "No existing artefact is available yet" in output.body
            assert "cover letter, supporting statement" in output.body
    finally:
        app.dependency_overrides.clear()


def test_build_artefact_tailoring_prompt_uses_selected_artefact_context() -> None:
    profile = UserProfile(target_roles="Technical Program Manager")
    job = Job(title="Staff TPM", status="saved", description_raw="Lead delivery. Please provide a supporting statement.")
    artefact = Artefact(
        kind="resume",
        purpose="TPM resume",
        filename="tpm-resume.pdf",
        storage_key="artefacts/tpm-resume.pdf",
    )
    candidate = _candidate("Kind: resume | Filename: tpm-resume.pdf | Metadata quality: strong")
    prior = AiOutput(body="### Best starting artefact\n* **tpm-resume.pdf**")
    analysis = AiOutput(
        body="### Evidence strength\n* Strong quantified delivery evidence",
        source_context={
            "detected_sections": ["experience", "skills"],
            "accomplishment_density": "high",
            "seniority_indicators": ["staff", "lead"],
        },
    )

    title, prompt = _build_artefact_tailoring_prompt(
        profile=profile,
        job=job,
        artefact=artefact,
        artefact_summary=candidate,
        prior_suggestion=prior,
        artefact_analysis=analysis,
        requirement_strategy_summary=(
            "Required or explicitly requested artefacts: supporting statement\n"
            "Selected baseline does not satisfy all explicitly requested artefact types by itself; "
            "guide the user on what should exist alongside it."
        ),
        evidence_phrasing_summary="Use cautious wording where evidence is thin and stronger wording only where the source supports it.",
        submission_pack_coordination_summary="Use the supporting statement for denser criteria evidence so the resume can stay evidence-led.",
        generation_brief_summary="- Focus areas: Emphasise cross-functional delivery and platform migrations\n- Must include: stakeholder leadership",
    )

    assert title == "AI tailoring guidance"
    assert "sections titled 'Keep', 'Strengthen', 'De-emphasise or remove'" in prompt
    assert "Selected artefact:" in prompt
    assert "Filename: tpm-resume.pdf" in prompt
    assert "Outcome signals:" in prompt
    assert "Artefact analysis:" in prompt
    assert "Artefact analysis index:" in prompt
    assert "Detected sections: experience, skills" in prompt
    assert "Submission strategy:" in prompt
    assert "Submission pack coordination:" in prompt
    assert "Evidence phrasing guidance:" in prompt
    assert "User generation brief:" in prompt
    assert "platform migrations" in prompt
    assert "supporting statement" in prompt
    assert "Prior artefact suggestion:" in prompt
    assert "Target roles: Technical Program Manager" in prompt


def test_build_artefact_draft_prompt_includes_content_mode_and_tailoring_guidance() -> None:
    profile = UserProfile(target_roles="Technical Program Manager")
    job = Job(title="Staff TPM", status="saved", description_raw="Lead delivery.")
    candidate = _candidate("Kind: resume | Filename: tpm-resume.pdf | Metadata quality: strong")
    tailoring = AiOutput(body="### Keep\n* **Programme delivery**")
    analysis = AiOutput(
        body="### What this artefact emphasizes\n* Platform delivery leadership",
        source_context={
            "detected_sections": ["summary", "experience"],
            "accomplishment_density": "moderate",
            "tooling_or_domain_mentions": ["platform", "aws"],
        },
    )

    title, prompt = _build_artefact_draft_prompt(
        profile=profile,
        job=job,
        artefact_summary=candidate,
        draft_kind="resume_draft",
        content_mode="extracted_text",
        extracted_text="# Resume\n\nPlatform delivery",
        tailoring_guidance=tailoring,
        artefact_analysis=analysis,
        requirement_strategy_summary="No explicit extra artefact requirement detected in the job text.",
        evidence_allocation_summary="Keep the resume focused on concrete role-relevant evidence, impact, scope, and skills.",
        section_emphasis_summary=(
            "Preserve a concise professional summary rather than expanding it into a long narrative block.\n"
            "Use the skills area to foreground the strongest relevant tooling/domain terms: platform, aws"
        ),
        evidence_phrasing_summary="Use the verified extracted text as the anchor for any stronger wording.",
        generation_brief_summary="- Focus areas: Platform delivery\n- Tone or positioning: concise and executive-ready",
    )

    assert title == "AI tailored resume draft"
    assert "Outcome signals:" in prompt
    assert "Content mode: extracted_text" in prompt
    assert "Verified extracted artefact text:" in prompt
    assert "Artefact analysis:" in prompt
    assert "Artefact analysis index:" in prompt
    assert "Submission strategy:" in prompt
    assert "Evidence allocation guidance:" in prompt
    assert "Section emphasis guidance:" in prompt
    assert "Evidence phrasing guidance:" in prompt
    assert "User generation brief:" in prompt
    assert "Tailoring guidance:" in prompt
    assert "Platform delivery" in prompt


def test_build_cover_letter_draft_prompt_uses_cover_letter_contract() -> None:
    job = Job(title="Staff TPM", company="Example Co", status="saved", description_raw="Please include a cover letter.")
    candidate = _candidate("Kind: resume | Filename: tpm-resume.pdf | Metadata quality: strong")
    analysis = AiOutput(
        body="### Evidence strength\n* Strong delivery outcomes",
        source_context={"accomplishment_density": "high"},
    )

    title, prompt = _build_artefact_draft_prompt(
        profile=None,
        job=job,
        artefact_summary=candidate,
        draft_kind="cover_letter_draft",
        content_mode="metadata_only",
        artefact_analysis=analysis,
        requirement_strategy_summary=(
            "Required or explicitly requested artefacts: cover letter\n"
            "The requested draft type directly satisfies one explicit job requirement: cover letter"
        ),
        evidence_allocation_summary="Use the cover letter for concise role motivation, fit framing, and a small number of high-signal examples.",
        section_emphasis_summary="Keep example claims brief and careful where outcome evidence is limited.",
        evidence_phrasing_summary="Where evidence is thin or mostly responsibility-based, use measured wording and mark gaps explicitly instead of polishing them into strengths.",
        submission_pack_coordination_summary="Do not duplicate the resume bullet structure; use the letter to connect the evidence to role motivation.",
    )

    assert title == "AI cover letter draft"
    assert "Draft a concise cover letter for this job" in prompt
    assert "Outcome signals:" in prompt
    assert "Content mode: metadata_only" in prompt
    assert "Artefact analysis:" in prompt
    assert "Artefact analysis index:" in prompt
    assert "Submission strategy:" in prompt
    assert "Submission pack coordination:" in prompt
    assert "Evidence allocation guidance:" in prompt
    assert "Section emphasis guidance:" in prompt
    assert "Evidence phrasing guidance:" in prompt
    assert "directly satisfies one explicit job requirement: cover letter" in prompt
    assert "Baseline artefact content is unavailable. Reason from metadata only." in prompt


def test_build_supporting_statement_draft_prompt_uses_statement_contract() -> None:
    job = Job(title="Staff TPM", company="Example Co", status="saved", description_raw="Please include a supporting statement.")
    candidate = _candidate("Kind: resume | Filename: tpm-resume.pdf | Metadata quality: strong")
    analysis = AiOutput(
        body="### Job requirement match\n* Likely supports statement-heavy application flow",
        source_context={"requirement_coverage_hints": ["job requests additional artefacts beyond this baseline: supporting statement"]},
    )

    title, prompt = _build_artefact_draft_prompt(
        profile=None,
        job=job,
        artefact_summary=candidate,
        draft_kind="supporting_statement_draft",
        content_mode="metadata_only",
        artefact_analysis=analysis,
        requirement_strategy_summary=(
            "Required or explicitly requested artefacts: supporting statement\n"
            "The requested draft type directly satisfies one explicit job requirement: supporting statement"
        ),
        evidence_allocation_summary=(
            "Use the supporting statement for explicit criteria coverage, fuller examples, and structured narrative evidence.\n"
            "Do not merely repeat resume bullets; expand them into context, actions, and outcomes where relevant."
        ),
        section_emphasis_summary=(
            "Expand the strongest evidence into fuller STAR-style or criteria-led examples.\n"
            "Thread the most relevant tooling/domain terms into the example sections: platform"
        ),
        evidence_phrasing_summary="Where the source clearly supports outcomes, use confident but precise impact phrasing.",
        submission_pack_coordination_summary="Use this document to carry the densest requirement-by-requirement evidence so the other documents can stay tighter.",
    )

    assert title == "AI supporting statement draft"
    assert "Draft a targeted supporting statement for this job" in prompt
    assert "Outcome signals:" in prompt
    assert "Content mode: metadata_only" in prompt
    assert "Artefact analysis:" in prompt
    assert "Artefact analysis index:" in prompt
    assert "Submission strategy:" in prompt
    assert "Submission pack coordination:" in prompt
    assert "Section emphasis guidance:" in prompt
    assert "Evidence phrasing guidance:" in prompt
    assert "Use the supporting statement for explicit criteria coverage" in prompt


def test_build_resume_draft_prompt_allocates_narrative_to_supporting_statement_when_required() -> None:
    job = Job(
        title="Staff TPM",
        company="Example Co",
        status="saved",
        description_raw="Please include a supporting statement.",
    )
    candidate = _candidate("Kind: resume | Filename: tpm-resume.pdf | Metadata quality: strong")

    _, prompt = _build_artefact_draft_prompt(
        profile=None,
        job=job,
        artefact_summary=candidate,
        draft_kind="resume_draft",
        content_mode="metadata_only",
        requirement_strategy_summary=(
            "Required or explicitly requested artefacts: supporting statement\n"
            "Selected baseline does not satisfy all explicitly requested artefact types by itself; "
            "guide the user on what should exist alongside it."
        ),
        evidence_allocation_summary=(
            "Keep the resume focused on concrete role-relevant evidence, impact, scope, and skills.\n"
            "Do not overload the resume with long criteria-by-criteria narrative that belongs in the supporting statement."
        ),
    )

    assert "Evidence allocation guidance:" in prompt
    assert "belongs in the supporting statement" in prompt


def test_build_resume_draft_prompt_uses_analysis_to_shape_section_emphasis() -> None:
    job = Job(title="Staff TPM", company="Example Co", status="saved")
    candidate = _candidate("Kind: resume | Filename: tpm-resume.pdf | Metadata quality: strong")
    analysis = AiOutput(
        body="### What this artefact emphasizes\n* Platform delivery leadership",
        source_context={
            "detected_sections": ["summary", "skills"],
            "accomplishment_density": "high",
            "tooling_or_domain_mentions": ["platform", "aws"],
        },
    )

    _, prompt = _build_artefact_draft_prompt(
        profile=None,
        job=job,
        artefact_summary=candidate,
        draft_kind="resume_draft",
        content_mode="metadata_only",
        artefact_analysis=analysis,
        section_emphasis_summary=(
            "Foreground quantified outcomes and impact bullets in the main evidence sections.\n"
            "Preserve a concise professional summary rather than expanding it into a long narrative block.\n"
            "Use the skills area to foreground the strongest relevant tooling/domain terms: platform, aws"
        ),
    )

    assert "Section emphasis guidance:" in prompt
    assert "Foreground quantified outcomes and impact bullets" in prompt
    assert "platform, aws" in prompt


def test_build_competency_star_shaping_prompt_uses_saved_evidence_without_job_context() -> None:
    evidence = CompetencyEvidence(
        owner_user_id=1,
        title="Platform migration recovery",
        competency="Delivery leadership",
        situation="A migration was blocked.",
        task="Recover launch readiness.",
        action="Reset governance and supplier cadence.",
        result="Released on the revised date.",
        evidence_notes="Credible because it involved directors and supplier leads.",
        strength="working",
        tags="platform, leadership",
    )

    title, prompt = _build_competency_star_shaping_prompt(profile=None, evidence=evidence)

    assert title == "AI STAR shaping"
    assert "Use markdown sections titled 'STAR response'" in prompt
    assert "Keep the response reusable across roles" in prompt
    assert "Platform migration recovery" in prompt
    assert "Reset governance and supplier cadence." in prompt
    assert "Job:" not in prompt


def test_generate_competency_star_shaping_stores_visible_output(tmp_path: Path, monkeypatch) -> None:
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
                situation="A launch path was contested.",
                task="Align directors on a smaller first release.",
                action="Built a trade-off narrative and reset cadence.",
                result="Agreement reached before steering group.",
                strength="working",
                tags="leadership, stakeholders",
            )
            setting = AiProviderSetting(
                owner_user_id=user.id,
                provider="gemini",
                model_name="gemini-flash-latest",
                api_key_encrypted="sealed",
                api_key_hint="key...1234",
                is_enabled=True,
            )
            db.add(setting)
            db.commit()
            user_id = user.id
            evidence_id = evidence.id
            evidence_uuid = evidence.uuid

        def fake_execute_prompt(setting, prompt, *, document=None, **kwargs):
            assert kwargs["action"] == "competency_star_shaping"
            assert "Competency evidence:" in prompt
            assert "Agreement reached before steering group." in prompt
            return "### STAR response\n* **Situation:** A launch path was contested."

        monkeypatch.setattr("app.services.ai._execute_prompt", fake_execute_prompt)

        with session_local() as db:
            user = db.get(User, user_id)
            evidence = db.get(type(evidence), evidence_id)

            output = generate_competency_star_shaping(db, user, evidence)
            db.commit()

            assert output.output_type == "competency_star_shaping"
            assert output.title == "AI STAR shaping"
            assert output.job_id is None
            assert output.artefact_id is None
            assert output.source_context["surface"] == "competency_library"
            assert output.source_context["competency_evidence_uuid"] == evidence_uuid
            assert output.source_context["prompt_contract"] == "competency_star_shaping_v1"

            stored = db.scalar(select(AiOutput).where(AiOutput.output_type == "competency_star_shaping"))
            assert stored is not None
            assert stored.body.startswith("### STAR response")
    finally:
        app.dependency_overrides.clear()


def test_generate_job_artefact_tailoring_guidance_stores_visible_output(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="Staff TPM", status="saved")
            artefact = Artefact(
                owner_user_id=user.id,
                job_id=job.id,
                kind="resume",
                purpose="TPM resume",
                version_label="v3",
                notes="Used for senior platform roles.",
                outcome_context="Helped reach interview loop.",
                filename="tpm-resume.pdf",
                storage_key="artefacts/tpm-resume.pdf",
            )
            setting = AiProviderSetting(
                owner_user_id=user.id,
                provider="gemini",
                model_name="gemini-flash-latest",
                api_key_encrypted="sealed",
                api_key_hint="key...1234",
                is_enabled=True,
            )
            db.add_all([job, artefact, setting])
            db.commit()
            user_id = user.id
            job_id = job.id
            artefact_id = artefact.id
            artefact_uuid = artefact.uuid

        monkeypatch.setattr(
            "app.services.ai.build_job_artefact_analysis",
            lambda *args, **kwargs: AiOutput(
                body="### Evidence strength\n* Strong quantified platform delivery evidence",
                source_context={
                    "artefact_uuid": artefact_uuid,
                    "detected_sections": ["experience", "skills"],
                    "accomplishment_density": "high",
                },
            ),
        )

        def fake_execute_prompt(setting, prompt, *, document=None, **kwargs):
            assert "Selected artefact:" in prompt
            assert "tpm-resume.pdf" in prompt
            assert "Artefact analysis:" in prompt
            assert "Artefact analysis index:" in prompt
            assert "Submission strategy:" in prompt
            assert "Submission pack coordination:" in prompt
            assert "Evidence phrasing guidance:" in prompt
            assert "User generation brief:" in prompt
            return "### Keep\n* **Programme delivery evidence**"

        monkeypatch.setattr("app.services.ai._execute_prompt", fake_execute_prompt)

        with session_local() as db:
            user = db.get(User, user_id)
            job = db.get(Job, job_id)
            artefact = db.get(Artefact, artefact_id)

            output = generate_job_artefact_tailoring_guidance(
                db,
                user,
                job,
                artefact,
                generation_brief={"focus_areas": "Programme delivery", "tone": "concise"},
            )
            db.commit()

            assert output.output_type == "tailoring_guidance"
            assert output.artefact_id == artefact_id
            assert output.title == "AI tailoring guidance"
            assert output.source_context["prompt_contract"] == "artefact_tailoring_v1"
            assert output.source_context["artefact_uuid"] == artefact.uuid
            assert output.source_context["used_extracted_text"] is False
            assert output.source_context["draft_handoff_contract"] == "artefact_draft_seed_v1"
            assert output.source_context["required_artefact_types"] == []
            assert output.source_context["generation_brief"] == {
                "focus_areas": "Programme delivery",
                "tone": "concise",
            }

            stored = db.get(AiOutput, output.id)
            assert stored is not None
            assert stored.body == "### Keep\n* **Programme delivery evidence**"
    finally:
        app.dependency_overrides.clear()


def test_generate_job_artefact_tailoring_guidance_uses_local_fallback_for_thin_metadata(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(
                owner_user_id=user.id,
                title="Sparse tailoring target",
                status="saved",
                description_raw="Please include a supporting statement.",
            )
            artefact = Artefact(
                owner_user_id=user.id,
                job_id=job.id,
                kind="resume",
                filename="baseline-resume.pdf",
                storage_key="artefacts/baseline-resume.pdf",
            )
            db.add_all([job, artefact])
            db.commit()
            user_id = user.id
            job_id = job.id
            artefact_id = artefact.id
            artefact_uuid = artefact.uuid

        with session_local() as db:
            user = db.get(User, user_id)
            job = db.get(Job, job_id)
            artefact = db.get(Artefact, artefact_id)

            output = generate_job_artefact_tailoring_guidance(db, user, job, artefact)
            db.commit()

            assert output.output_type == "tailoring_guidance"
            assert output.provider == "system"
            assert output.source_context["local_fallback"] is True
            assert output.source_context["metadata_quality"] == "thin"
            assert output.source_context["artefact_uuid"] == artefact.uuid
            assert "Tailoring is currently working from metadata only" in output.body
            assert "supporting statement" in output.body
    finally:
        app.dependency_overrides.clear()


def test_load_artefact_text_excerpt_reads_textlike_artefacts() -> None:
    artefact = Artefact(
        kind="resume",
        filename="baseline.md",
        content_type="text/markdown",
        storage_key="artefacts/baseline.md",
    )

    excerpt = load_artefact_text_excerpt(
        artefact,
        storage=type("FakeStorage", (), {"load": lambda self, key: b"# Resume\n\nPlatform delivery evidence"})(),
    )

    assert excerpt == "# Resume\n\nPlatform delivery evidence"


def test_generate_job_artefact_tailoring_guidance_uses_extracted_text_for_textlike_artefacts(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(
                owner_user_id=user.id,
                title="Markdown tailoring target",
                status="saved",
                description_raw="Please include a supporting statement.",
            )
            artefact = Artefact(
                owner_user_id=user.id,
                job_id=job.id,
                kind="resume",
                filename="baseline.md",
                content_type="text/markdown",
                storage_key="artefacts/baseline.md",
            )
            setting = AiProviderSetting(
                owner_user_id=user.id,
                provider="gemini",
                model_name="gemini-flash-latest",
                api_key_encrypted="sealed",
                api_key_hint="key...1234",
                is_enabled=True,
            )
            db.add_all([job, artefact, setting])
            db.commit()
            user_id = user.id
            job_id = job.id
            artefact_id = artefact.id
            artefact_uuid = artefact.uuid

        monkeypatch.setattr(
            "app.services.ai.load_artefact_text_excerpt",
            lambda artefact: "# Resume\n\n* Platform delivery\n* Stakeholder leadership",
        )
        monkeypatch.setattr(
            "app.services.ai.build_job_artefact_analysis",
            lambda *args, **kwargs: AiOutput(
                body="### What this artefact emphasizes\n* Platform delivery and stakeholder leadership",
                source_context={
                    "artefact_uuid": artefact_uuid,
                    "detected_sections": ["summary", "experience"],
                    "tooling_or_domain_mentions": ["platform"],
                },
            ),
        )

        def fake_execute_prompt(setting, prompt, *, document=None, **kwargs):
            assert "Extracted artefact text (verified excerpt):" in prompt
            assert "Platform delivery" in prompt
            assert "Artefact analysis:" in prompt
            assert "Artefact analysis index:" in prompt
            assert "Submission strategy:" in prompt
            assert "Submission pack coordination:" in prompt
            assert "Evidence phrasing guidance:" in prompt
            assert "User generation brief:" in prompt
            assert "supporting statement" in prompt
            return "### Keep\n* **Platform delivery**"

        monkeypatch.setattr("app.services.ai._execute_prompt", fake_execute_prompt)

        with session_local() as db:
            user = db.get(User, user_id)
            job = db.get(Job, job_id)
            artefact = db.get(Artefact, artefact_id)

            output = generate_job_artefact_tailoring_guidance(
                db,
                user,
                job,
                artefact,
                generation_brief={"must_include": "Stakeholder leadership"},
            )
            db.commit()

            assert output.provider == "gemini"
            assert output.source_context["used_extracted_text"] is True
            assert output.source_context["draft_handoff_contract"] == "artefact_draft_seed_v1"
            assert output.source_context["required_artefact_types"] == ["supporting statement"]
            assert output.source_context["generation_brief"] == {"must_include": "Stakeholder leadership"}
    finally:
        app.dependency_overrides.clear()


def test_generate_job_artefact_draft_stores_visible_output(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="Draft target", status="saved")
            artefact = Artefact(
                owner_user_id=user.id,
                job_id=job.id,
                kind="resume",
                purpose="TPM resume",
                version_label="v3",
                notes="Used for senior platform roles.",
                outcome_context="Helped reach interview loop.",
                filename="baseline.md",
                content_type="text/markdown",
                storage_key="artefacts/baseline.md",
            )
            setting = AiProviderSetting(
                owner_user_id=user.id,
                provider="gemini",
                model_name="gemini-flash-latest",
                api_key_encrypted="sealed",
                api_key_hint="key...1234",
                is_enabled=True,
            )
            db.add_all([job, artefact, setting])
            db.commit()
            user_id = user.id
            job_id = job.id
            artefact_id = artefact.id
            artefact_uuid = artefact.uuid

        monkeypatch.setattr(
            "app.services.ai.load_artefact_text_excerpt",
            lambda artefact: "# Resume\n\n* Platform delivery",
        )
        monkeypatch.setattr(
            "app.services.ai.build_job_artefact_analysis",
            lambda *args, **kwargs: AiOutput(
                body="### What this artefact emphasizes\n* Platform delivery leadership",
                source_context={
                    "artefact_uuid": artefact_uuid,
                    "detected_sections": ["summary", "experience"],
                    "accomplishment_density": "moderate",
                },
            ),
        )

        def fake_execute_prompt(setting, prompt, *, document=None, **kwargs):
            assert "Content mode: extracted_text" in prompt
            assert "Platform delivery" in prompt
            assert "Artefact analysis:" in prompt
            assert "Artefact analysis index:" in prompt
            assert "Submission strategy:" in prompt
            assert "Submission pack coordination:" in prompt
            assert "Section emphasis guidance:" in prompt
            assert "Evidence phrasing guidance:" in prompt
            assert "User generation brief:" in prompt
            assert document is None
            return "### Headline\nTechnical Program Manager"

        monkeypatch.setattr("app.services.ai._execute_prompt", fake_execute_prompt)

        with session_local() as db:
            user = db.get(User, user_id)
            job = db.get(Job, job_id)
            artefact = db.get(Artefact, artefact_id)

            output = generate_job_artefact_draft(
                db,
                user,
                job,
                artefact,
                draft_kind="resume_draft",
                generation_brief={"focus_areas": "Platform delivery", "tone": "assertive"},
            )
            db.commit()

            assert output.output_type == "draft"
            assert output.title == "AI tailored resume draft"
            assert output.source_context["prompt_contract"] == "artefact_draft_v1"
            assert output.source_context["draft_kind"] == "resume_draft"
            assert output.source_context["content_mode"] == "extracted_text"
            assert output.source_context["artefact_uuid"] == artefact.uuid
            assert output.source_context["required_artefact_types"] == []
            assert output.source_context["generation_brief"] == {
                "focus_areas": "Platform delivery",
                "tone": "assertive",
            }
    finally:
        app.dependency_overrides.clear()


def test_generate_job_artefact_draft_uses_gemini_provider_document_for_pdf_when_no_text_excerpt(
    tmp_path: Path, monkeypatch
) -> None:
    client, session_local = build_client(tmp_path, monkeypatch)
    try:
        with session_local() as db:
            user = create_local_user(db, email="jobseeker@example.com", password="password")
            db.flush()
            job = Job(owner_user_id=user.id, title="PDF draft target", status="saved")
            artefact = Artefact(
                owner_user_id=user.id,
                job_id=job.id,
                kind="resume",
                filename="baseline.pdf",
                content_type="application/pdf",
                storage_key="artefacts/baseline.pdf",
            )
            setting = AiProviderSetting(
                owner_user_id=user.id,
                provider="gemini",
                model_name="gemini-flash-latest",
                api_key_encrypted="sealed",
                api_key_hint="key...1234",
                is_enabled=True,
            )
            db.add_all([job, artefact, setting])
            db.commit()
            user_id = user.id
            job_id = job.id
            artefact_id = artefact.id
            artefact_uuid = artefact.uuid

        monkeypatch.setattr("app.services.ai.load_artefact_text_excerpt", lambda artefact: None)
        monkeypatch.setattr(
            "app.services.ai.load_artefact_document_payload",
            lambda artefact: ("application/pdf", b"%PDF-sample"),
        )
        monkeypatch.setattr(
            "app.services.ai.build_job_artefact_analysis",
            lambda *args, **kwargs: AiOutput(
                body="### Artefact type and structure\n* Resume PDF with likely multi-section content",
                source_context={
                    "artefact_uuid": artefact_uuid,
                    "detected_sections": ["experience", "skills"],
                    "requirement_coverage_hints": ["no explicit extra artefact requirement detected"],
                },
            ),
        )

        def fake_execute_prompt(setting, prompt, *, document=None, **kwargs):
            assert "Content mode: provider_document" in prompt
            assert "Artefact analysis:" in prompt
            assert "Artefact analysis index:" in prompt
            assert "Submission strategy:" in prompt
            assert "Section emphasis guidance:" in prompt
            assert document is not None
            assert document["mime_type"] == "application/pdf"
            assert document["data"] == b"%PDF-sample"
            return "### Headline\nTechnical Program Manager"

        monkeypatch.setattr("app.services.ai._execute_prompt", fake_execute_prompt)

        with session_local() as db:
            user = db.get(User, user_id)
            job = db.get(Job, job_id)
            artefact = db.get(Artefact, artefact_id)

            output = generate_job_artefact_draft(
                db,
                user,
                job,
                artefact,
                draft_kind="resume_draft",
            )
            db.commit()

            assert output.source_context["content_mode"] == "provider_document"
            assert output.source_context["provider_document_mime_type"] == "application/pdf"
            assert output.source_context["used_extracted_text"] is False
            assert output.source_context["required_artefact_types"] == []
    finally:
        app.dependency_overrides.clear()


def test_call_gemini_maps_raw_timeout_error(monkeypatch) -> None:
    setting = AiProviderSetting(
        provider="gemini",
        model_name="gemini-flash-latest",
        api_key_encrypted="sealed",
    )

    monkeypatch.setattr("app.services.ai._open_provider_api_key", lambda setting: "gemini-secret-1234")
    monkeypatch.setattr("app.services.ai.request.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError()))

    try:
        _call_gemini(setting, "hello")
    except AiExecutionError as exc:
        assert "Google Gemini timed out before returning a response" in str(exc)
    else:
        raise AssertionError("Expected AiExecutionError")


def test_call_gemini_uses_extended_timeout_for_document_payload(monkeypatch) -> None:
    setting = AiProviderSetting(
        provider="gemini",
        model_name="gemini-flash-latest",
        api_key_encrypted="sealed",
    )
    captured: dict[str, object] = {}

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return b'{"candidates":[{"content":{"parts":[{"text":"ok"}]}}]}'

    def _fake_urlopen(*args, **kwargs):
        captured.update(kwargs)
        return _FakeResponse()

    monkeypatch.setattr("app.services.ai._open_provider_api_key", lambda setting: "gemini-secret-1234")
    monkeypatch.setattr("app.services.ai.request.urlopen", _fake_urlopen)

    result = _call_gemini(
        setting,
        "hello",
        document={"mime_type": "application/pdf", "data": b"pdf"},
    )

    assert result == "ok"
    assert captured["timeout"] == 60


def test_execute_prompt_enriches_ai_execution_error_with_diagnostics(monkeypatch) -> None:
    setting = AiProviderSetting(
        provider="gemini",
        model_name="gemini-flash-latest",
        api_key_encrypted="sealed",
    )

    def _raise(*args, **kwargs):
        raise AiExecutionError("Google Gemini timed out before returning a response. Try again or reduce the request size.")

    monkeypatch.setattr("app.services.ai._call_gemini", _raise)

    try:
        _execute_prompt(
            setting,
            "hello",
            document={"mime_type": "application/pdf", "data": b"pdf"},
            action="tailoring_guidance",
            content_mode="provider_document",
            job_uuid="job-123",
            artefact_uuid="artefact-456",
        )
    except AiExecutionError as exc:
        assert exc.diagnostics["action"] == "tailoring_guidance"
        assert exc.diagnostics["provider"] == "gemini"
        assert exc.diagnostics["model"] == "gemini-flash-latest"
        assert exc.diagnostics["content_mode"] == "provider_document"
        assert exc.diagnostics["document_attached"] is True
        assert exc.diagnostics["timeout_seconds"] == 60
        assert exc.diagnostics["job_uuid"] == "job-123"
        assert exc.diagnostics["artefact_uuid"] == "artefact-456"
        summary = _ai_debug_summary(exc)
        assert "action=tailoring_guidance" in summary
        assert "provider=gemini" in summary
        assert "content_mode=provider_document" in summary
        assert "timeout_seconds=60" in summary
    else:
        raise AssertionError("Expected AiExecutionError")
