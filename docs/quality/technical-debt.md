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
| TD-006 | Product/doc drift | Some longer-term route/model intentions still live mainly in deep planning docs instead of narrow execution plans. | Future agent work can restart from the wrong document surface. | Keep active work routed through `docs/exec-plans/active/` and retire stale plan state. | Open |
| TD-007 | Codex overlay drift | `.codex/*` remains optional and ignored, so local overlays can diverge from the tracked repo-native harness. | Future contributors may rely on untracked local routing or prompts. | Keep `docs/agent/codex-routing.md` authoritative and document overlay limits. | Open |

## Cleanup Rules

- Prefer small targeted cleanup changes.
- Link debt items to execution plans when work is complex.
- Remove or close debt entries when the fix lands.
- Promote recurring debt into validation checks.
