# Execution Plan: Free-Text Markdown Rendering Audit

Status: Complete

Owner: Agent

Created: 2026-05-02

Last Updated: 2026-05-02

## Goal

Identify every free-text field and page that renders user-authored, extracted, captured, or
AI-generated text so the first shared Markdown renderer slice can be implemented safely.

## Non-Goals

- renderer implementation
- schema changes
- UI redesign
- prompt or provider changes
- search, extraction, or export implementation

## Context

- `docs/DOCUMENT_HANDLING_STRATEGY.md`
- `docs/DOCUMENT_HANDLING_ARCHITECTURE.md`
- `docs/DOCUMENT_HANDLING_TASK_MAP.md`
- `docs/exec-plans/active/document-handling-foundation.md`
- `docs/agent/security-rules.md`
- `docs/agent/ai-feature-rules.md`

## Acceptance Criteria

- Audit covers job descriptions, notes, interview notes, application notes, follow-up content,
  competency evidence, AI outputs, generated drafts, artefact summaries, email capture text, and
  employer rubric text.
- Each audited item records source model, storage field, current rendering path, risk, and
  recommended handling.
- Audit identifies the first low-risk surfaces for shared Markdown rendering.
- No product behavior changes are made during the audit.

## Plan

1. Inspect models for free-text fields.
2. Inspect route/template rendering for those fields.
3. Classify content source as user-authored, captured, extracted, or AI-generated.
4. Record rendering safety risks and recommended Markdown handling.
5. Choose first renderer implementation surfaces, likely AI outputs plus one low-risk text surface.

## Current Rendering Summary

The app already has Markdown-like rendering in several route modules, but it is duplicated and
limited:

- `app/api/routes/job_detail.py` renders job descriptions and Job Workspace AI output through
  route-local `_render_markdown_blocks` helpers.
- `app/api/routes/inbox.py` renders Inbox review AI output through another local helper.
- `app/api/routes/focus.py` renders Focus AI output through another local helper.
- `app/api/routes/competencies.py` renders competency STAR-shaping AI output through another local
  helper.

These helpers escape text before applying limited Markdown handling, which is safer than raw HTML
but inconsistent. They do not provide one shared policy for links, tables, code blocks, unsafe
protocols, or future document/rubric content.

Most user notes and metadata fields are rendered with `escape(...)` inside plain paragraphs,
definition lists, or `<pre>` blocks. That is safe for HTML injection but does not give users
consistent Markdown rendering.

## Audit Table

