# Quality Score

Use this document as a recurring snapshot of project health. Keep it factual and useful for prioritization.

## Scorecard

| Area | Grade | Evidence | Next Action |
| --- | --- | --- | --- |
| Product clarity | B | Product direction is strong across `docs/PRODUCT_VISION.md`, `docs/DELIVERY_PLAN.md`, and the public roadmap, but the planning surface was fragmented before the harness migration. | Route active work through execution plans and keep product-brief contracts current. |
| Architecture legibility | B- | Runtime shape is understandable from code and docs, but boundary rules were implicit until the harness pass and remain unenforced mechanically. | Add targeted boundary checks and keep ADRs current. |
| Validation reliability | B- | `make lint`, `make test`, `make check`, migrations, and Docker smoke exist, but harness validation is new and CI enforcement is missing. | Add CI coverage for harness validation and fill any missing smoke paths. |
| UI quality | B | The design system is strong and the shared shell is in place, but mobile portrait and shell overflow issues remain open. | Continue workspace/shell responsive cleanup with browser validation. |
| Security posture | B | Local auth, sessions, CSRF, owner scoping, API tokens, and production guardrails are documented and tested. OIDC/proxy modes remain future work. | Keep auth expansion scoped and validate every boundary change. |
| Observability | C+ | Health/admin surfaces exist, but deeper runtime observability for scheduler/worker and provider behavior is still limited. | Improve logs, smoke checks, and operational docs as background/runtime work lands. |

## Review Cadence

Review monthly during active development and before major release or deployment-architecture changes.

## Notes

Record evidence, not vibes. Link to failures, flaky tests, incidents, review comments, and completed cleanup work when updating this scorecard.
