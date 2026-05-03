# MCP Feature Task Map

## Purpose

This task map breaks MCP exploration into safe, reviewable tasks.

The first tasks are planning and contract definition only. Runtime implementation should follow only after the taxonomy, security, and interaction model are agreed.

---

## Task 1: MCP strategy and decision docs

### Goal

Add product and architecture docs for MCP as an alternative AI execution path.

### Deliverables

- `docs/MCP_INTEGRATION_STRATEGY.md`
- `docs/MCP_ARCHITECTURE_PLAN.md`
- `docs/MCP_SECURITY_MODEL.md`
- update doc index if present

### Acceptance criteria

- explains why MCP is being considered
- distinguishes embedded AI from MCP-assisted AI
- states that MCP is optional
- states that app remains system of record
- defines non-mutating default posture
- identifies open decisions

---

## Task 2: MCP tool taxonomy and contract design

### Goal

Define initial MCP naming rules, resources, tools, permissions, and output contracts.

### Deliverables

- `docs/MCP_TOOL_CONTRACTS.md`

### Requirements

Tool names must follow:

```text
domain_object_action
```

Constraints:

- snake_case only
- maximum 60 characters
- descriptions maximum 250 characters
- names use domain/product language, not internal service names

### Include

- V1 read-only tools
- V1 visible output creation tool
- V2 UI-operation list/read candidates
- deferred mutation tools
- permission scopes
- request/response examples
- source context and provenance fields

### Acceptance criteria

- no raw database tools
- no broad read-everything tool
- first implementation candidate identified
- tools are taxonomy-driven and extensible

---

## Task 3: MCP deployment decision

### Goal

Decide whether MCP starts as embedded server, sidecar, or local CLI server.

### Deliverables

- `docs/MCP_DEPLOYMENT_DECISION.md`

### Options

- embedded FastAPI route/server
- Docker Compose sidecar
- local CLI/server
- disabled by default

### Acceptance criteria

- QNAP/local Docker deployment considered
- network exposure considered
- auth/token model considered
- first implementation mode selected

---

## Task 4: MCP V1 read-only prototype

### Goal

Implement a minimal MCP server exposing read-only scoped context tools.

### Scope

- no writes except possibly feature-flagged stub responses
- no AI generation
- no workflow mutation

### Candidate tools

```text
jobseeker_profile_get
focus_summary_get
job_list
job_context_get
artefact_markdown_get
competency_evidence_list
```

### Acceptance criteria

- owner scoping enforced
- MCP disabled unless configured
- no secrets exposed
- tool names obey taxonomy
- descriptions are 250 characters or fewer
- tests cover unauthorised access
- docs explain local setup

---

## Task 5: MCP visible output write tool

### Goal

Allow an external AI client to save generated Markdown into Application Tracker.

### Tool

```text
ai_output_create
```

### Inputs

- job id or context id
- output type
- title
- markdown content
- source context
- optional client metadata

### Acceptance criteria

- creates visible output only
- no workflow state mutation
- Markdown sanitized on render
- output is marked `created_via = mcp`
- owner scoped
- tests cover invalid ownership and missing permissions

---

## Task 6: First external-reasoning workflow validation

### Goal

Validate the external-AI reasoning model without app-owned provider calls.

### Candidate flow

```text
job_list
job_context_get
artefact_markdown_get
competency_evidence_list
external AI generates Markdown
ai_output_create
```

### Acceptance criteria

- job fit report can be created without app-owned provider call
- output is visible in Job Workspace
- source context is preserved
- no job status changes
- flow is documented

---

## Task 7: MCP V2 UI-operation read tools

### Goal

Begin mapping the data operations that populate main UI views into MCP tools.

### Candidate tools

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

### Acceptance criteria

- tools map to real UI data needs
- tools return compact summaries by default
- tools obey naming and description constraints
- no mutation tools included

---

## Task 8: Higher-level workflow tools

### Goal

Add workflow-oriented MCP tools after the V1 context/write foundation is proven.

### Candidate tools

```text
job_fit_report_create
artefact_tailoring_suggest
artefact_draft_create
employer_rubric_map
interview_prep_pack_create
focus_next_move_create
```

### Decision point

For each workflow tool decide whether:

1. the app performs provider-backed AI calls, or
2. the external AI client reasons and the app persists output.

For the API-token friction problem, prefer external AI reasoning first.

---

## Task 9: Deferred mutation tools and headless guardrails

### Goal

Define and eventually implement safe state-changing tools.

### Candidate tools

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

### Requirements

- explicit scopes
- audit log
- dry-run where appropriate
- confirmation for destructive or workflow-changing actions
- owner scoping
- clear UI visibility after mutation

---

## Recommended first Codex task

Start with docs only:

```text
Add MCP integration strategy, architecture, security model, taxonomy-driven tool contracts, and task map. Do not implement runtime MCP support yet.
```

This lets the project settle interaction, security, and naming before code is added.