| Surface | Source model | Storage field | Source type | Current rendering | Risk | Recommended handling |
| --- | --- | --- | --- | --- | --- | --- |
| Job Workspace description | `Job` | `description_raw` | manual, captured, email-derived, imported | `job_detail._render_description_markdown`; route-local limited Markdown renderer | Medium: important user/captured content already uses ad hoc Markdown; future renderer changes may alter job readability | Move to shared safe renderer after AI outputs; preserve current headings, bullets, bold, italics, and plain-text paragraph behavior |
| Inbox review description editor | `Job` | `description_raw` | captured, email-derived, user-edited | `<textarea>` with escaped value; no rendered preview | Low: edit-only path is safe; preview behavior belongs to later UX work | No first-slice rendering change; shared renderer can support a later preview if needed |
| Board job cards | `Job` | title/company/location/source only; description not shown | user/captured summary metadata | escaped inline text | Low: no long free text rendered | No Markdown handling needed |
| Job timeline journal | `Communication` | `subject`, `notes` | user notes plus system-generated lifecycle notes | escaped text in `_timeline_event` paragraphs | Medium: user notes may benefit from Markdown, but system notes/provenance are mixed in same model | Keep escaped for first slice; after shared renderer lands, render only user-authored note bodies with Markdown and leave system subjects plain |
| Follow-up notes | `Communication` | `notes`, `follow_up_at` | user-authored or system-generated follow-up context | escaped snippets in Focus, Board, and Job Workspace follow-up lists | Low/Medium: snippets need compact plain rendering; Markdown could add visual noise | Keep plain escaped snippets; consider Markdown only in expanded journal/detail view |
| Interview notes | `InterviewEvent` | `notes` | user-authored interview prep/context | escaped paragraph in job detail interview list; captured as communication note too | Medium: likely structured prep notes, but currently a compact list | Defer until shared renderer exists and a dedicated interview prep surface needs it |
| Application notes | `Application` | `notes` | user-authored application context | escaped paragraph in job detail application list | Low/Medium: useful but less central than AI/job description | Defer; render through shared renderer only in an expanded application detail surface |
| Artefact metadata notes | `Artefact` | `notes` | user-authored metadata plus system provenance strings for saved AI drafts | escaped paragraph in artefact library; regex-parsed provenance for AI-draft notes | Medium: field mixes free notes and machine-readable provenance text | Keep escaped until provenance is structured; do not Markdown-render machine-readable provenance strings |
| Artefact source files | `Artefact` + storage provider | `storage_key`, stored bytes | uploaded source, saved AI Markdown drafts, generated artefacts | download only; no internal source/Markdown view | Medium/High for future work: source preservation and Markdown view need clear separation | Defer to Artefact Markdown Representation Design; original source remains canonical |
| Artefact summaries and extracted text for AI | service-level summaries/excerpts | storage-derived text, summary strings | extracted or derived content | used inside prompts; not generally rendered directly | Medium: source text can contain prompt-injection-like instructions | Treat as untrusted source data; use Markdown representation and prompt boundary rules before expanding UI rendering |
| AI output: Job Workspace | `AiOutput` | `body` | AI-generated Markdown-like text | `job_detail._render_ai_markdown`; route-local limited renderer | High leverage: multiple output types and generated drafts already expect Markdown-like structure | First renderer slice: replace route-local rendering with shared safe renderer while preserving current output layout |
| AI output: Inbox review | `AiOutput` | `body` | AI-generated review guidance | `inbox._render_markdown_blocks`; route-local limited renderer | High leverage: same duplicated policy as Job Workspace | Include in first renderer slice after shared helper is available |
| AI output: Focus nudge | `AiOutput` | `body` | AI-generated recommendation | `focus._render_markdown_blocks`; route-local limited renderer | Medium: compact recommendation surface, but duplicate renderer | Include in first renderer slice or second pass with AI outputs as a group |
| AI output: Competency STAR shaping | `AiOutput` | `body` | AI-generated STAR guidance | `competencies._render_markdown_blocks`; route-local limited renderer; parsed separately for save-back | High: rendered Markdown and parser both depend on output structure | Render with shared renderer, but do not change STAR save-back parser behavior in same slice |
| Competency evidence STAR fields | `CompetencyEvidence` | `situation`, `task`, `action`, `result`, `evidence_notes`, `tags` | user-authored structured evidence | escaped definition-list fields and notes in competency cards | Medium: STAR fields are structured text but should stay easy to scan | Defer Markdown rendering for STAR fields until shared renderer exists; consider Markdown for `evidence_notes` first, not compact STAR labels |
| Competency evidence form inputs | `CompetencyEvidence` | STAR fields and notes | user-authored | escaped textarea values | Low: edit controls are safe | No rendering change |
| Email capture source | `EmailIntake` | `body_text`, `body_html` | pasted/captured email source | `body_text` rendered in Job Workspace provenance as escaped `<pre>`; `body_html` preserved but not rendered | Medium/High: source material can contain HTML and prompt-injection content | Keep raw email source escaped/preformatted; do not Markdown-render raw HTML; future normalized Markdown view must be separate from canonical source |
| Inbox email candidate descriptions | `Job` from `EmailIntake` | `description_raw` | deterministic extraction from email | editable textarea in Inbox, rendered as job description after acceptance/open workspace | Medium: extracted email snippets can be noisy or multi-job | Shared renderer should treat accepted `description_raw` as Markdown-compatible plain text; source email stays separate |
| User profile free text | `UserProfile` | `target_roles`, `target_locations`, `preferred_industries`, `excluded_industries`, `constraints`, `positioning_notes` | user-authored profile context | settings form textareas; profile values mainly consumed by prompts/focus chips, not long rendered prose | Medium for AI context; low for current UI rendering | Keep settings escaped; later normalize profile-to-Markdown summaries for AI prompts rather than render raw profile text as Markdown |
| Employer rubric text | future model or `AiOutput.source_context` | TBD | pasted employer rubric/interview brief | not implemented | High future risk: external rubric text may look like instructions | Implement only after shared renderer; preserve pasted source, normalize Markdown separately, and treat source as data in prompts |
| Generated draft saved as artefact | `AiOutput` -> `Artefact` | `AiOutput.body`, stored artefact bytes, `Artefact.notes` | AI-generated Markdown promoted by explicit user action | AI output rendered in Job Workspace; saved artefact is downloadable `text/markdown`; provenance in `Artefact.notes` escaped/parsed | Medium: output Markdown rendering and saved source lineage must stay aligned | Use shared renderer for `AiOutput.body`; defer artefact Markdown view and structured provenance to artefact Markdown design |

## First Renderer Slice Recommendation

Implement the shared renderer in this order:

1. Add a shared safe Markdown rendering helper with tests for headings, paragraphs, unordered lists,
   bold, italic, plain text, escaped HTML, script tags, event handlers, unsafe links, and code-ish
   text.
2. Replace route-local AI output renderers in Job Workspace, Inbox review, Focus, and Competencies
   with the shared helper, preserving current CSS class hooks.
3. Move Job Workspace `Job.description_raw` rendering to the shared helper after AI output behavior
   is covered.
4. Leave notes, artefact metadata notes, email provenance, profile fields, and competency STAR fields
   escaped until dedicated expanded views need Markdown rendering.

Do not combine this with schema changes, artefact Markdown representation, employer rubric mapping,
search, or export.

## Follow-On Tasks

- Shared safe Markdown renderer implementation.
- AI output Markdown standardization across all current AI surfaces.
- Job description renderer migration.
- Artefact Markdown representation design.
- Employer rubric mapping once shared rendering and AI-output Markdown display are complete.

## Progress Log

- 2026-05-02: Created plan as the first implementation task for Document Handling Foundation.
- 2026-05-02: Completed audit. Found duplicated route-local Markdown-like renderers for AI output
  and job descriptions, while notes/provenance/metadata are mostly escaped plain text.

## Decisions

- The audit precedes renderer implementation.
- Existing plain text should remain readable when rendered as Markdown.
- The first implementation slice should centralize existing AI output rendering before expanding
  Markdown to notes, artefacts, profile fields, employer rubrics, search, or export.

## Validation

Commands to run before completion:

```sh
bash scripts/validate-harness.sh
git diff --check
```

## Risks

- Some text may already contain HTML fragments. Treat all rendered content as untrusted until the
  audit proves otherwise.
