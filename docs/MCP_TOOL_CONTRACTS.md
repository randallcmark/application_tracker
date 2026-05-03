# MCP Tool Contracts Draft

## Purpose

This document defines draft MCP resources, tools, naming conventions, descriptions, and permission scopes for Application Tracker.

It is a planning document. Tool names and schemas may change before implementation, but the naming taxonomy should be treated as the starting contract.

---

## Naming rules

Tool names must follow:

```text
domain_object_action
```

Optional qualifier form:

```text
domain_object_qualifier_action
```

Rules:

- snake_case only
- maximum 60 characters
- descriptions maximum 250 characters
- names should use stable product/domain language
- names should not expose internal route, function, or service names
- names should be discoverable by an agent scanning available tools
- names should be reusable across UI and headless workflows

Good examples:

```text
job_context_get
job_application_list
artefact_markdown_get
competency_evidence_list
employer_rubric_map
ai_output_create
```

Avoid:

```text
get_all_data
query_database
update_any_record
agent_do_anything
createVisibleAIOutput
run_ai_workflow_v2
```

---

## Domain taxonomy

Initial domains:

```text
jobseeker
job
application
artefact
competency
employer
interview
followup
task
note
inbox
focus
board
ai_output
```

Guidance:

- use `jobseeker` for the human career owner
- use `employer` for employer-provided briefs, rubrics, values, and assessment criteria
- use `ai_output` for visible generated output records
- avoid `user` unless the tool is about account/auth identity

---

## Scope model

Initial MCP support should expose:

- read-only resources/tools
- visible Markdown output creation
- no workflow mutation

Future support may add save/promote tools and state-changing workflows.

---

## Permission scopes

Initial scopes:

```text
mcp:read_profile
mcp:read_jobs
mcp:read_artefacts
mcp:read_competencies
mcp:read_focus
mcp:write_ai_outputs
```

Deferred scopes:

```text
mcp:write_notes
mcp:write_artefacts
mcp:write_competency_evidence
mcp:mutate_workflow
mcp:admin
```

---

## V1 tools

V1 should prove safe agent-assisted operation with scoped reads and visible Markdown output creation.

### `jobseeker_profile_get`

Description:

```text
Get the jobseeker profile and goal context needed for career and application guidance.
```

Required scope:

```text
mcp:read_profile
```

Returns compact Markdown-friendly profile context. Do not return secrets or account security details.

---

### `focus_summary_get`

Description:

```text
Get the current Focus summary, including counts and the most important work queues.
```

Required scope:

```text
mcp:read_focus
```

Returns the same kind of data needed to populate the Focus view, but in compact Markdown-friendly form.

---

### `job_list`

Description:

```text
List jobs with metadata, company, role, status, dates, and key workflow indicators.
```

Required scope:

```text
mcp:read_jobs
```

Supports filters where useful, such as status, active-only, applied-only, stale-only, or upcoming-interview.

This is a general list of jobs. More specific lists may be added later.

---

### `job_context_get`

Description:

```text
Get Markdown-friendly context for one job, including description, status, notes, artefacts, and activity.
```

Required scopes:

```text
mcp:read_jobs
mcp:read_artefacts
```

Returns curated job context for AI reasoning. Do not return unrelated user data.

---

### `artefact_markdown_get`

Description:

```text
Get the Markdown preview or extraction status for a user-owned artefact.
```

Required scope:

```text
mcp:read_artefacts
```

Returns Markdown if available, or extraction/preview status if not available. The source file remains canonical.

---

### `competency_evidence_list`

Description:

```text
List saved competency evidence summaries for interview and application preparation.
```

Required scope:

```text
mcp:read_competencies
```

Returns compact evidence summaries. Full detail can be added later if needed.

---

### `ai_output_create`

Description:

```text
Save externally generated Markdown as a visible, source-linked AI output. Does not change workflow state.
```

Required scope:

```text
mcp:write_ai_outputs
```

Input shape:

```json
{
  "job_id": "optional job uuid",
  "artefact_id": "optional artefact uuid",
  "output_type": "job_fit_report | tailoring_guidance | draft | employer_competency_mapping | focus_nudge | other",
  "title": "Short title",
  "markdown": "Markdown content",
  "source_context": {
    "tool_context": "What the AI used",
    "source_ids": []
  }
}
```

Output shape:

```json
{
  "status": "created",
  "output_id": 123,
  "title": "Short title",
  "url": "/jobs/...#ai-output-123",
  "warnings": []
}
```

Rules:

- does not mutate workflow state
- renders through safe Markdown viewer
- records `created_via = mcp`
- records source context
- records tool/client metadata where available

---

## V1 workflow examples

### External job fit report

```text
job_list
job_context_get
artefact_markdown_get
competency_evidence_list
external AI generates Markdown
ai_output_create with output_type=job_fit_report
```

### External resume tailoring suggestion

```text
job_context_get
artefact_markdown_get
external AI generates Markdown
ai_output_create with output_type=tailoring_guidance
```

### External employer rubric mapping

```text
job_context_get
competency_evidence_list
external AI maps rubric to evidence
ai_output_create with output_type=employer_competency_mapping
```

---

## V2 read/list tool candidates

V2 should begin mapping the data operations that populate main UI views.

Candidate tools:

```text
job_application_list
board_summary_get
board_column_list
inbox_item_list
inbox_item_get
interview_list
followup_list
task_list
note_list
ai_output_list
```

### `job_application_list`

Description:

```text
List jobs that have reached application state, with metadata, status, dates, and next actions.
```

### `board_summary_get`

Description:

```text
Get board status counts and column summaries for the jobseeker workflow board.
```

### `board_column_list`

Description:

```text
List jobs in a board column with compact card metadata and workflow indicators.
```

### `inbox_item_list`

Description:

```text
List inbox items awaiting review, including source, extracted role data, and triage status.
```

### `inbox_item_get`

Description:

```text
Get details for one inbox item awaiting jobseeker review.
```

### `interview_list`

Description:

```text
List interviews with dates, job context, preparation state, and upcoming indicators.
```

### `followup_list`

Description:

```text
List follow-ups with due dates, job context, status, and suggested next action.
```

### `task_list`

Description:

```text
List job-search tasks with status, due dates, related job, and priority indicators.
```

### `note_list`

Description:

```text
List notes with related job, created date, tags, and compact Markdown preview.
```

### `ai_output_list`

Description:

```text
List visible AI outputs with type, source context, related job or artefact, and created date.
```

---

## Deferred write tools

Do not implement these in V1.

Candidate future tools:

```text
job_status_update
inbox_item_accept
inbox_item_dismiss
followup_complete
task_complete
note_create
artefact_attach
ai_output_promote
```

These require:

- explicit write scopes
- audit logging
- owner scoping
- dry-run where appropriate
- confirmation for destructive or workflow-mutating actions

---

## Higher-level workflow tools

Higher-level tools can be added after the V1 context/read/write foundation is proven.

Candidate tools:

```text
job_fit_report_create
artefact_tailoring_suggest
artefact_draft_create
employer_rubric_map
interview_prep_pack_create
focus_next_move_create
```

Implementation decision:

- if the app performs the model call, these tools require app-embedded AI provider configuration
- if the external AI client performs reasoning, prefer context tools plus `ai_output_create`

For the API-token-friction problem, prefer external reasoning plus `ai_output_create` first.

---

## Contract decision

The initial MCP contract should support agent-assisted usage without requiring app-owned AI provider calls.

Therefore V1 should expose enough context for the external AI client to reason, plus a single safe output creation tool. Higher-level generation tools can follow after the interaction, permission, and audit model is proven.
