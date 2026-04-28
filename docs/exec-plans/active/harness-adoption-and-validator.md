# Execution Plan: Harness Adoption And Validator

Status: Active

Owner: Agent

Created: 2026-04-28

Last Updated: 2026-04-28

## Goal

Adopt the template harness structure into Application Tracker so future agent work routes through tracked docs, execution plans, and a local validator instead of missing local-only `.codex` state.

## Non-Goals

- CI wiring
- product behavior changes
- application refactors outside harness support

## Context

- `AGENTS.md`
- `docs/agent/codex-routing.md`
- `docs/CODEX_CONFIGURATION.md`
- `docs/roadmap/task-map.md`
- `scripts/validate-harness.sh`

## Acceptance Criteria

- New harness routes exist and are non-empty.
- `AGENTS.md` points to tracked repo-native routes.
- `docs/CODEX_CONFIGURATION.md` no longer depends on the missing `.codex/application_tracker.toml`.
- `bash scripts/validate-harness.sh` passes.

## Plan

1. Create the harness directory layout and route docs.
2. Replace missing `.codex` references with tracked repo-native routing.
3. Add task maps, active execution plans, and quality docs.
4. Run validator and repo tests relevant to helper-script changes.

## Progress Log

- 2026-04-28: Created plan during harness migration implementation.

## Decisions

- Use `docs/agent/codex-routing.md` as the tracked replacement for the missing `.codex/application_tracker.toml`.
- Keep existing long-form planning docs as source material and normalize active work into `docs/exec-plans/active/`.

## Validation

Commands to run before completion:

```sh
bash scripts/validate-harness.sh
make test
```

## Risks

- Existing tracked and untracked doc surfaces may drift unless the validator stays maintained.
