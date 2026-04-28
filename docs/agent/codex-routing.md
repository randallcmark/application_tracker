# Codex Routing

This file is the tracked in-repo source of truth for task slicing, risk classification, validation gates, model/reasoning selection guidance, and sub-agent policy.

## Default Loop

1. Read the smallest relevant product, architecture, and test context.
2. Classify risk before editing.
3. For medium/high-risk work, state a brief plan or create an execution plan.
4. Implement the smallest useful slice.
5. Run targeted checks, then broader checks if the blast radius warrants it.
6. Update docs when behavior, routes, validation, or durable decisions change.

## Risk Profiles

### Low Risk

Use for docs, small CSS, local test fixes, copy, and isolated mechanical edits.

- Prefer the cheapest adequate model/reasoning profile.
- Validation: run the narrowest relevant command plus `bash scripts/validate-harness.sh` for harness work.

### Standard Implementation

Use for bounded FastAPI, template, route, or service changes with limited blast radius.

- Inspect the changed surface and nearby tests first.
- Validation: targeted tests, then `make test` or `make check` if the change spans multiple layers.

### Long-Running Refactor

Use for mechanical refactors after the design is settled.

- Split into reviewable slices.
- Keep execution plans current.
- Avoid behavior changes unless explicitly planned.

### High Risk

Use for schema, auth, owner scope, workflow semantics, AI execution, scheduler/worker, deployment, storage, or cross-layer bugs.

- Require an execution plan.
- Read product, architecture, validation, and security docs before editing.
- Validation: targeted tests, relevant smoke path, and broader regression coverage before handoff.

## Task Slicing

- Start with the smallest coherent vertical slice.
- Split work when schema and UI can be validated separately.
- Split when a task crosses multiple surfaces, risks broad regressions, or needs different validation modes.
- Prefer helper extraction and service boundaries over rewrites.

## Validation Gates

- Harness/doc changes: `bash scripts/validate-harness.sh`.
- Python/code changes: `make lint`, targeted `pytest`, then `make test` or `make check` as needed.
- Migration changes: `make migrate` plus migration-relevant tests.
- Docker/deployment changes: `make docker-import-smoke` when relevant.
- UI changes: browser-level validation at desktop and mobile widths.

## Sub-Agent Policy

Use sub-agents only when they can work independently without blocking the main thread. Good examples:

- route or test inventory;
- disjoint documentation edits;
- bounded CSS or fixture cleanup.

Do not delegate the immediate blocker. Keep ownership explicit and integrate results before final verification.

## Local Overlay Policy

Local `.codex/*` files may exist as optional overlays for personal prompts, skills, or model preferences. They must not be required for repository comprehension or safe execution.
