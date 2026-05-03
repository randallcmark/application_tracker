# Codex Task: Plan MCP Integration With Tool Taxonomy

## Goal

Add planning documentation for MCP support in Application Tracker.

MCP is being considered as an alternative AI execution path because app-embedded AI features require provider API keys, while some users may already have an AI client or subscription but no API access.

The aim is to expose safe, user-owned Application Tracker workflows to an external AI client while keeping Application Tracker as the system of record.

This task is documentation and architecture planning only. Do not implement runtime MCP support yet.

---

## Current product constraints

Application Tracker already has AI features and AI output contracts.

The existing AI principles must remain true:

- AI is optional.
- AI output is visible and inspectable.
- AI does not silently mutate jobs, artefacts, profile data, competency evidence, notes, or workflow state.
- The app remains useful when no provider is configured.
- Generated content should be Markdown-first where possible.
- Source context and provenance should be preserved.

---

## Core question

Can Application Tracker support an MCP mode where:

- the app exposes safe tools/resources
- the user's external AI client performs reasoning/generation
- the AI client calls MCP tools to save visible Markdown outputs back into the app
- the app avoids requiring its own provider API key for these workflows

---

## Tool taxonomy requirements

MCP tool names are an agent-facing product contract. They should be designed before runtime implementation.

Use:

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
- names must use stable product/domain language
- names must not expose internal route, function, or service names
- names must be reusable across UI and headless workflows

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

Avoid `user` unless a tool is specifically about account identity or authentication. Use `jobseeker` for the human career owner.

---

## Deliverables

Create these planning docs:

```text
docs/MCP_INTEGRATION_STRATEGY.md
docs/MCP_ARCHITECTURE_PLAN.md
docs/MCP_SECURITY_MODEL.md
docs/MCP_TOOL_CONTRACTS.md
docs/MCP_TASK_MAP.md
```

Update any relevant doc index if one exists.

Do not change application code.

---

## Required topics

The docs should cover:

- why MCP is being considered
- embedded AI versus MCP-assisted AI
- app remains system of record
- MCP as optional mode
- feasibility and interaction model
- security hardening
- domain_object_action tool taxonomy
- 60-character tool name limit
- 250-character tool description limit
- workflow-oriented tools
- UI-operation tools for future headless mode
- read/write separation
- headless mode guardrails
- whether there is an Arazzo-like workflow model for MCP
- initial tool/resource contracts
- recommended implementation sequence

---

## Design position to capture

MCP should be treated as an alternative AI execution path, not as a replacement for the UI or the app's workflow model.

The safest early model is:

1. expose read-only scoped context tools
2. allow creation of visible Markdown AI outputs
3. avoid workflow state mutation
4. defer destructive/state-changing tools
5. keep all writes auditable
6. use external AI reasoning first to avoid app-owned provider API dependency

---

## V1 tool candidates

Initial V1 tools should be limited to scoped context and safe output creation:

```text
jobseeker_profile_get
focus_summary_get
job_list
job_context_get
artefact_markdown_get
competency_evidence_list
ai_output_create
```

`ai_output_create` should save externally generated Markdown as visible output and must not change workflow state.

---

## V2 tool candidates

V2 should map the operations that populate the main UI views into MCP tools.

Candidate read/list tools:

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

Deferred write tools:

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

Do not implement mutation tools in the first runtime slice.

---

## Higher-level workflow tools

Higher-level workflow tools may be added after the V1 context/write foundation is proven.

Candidate tools:

```text
job_fit_report_create
artefact_tailoring_suggest
artefact_draft_create
employer_rubric_map
interview_prep_pack_create
focus_next_move_create
```

For each workflow, decide whether:

1. the app performs a provider-backed AI call, or
2. the external AI client reasons and the app persists output.

For the API-token friction problem, prefer external AI reasoning first.

---

## Tool design guidance

Prefer workflow or UI-operation tools, not raw database tools.

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
```

Initial tools should not silently mutate jobs, artefacts, profile, notes, competency evidence, or workflow state.

---

## Headless mode guidance

Headless mode should be possible eventually, but not uncontrolled.

Capture guardrails:

- explicit scopes
- visible outputs
- audit logs
- source context
- dry-run for future state changes
- confirmation for destructive actions
- no broad data export by default
- MCP disabled unless configured

---

## Security topics

Include:

- token/scopes model
- owner scoping
- prompt injection from external documents
- avoiding broad data exfiltration
- no public network exposure by default
- token revocation
- auditability
- safe Markdown rendering
- no hidden state mutation

---

## Non-goals

Do not implement MCP runtime support.

Do not change existing AI provider integration.

Do not remove embedded AI features.

Do not change application schema.

Do not expose raw DB access.

Do not add broad read-all tools.

Do not add state-changing MCP tools yet.

Do not make MCP required for normal app usage.

---

## Acceptance criteria

The task is complete when:

- MCP strategy is documented
- architecture options are documented
- security model is documented
- tool taxonomy is documented
- initial tool contracts are drafted
- V1 and V2 task sequencing is clear
- the first recommended implementation slice is clear
- no application behaviour has changed

---

## Validation

This is a docs-only task.

Run doc validation if available.

Do not claim application tests are required unless code changes are made.

---

## First implementation recommendation to document

The recommended first technical slice should be:

1. MCP disabled by default.
2. Read-only context tools.
3. One safe write tool: `ai_output_create`.
4. No workflow state mutation.
5. Owner-scoped access only.
6. Generated content saved as visible Markdown output with `created_via = mcp`.

This allows an external AI client to perform reasoning and save results back to the app without requiring the app to call a provider API.
