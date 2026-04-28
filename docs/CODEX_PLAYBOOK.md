# Codex Playbook

This is the short operating loop for agents working on Application Tracker.
`AGENTS.md` is the guardrail contract. `docs/agent/codex-routing.md` is the
tracked source of truth for routing, risk levels, verification, and sub-agent
use. Local `.codex/*` files are optional overlays when present.

## Default Loop

1. Read the smallest relevant context: product docs for direction, route/model
   files for implementation, tests for expected behavior.
2. Classify risk using `docs/agent/codex-routing.md`.
3. For medium/high-risk work, state a short plan before editing.
4. Implement the smallest useful slice.
5. Run targeted checks, then broader checks if the blast radius warrants it.
6. Update docs when behavior, setup, public routes, or roadmap expectations
   change.

## Model And Token Strategy

Use the cheapest model/reasoning tier that can safely handle the task:

- `models.low_risk`: docs, small CSS fixes, localized tests, simple copy.
- `models.standard_implementation`: bounded FastAPI/UI/service changes.
- `models.long_running_refactor`: mechanical refactors after design is settled.
- `models.high_risk`: schema, auth, owner scope, workflow semantics, AI
  execution, scheduler/worker, deployment architecture, or cross-layer bugs.

Reduce token use by reading targeted files with `rg`, avoiding repeated product
doc summaries, and keeping plans to the decisions needed for the current slice.

## Quality Gates

Do not finish meaningful implementation work without the smallest relevant
verification available. Typical checks are listed in
`docs/agent/codex-routing.md`.

For schema changes, include an Alembic migration and test/verify the migration.
For owner-scoped behavior, include tests or a clear manual validation path for
cross-user boundaries.

## Split Work When

- the task crosses multiple product surfaces;
- schema and UI changes can be validated separately;
- the current slice cannot be tested cleanly;
- a refactor is useful but not required for the requested behavior.

## Sub-Agent Use

Use sub-agents sparingly and only for bounded, non-blocking work such as route
inventory, test gap discovery, or disjoint file edits. Keep ownership explicit
and integrate results before final verification.
