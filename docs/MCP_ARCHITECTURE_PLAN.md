# MCP Architecture Plan

## Purpose

This document proposes an MCP architecture for Application Tracker.

The goal is to allow external AI clients to interact with Application Tracker through safe, owner-scoped tools and resources while preserving the app as the system of record.

---

## Architectural principles

1. MCP is an adapter, not the core domain model.
2. Existing services remain the source of business logic.
3. Tools should be workflow-oriented or UI-operation-oriented, not database-oriented.
4. Reads and writes should be separated.
5. Generation and persistence should be separated where possible.
6. All outputs should be Markdown-first.
7. All writes should be visible and auditable.
8. Owner scoping is mandatory.
9. MCP must not bypass existing auth, permission, or provenance rules.
10. The app must still work with no AI and no MCP.
11. Production-quality MCP requires OAuth 2.0 with Dynamic Client Registration or a documented self-hosted equivalent.

---

## Proposed architecture

```text
External AI Client
        ↓
OAuth/DCR client registration and consent
        ↓
MCP Server / Adapter
        ↓
MCP Tool Router
        ↓
Application Service Layer
        ↓
Domain Models / Storage
        ↓
Visible Markdown Outputs / Artefacts / Notes
```

The MCP server should call existing application services rather than directly manipulating models.

---

## Deployment options

### Option A: MCP server embedded in the FastAPI app

Pros:

- simplest packaging
- shares configuration and services
- easiest local deployment
- fewer moving parts
- can share OAuth/DCR implementation with the web app

Cons:

- exposes a new protocol surface inside the web app
- tighter coupling
- must be careful with auth and routing

### Option B: MCP sidecar service in Docker Compose

Pros:

- clearer separation
- can be enabled/disabled independently
- easier to secure at network boundary
- good for QNAP/local deployment

Cons:

- more deployment complexity
- needs shared config/auth
- needs service-to-service access to app or DB
- must integrate with OAuth/DCR or delegate auth to the app

### Option C: MCP CLI/server launched locally by user

Pros:

- good for local-first users
- avoids exposing MCP over network
- can connect to local app APIs
- strong privacy story

Cons:

- harder setup
- less friendly for QNAP/headless deployment
- depends on user machine availability
- may still need OAuth/DCR for standards-compatible external clients

### Recommendation

Start with Option B or C as the safest architecture decision.

For self-hosted QNAP use, a sidecar MCP service is attractive:

```text
app
worker
mcp
```

For first prototype, Option C may be safer because it can run locally and talk to the app's existing authenticated APIs.

Do not expose MCP publicly by default.

---

## Authentication and authorization model

MCP should use OAuth 2.0 with Dynamic Client Registration for production-quality support.

Static tokens or local-only trust may be acceptable for constrained development mode, but they are not the production model.

Application Tracker should conceptually act as:

```text
Authorization Server
  registers MCP clients
  collects user consent
  issues scoped tokens

Resource Server
  serves MCP tools and resources
  enforces scopes and owner access
```

In a small self-hosted deployment these may run inside the same FastAPI app.

---

## OAuth/DCR responsibilities

The architecture needs support for:

- dynamic client registration
- registered client records
- redirect URI validation
- Authorization Code with PKCE for user-facing clients where applicable
- scoped access tokens
- token expiry
- token revocation
- client revocation
- consent records
- client management UI
- audit logging

See `docs/MCP_OAUTH_DCR_PLAN.md`.

---

## Tool permission tiers

### Tier 0: Introspection

- list available tools
- list allowed scopes
- get current account/token summary

### Tier 1: Read-only context

- read jobseeker profile summary
- read focus summary
- list jobs
- get one job context
- read artefact Markdown preview
- list competency evidence summaries

### Tier 2: Create visible AI outputs

- save externally generated Markdown output
- attach source context
- mark output as MCP-created

### Tier 3: Higher-level AI workflow tools

- job fit report creation
- resume tailoring suggestion
- employer rubric mapping
- interview prep pack creation

If the app performs the model call, these require app AI provider configuration. If the external AI client reasons, these may simply orchestrate context and output creation.

### Tier 4: Promote or save derived content

- save AI output as artefact
- save AI output as note
- attach output to job
- save shaped STAR to evidence

### Tier 5: Mutate workflow state

- accept/dismiss inbox item
- change job status
- mark follow-up complete
- archive job

Initial production implementation should not expose runtime tools until OAuth/DCR foundations are in place. A constrained local prototype may stop at Tier 2.

---

## Resource and tool model

MCP should expose compact, Markdown-friendly, owner-scoped context.

Initial V1 tool candidates:

```text
jobseeker_profile_get
focus_summary_get
job_list
job_context_get
artefact_markdown_get
competency_evidence_list
ai_output_create
```

V2 should then map UI view operations into MCP tools:

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

---

## Workflow orchestration

There may not be a direct MCP equivalent of Arazzo for workflow sequencing.

Therefore Application Tracker should encode workflows in two places:

1. coarse-grained MCP tools that perform product-level orchestration internally
2. documentation/prompt resources that explain recommended sequences to agents

To solve API-token friction, prefer this initial model:

```text
External AI client reasons
Application Tracker supplies context + safe write tools
```

The app can still support app-embedded provider calls for UI-triggered actions.

---

## Headless operation

Headless mode should mean agent-operable, not uncontrolled.

Minimum requirements:

- OAuth/DCR client registration and scoped authorization
- read-only summary tools
- create visible Markdown output tools
- links back into the UI for review
- explicit promote/save tools later
- audit log
- no destructive state changes initially
- dry-run mode for state changes later

---

## Audit and provenance

Every MCP-created output should record:

```text
created_via = mcp
client_id
tool_name
tool_version
mcp_client_name if available
owner_id
source_context
input_summary
created_at
```

Do not store full external AI conversation transcripts by default.

---

## Initial implementation target

Start with planning and prerequisites:

1. Document MCP architecture and security model.
2. Define tool taxonomy and V1 tool contracts.
3. Add OAuth/DCR architecture and task plan.
4. Decide deployment mode.
5. Implement no production runtime MCP support until auth prerequisites are designed.

Then first technical slices:

1. OAuth/DCR foundation.
2. MCP disabled by default.
3. Expose read-only V1 context tools behind scoped authorization.
4. Add `ai_output_create` as the only write tool.
5. Store generated Markdown as visible output with `created_via = mcp`.
6. Do not mutate workflow state.
