# Codex Configuration

This repository keeps Codex guidance lightweight and layered so routine work
does not consume unnecessary context.

## Files

- `AGENTS.md`: short always-loaded product, safety, and engineering guardrails.
- `.codex/application_tracker.toml`: canonical model routing, risk levels,
  verification commands, quality gates, and sub-agent policy.
- `.codex/skills/application-tracker/SKILL.md`: portable repo skill for Codex
  environments that support skills.
- `.codex/prompts/`: reusable prompts for common implementation and review
  slices.
- `docs/CODEX_PLAYBOOK.md`: concise human-readable operating loop.

`AGENTS.md`, `.codex/`, and `docs/CODEX_PLAYBOOK.md` are intentionally local
agent configuration and may remain ignored. Track this file if you want the repo
to document how local agent configuration is expected to work.

## Model Strategy

Default to the lowest safe tier:

| Work type | Profile |
| --- | --- |
| Docs, small CSS, local tests | `models.low_risk` |
| Bounded feature work | `models.standard_implementation` |
| Mechanical refactor after design is settled | `models.long_running_refactor` |
| Schema, auth, owner scope, workflow, AI, worker, deployment | `models.high_risk` |

Use stronger reasoning for decisions that are expensive to unwind. Use smaller
models for already-scoped edits, regression tests, CSS cleanup, documentation,
and command/test orchestration.

## Rate-Limit Discipline

- Start each task by identifying the smallest viable slice.
- Read targeted files with `rg`/line ranges instead of loading broad docs.
- Keep product context in `AGENTS.md` and detailed routing in TOML; do not paste
  both into every prompt.
- Prefer targeted tests before full-suite runs.
- Save high-reasoning work for schema, security, workflow, AI, and deployment
  decisions.

## Prompt Templates

Use `.codex/prompts/implementation-slice.md` for a bounded build task.
Use `.codex/prompts/review-and-plan.md` when the next step is assessment or
planning rather than immediate implementation.

## Sub-Agents

Use sub-agents only when they can work independently without blocking the main
thread. Good examples: inventory affected routes, inspect tests, or make a
disjoint CSS/documentation edit. Avoid delegating the immediate blocker.

## Maintenance

When product direction changes, update `AGENTS.md` only if the always-on
guardrails change. Update `.codex/application_tracker.toml` for routing,
verification, or model changes. Update the playbook only when the operating
loop changes.
