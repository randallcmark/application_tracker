# Technical Debt

Track known gaps here so agents can improve the system incrementally.

## Active Debt

| ID | Area | Problem | Impact | Suggested Fix | Status |
| --- | --- | --- | --- | --- | --- |
| TD-001 | Harness enforcement | Harness validation is local-only and not wired into CI. | Docs can drift without automated repository enforcement. | Add a CI job that runs `bash scripts/validate-harness.sh`. | Open |
| TD-002 | Architecture boundaries | Boundary rules are documented but not mechanically enforced. | Cross-layer drift can accumulate invisibly. | Add import/boundary checks or targeted architecture tests. | Open |
| TD-003 | Shared shell | The contextual header chip is hidden too aggressively in some desktop cases. | Shell framing loses useful context and can drift from product intent. | Revisit shell overflow logic with browser validation. | Open |
| TD-004 | Mobile portrait usability | Some portrait layouts remain hard to use where text, forms, and action controls compete vertically. | Core workflows can degrade on narrow screens. | Continue responsive hardening from the workspace and shell plans. | Open |
| TD-005 | Timezone rendering | Board follow-up timestamps still use server-rendered UTC/date handling. | Users can misread due/aging state across timezones. | Align board timestamps with browser-local rendering used in job detail journal. | Open |
| TD-006 | Product/doc drift | Product planning previously lived across overlapping roadmap and product docs. | Future agent work can restart from the wrong document surface if historical docs are treated as current. | Three planning hubs now route current vision, execution order, and task detail; keep historical docs bannered and active plans clean. | Monitoring |
| TD-007 | Codex overlay drift | `.codex/*` remains optional and ignored, so local overlays can diverge from the tracked repo-native harness. | Future contributors may rely on untracked local routing or prompts. | Keep `docs/agent/codex-routing.md` authoritative and document overlay limits. | Open |
| TD-008 | UI/UX refinement drift | Broad UI polish issues can get rediscovered piecemeal while feature work lands elsewhere. | Rework accumulates and finished cleanup passes can regress quietly. | Treat cross-surface UI/UX polish as one canonical debt track, archive finished cleanup plans, and re-run browser/manual validation when layout changes land. | Open |

## Cleanup Rules

- Prefer small targeted cleanup changes.
- Link debt items to execution plans when work is complex.
- Remove or close debt entries when the fix lands.
- Promote recurring debt into validation checks.
