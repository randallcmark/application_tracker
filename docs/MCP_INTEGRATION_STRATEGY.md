# MCP Integration Strategy

## Purpose

This document defines the strategic direction for adding MCP support to Application Tracker.

MCP is being considered because the current app-embedded AI model requires provider API keys. A jobseeker may already have access to an AI client, such as a paid ChatGPT or Claude subscription, but not have separate API access. MCP can let the user bring their own AI client while Application Tracker remains the system of record.

## Strategic position

MCP should be an alternative AI execution path, not a replacement for the app UI or the existing AI provider abstraction.

Application Tracker should remain useful in three modes:

1. no AI configured
2. app-embedded AI provider configured
3. external AI client connected through MCP

The same product rules apply in all modes:

- AI is optional.
- AI output is visible and inspectable.
- AI should not silently mutate jobs, artefacts, profile data, competency evidence, notes, or workflow state.
- Generated content should be Markdown-first.
- Source context and provenance should be preserved.
- User-owned data must remain owner-scoped.

## Vision adaptation

Application Tracker is a user-first, goal-aware job-seeking workspace.

With MCP, it can also become an agent-operable career workspace. The user can work through the UI or through an external AI assistant while Application Tracker remains the durable store for jobs, artefacts, evidence, notes, and visible generated outputs.

Suggested vision extension:

> Application Tracker should remain useful with or without embedded AI. Where users bring their own AI client, the product should expose safe, auditable MCP workflows that allow the assistant to read relevant context, generate Markdown outputs, and save visible work products without silently mutating the user's career data.

## Initial MCP goal

The first MCP pass should not wrap every internal AI generation button as a server-side AI tool.

The first pass should establish:

1. a stable tool naming taxonomy
2. read-only context tools
3. one safe write tool for visible Markdown AI outputs
4. no workflow state mutation
5. owner-scoped access
6. MCP disabled unless configured

This lets an external AI client perform reasoning and save results back to Application Tracker without the app needing to call an AI provider API.

## Tool taxonomy

MCP tool names are an agent-facing product contract. They must be stable, short, and discoverable.

Use:

```text
domain_object_action
```

Use snake_case only.

Hard constraints:

- tool names must be 60 characters or fewer
- tool descriptions must be 250 characters or fewer
- names should use product/domain language, not internal service names
- names should avoid ambiguous terms where possible
- names should be extensible across UI-backed and headless workflows

Optional qualifier form:

```text
domain_object_qualifier_action
```

Examples:

```text
job_context_get
job_application_list
artefact_markdown_get
competency_evidence_list
employer_rubric_map
ai_output_create
```

## Domain taxonomy

Prefer product/domain terms over implementation terms.

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

Avoid `user` for jobseeker-facing tools unless the tool truly concerns account identity or authentication. `user` can be ambiguous in agent systems because it may refer to the app user, AI client user, operating system user, or authenticated account.

Use `jobseeker` for the human career owner where useful.

Use `employer` for external employer-provided material, such as rubrics, briefs, values, and competency frameworks.

## V1 scope

V1 should support read-only context plus visible Markdown output creation.

Recommended V1 tools:

```text
jobseeker_profile_get
focus_summary_get
job_list
job_context_get
artefact_markdown_get
competency_evidence_list
ai_output_create
```

V1 should not add mutation tools such as accepting inbox items, changing job status, completing tasks, or overwriting artefacts.

## V2 direction

V2 should map the operations that populate the main UI views into MCP tools.

The goal is to support AI-first and headless usage without bypassing the app's domain model.

Likely V2 read/list tools:

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

Write tools should require explicit scopes, audit logging, and in some cases dry-run plus confirmation.

## Interaction model

The preferred initial MCP interaction model is:

```text
External AI client reads scoped context
External AI client reasons and generates Markdown
External AI client calls ai_output_create
Application Tracker stores visible output with source context
User reviews in the app UI or through follow-up MCP reads
```

This directly addresses the API-token friction problem because the app does not need to perform the model call.

## Arazzo-like workflow question

Arazzo describes API workflows over OpenAPI-style operations. MCP provides tools, resources, and prompts, but should not be treated as a full workflow choreography language by itself.

Application Tracker should encode workflow in:

1. coarse-grained product tools
2. strict tool schemas
3. prompt/workflow docs for agents
4. service-layer orchestration inside the app where needed

Do not expose many tiny database-style tools and expect the external AI client to invent safe workflows.

## Decision statement

MCP is worth exploring as a second AI execution path because it can reduce API-key friction, support AI-first workflows, and make Application Tracker more composable.

The first implementation should establish a strict naming taxonomy, read-only context access, and safe visible Markdown output creation. Broader UI-equivalent operations and state-changing tools should be added only after the permission, audit, and confirmation model is proven.
