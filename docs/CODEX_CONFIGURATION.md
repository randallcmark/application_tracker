# Codex Configuration

This repository keeps Codex guidance lightweight and layered so routine work
does not consume unnecessary context.

## Files

- `AGENTS.md`: short always-loaded product, safety, and engineering guardrails.
- `docs/agent/codex-routing.md`: canonical in-repo routing for risk levels,
  verification commands, quality gates, task slicing, and sub-agent policy.
- `.codex/skills/application-tracker/SKILL.md`: portable repo skill for Codex
  environments that support skills when a local `.codex/` overlay exists.
- `.codex/prompts/`: reusable prompts for common implementation and review
  slices when a local `.codex/` overlay exists.
- `docs/CODEX_PLAYBOOK.md`: concise human-readable operating loop.

`AGENTS.md`, `docs/CODEX_PLAYBOOK.md`, and `docs/agent/codex-routing.md` are
the tracked repo-native operating surface. `.codex/` is optional local overlay
space and may remain ignored.

## Model Strategy

Default to the lowest safe tier:

| Work type | Profile |
| --- | --- |
| Docs, small CSS, local tests | `docs/agent/codex-routing.md#low-risk` |
| Bounded feature work | `docs/agent/codex-routing.md#standard-implementation` |
| Mechanical refactor after design is settled | `docs/agent/codex-routing.md#long-running-refactor` |
| Schema, auth, owner scope, workflow, AI, worker, deployment | `docs/agent/codex-routing.md#high-risk` |

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

Use `docs/agent/codex-routing.md` for the tracked build/review loop.
Local `.codex/prompts/*` helpers are optional overlays when present.

## Sub-Agents

Use sub-agents only when they can work independently without blocking the main
thread. Good examples: inventory affected routes, inspect tests, or make a
disjoint CSS/documentation edit. Avoid delegating the immediate blocker.

## Maintenance

When product direction changes, update `AGENTS.md` only if the always-on
guardrails change. Update `docs/agent/codex-routing.md` for routing,
verification, or model changes. Update the playbook only when the operating
loop changes. Update `.codex/*` only if you intentionally maintain a local
overlay in addition to the tracked repo-native harness.
