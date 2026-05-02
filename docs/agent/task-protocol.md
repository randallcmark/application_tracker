# Task Protocol

Use this protocol to keep agent work reviewable and recoverable.

## Intake

Before editing, identify:

- the requested outcome;
- the files or subsystems likely involved;
- the source of product truth;
- the validation commands required before completion;
- whether an execution plan is required.

If product behavior is underspecified, read the product docs first. Ask only when the missing behavior cannot be recovered from repository context.

## Planning

Use an execution plan for complex work. The plan is a working artifact, not ceremony. It must capture:

- goal and non-goals;
- relevant context links;
- step-by-step approach;
- acceptance criteria;
- validation commands;
- decisions and tradeoffs discovered during work;
- progress log.

Keep active plans in `docs/exec-plans/active/`. Move completed plans to `docs/exec-plans/completed/` after the work lands.

## Implementation

- Prefer existing patterns over new abstractions.
- Keep changes scoped to the task.
- Add tests near the changed behavior when the project has a test harness.
- Avoid broad formatting churn unless formatting is the task.
- Do not introduce dependencies without checking architecture and validation docs.
- Update product, architecture, or validation docs in the same change when behavior changes.
- When the data model or schema changes, include the migration patch in the work and apply it to
  the active local database before handoff.

## Review

Before proposing completion, inspect the diff as a reviewer:

- Does the implementation match the requested behavior?
- Did it invent behavior not captured in product docs or acceptance criteria?
- Are boundaries and dependency directions respected?
- Are failure modes handled?
- Are validation commands documented and run?
- Did the task reveal a missing harness rule or check?

## Completion

Report:

- what changed;
- which validation commands ran and their result;
- any commands not run and why;
- remaining risks or follow-up work.
