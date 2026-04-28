# Agent Operating Index

This directory tells agents how to work in this repository. Read this page first, then follow only the route that matches the task.

## Principles

- Repository knowledge is the system of record.
- Small accurate docs beat large stale manuals.
- The harness should improve when an agent gets stuck.
- Product intent, acceptance criteria, architecture constraints, and final risk calls need human judgment.
- Repeated rules should become mechanical checks when possible.

## Task Routes

- Product behavior: `docs/product/product-brief.md` and `docs/product/user-journeys.md`.
- Architecture or dependency changes: `docs/architecture/index.md` and `docs/architecture/boundaries.md`.
- Complex or multi-step work: `docs/agent/task-protocol.md` and `docs/exec-plans/template.md`.
- Model/risk/validation routing: `docs/agent/codex-routing.md`.
- UI work: `docs/agent/ui-ux-rules.md`.
- AI or agentic features: `docs/agent/ai-feature-rules.md`.
- Security-sensitive work: `docs/agent/security-rules.md`.
- Validation: `docs/agent/validation.md`.
- Documentation changes: `docs/agent/doc-maintenance.md`.
- Cleanup and quality work: `docs/quality/quality-score.md` and `docs/quality/technical-debt.md`.

## Default Workflow

1. Clarify the task by reading the smallest relevant docs.
2. Inspect existing code before proposing behavior or structure.
3. For complex work, create or update an execution plan in `docs/exec-plans/active/`.
4. Make the smallest coherent change.
5. Update docs when behavior, commands, constraints, or decisions change.
6. Run the documented validation commands.
7. Summarize the change, validation, and remaining risks.

## When To Create An Execution Plan

Create a plan when the work changes architecture, touches multiple subsystems, introduces new product behavior, changes data models, changes auth/security/privacy behavior, or requires more than one implementation pass.

Small bug fixes and isolated documentation edits can use a lightweight conversation plan.

## Harness Improvement Rule

If a task fails because the repository is hard for the agent to understand or verify, do not only fix the immediate issue. Add the missing route, doc, validation command, fixture, script, or architecture note so the next run has less ambiguity.
