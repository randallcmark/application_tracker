# Documentation Maintenance

Documentation is part of the harness. It must stay small, routed, and current.

## Maintenance Rules

- `AGENTS.md` remains a table of contents, not an encyclopedia.
- Long-lived facts live under `docs/`.
- Product behavior lives under `docs/product/`.
- Architecture constraints live under `docs/architecture/`.
- Repeated task rules live under `docs/agent/`.
- Temporary implementation state lives in execution plans.
- Completed decisions live in architecture decision records.

## When To Update Docs

Update docs in the same change when:

- product behavior changes;
- validation commands change;
- a new subsystem, dependency, or boundary is introduced;
- a repeated review comment should become a rule;
- an agent got stuck because context was missing;
- a known quality gap is fixed or discovered.

## Staleness Checks

During maintenance, check:

- broken links;
- empty placeholder files;
- the root `README.md` still matches the current product vision, roadmap, and shipped capability
  set;
- stale references to missing local-only Codex routing files;
- validation commands that no longer exist;
- product docs that conflict with tests or implementation;
- architecture docs that conflict with imports or package boundaries.

Run:

```sh
bash scripts/validate-harness.sh
```

## Promotion Rule

If a doc rule is repeatedly violated, promote it into a mechanical check where possible. Prefer a script, lint rule, test, or CI check over asking every future agent to remember it.
