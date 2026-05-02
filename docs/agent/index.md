# Agent Operating Index

This directory tells agents how to work in this repository. Read this page first, then follow only the route that matches the task.

## Principles

- Repository knowledge is the system of record.
- Small accurate docs beat large stale manuals.
- The harness should improve when an agent gets stuck.
- Product intent, acceptance criteria, architecture constraints, and final risk calls need human judgment.
- Repeated rules should become mechanical checks when possible.

## Task Routes

- Product vision and roadmap: `docs/PRODUCT_VISION.md`, `docs/roadmap/implementation-sequencing.md`, and `docs/roadmap/task-map.md`.
- Product behavior: `docs/product/product-brief.md` and `docs/product/user-journeys.md`.
- Architecture or dependency changes: `docs/architecture/index.md` and `docs/architecture/boundaries.md`.
- Document handling, Markdown rendering, source preservation, search, or export: `docs/DOCUMENT_HANDLING_STRATEGY.md`, `docs/DOCUMENT_HANDLING_ARCHITECTURE.md`, and `docs/DOCUMENT_HANDLING_TASK_MAP.md`.
- Complex or multi-step work: `docs/agent/task-protocol.md` and `docs/exec-plans/template.md`.
- Model/risk/validation routing: `docs/agent/codex-routing.md`.
- UI work: `docs/agent/ui-ux-rules.md`.
- AI or agentic features: `docs/agent/ai-feature-rules.md`.
- Security-sensitive work: `docs/agent/security-rules.md`.
- Validation: `docs/agent/validation.md`.
- Documentation changes: `docs/agent/doc-maintenance.md`.
- Cleanup and quality work: `docs/quality/quality-score.md` and `docs/quality/technical-debt.md`.

## Default Workflow

1. Clarify product direction from the three planning hubs when the task touches roadmap or priority.
2. Read the smallest relevant behavior, architecture, validation, or feature docs.
3. Inspect existing code before proposing behavior or structure.
4. For complex work, create or update an execution plan in `docs/exec-plans/active/`.
5. Make the smallest coherent change.
6. Update docs when behavior, commands, constraints, or decisions change.
7. Run the documented validation commands.
8. Summarize the change, validation, and remaining risks.

## When To Create An Execution Plan

Create a plan when the work changes architecture, touches multiple subsystems, introduces new product behavior, changes data models, changes auth/security/privacy behavior, or requires more than one implementation pass.

Small bug fixes and isolated documentation edits can use a lightweight conversation plan.

## Harness Improvement Rule

If a task fails because the repository is hard for the agent to understand or verify, do not only fix the immediate issue. Add the missing route, doc, validation command, fixture, script, or architecture note so the next run has less ambiguity.
