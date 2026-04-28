# UI And UX Rules

Use this file for interface work.

## Source Of Truth

- Product behavior: `docs/product/product-brief.md`.
- User journeys: `docs/product/user-journeys.md`.
- Design system: `docs/design/DESIGN_SYSTEM.md`.
- Competency evidence UX: `docs/design/COMPETENCY_EVIDENCE_UX.md` when the workflow touches competency capture, shaping, or grounding.
- Existing UI patterns in the codebase take precedence over generic advice.

## Rules

- Build the actual workflow, not a marketing surface, unless the task asks for marketing.
- Preserve the calm-precision design language and avoid noisy dashboard behavior.
- Keep the next useful action obvious without oversized controls, duplicate actions, or decorative clutter.
- Treat Focus as the product anchor; do not make Board feel like the strategic center.
- Make loading, empty, error, disabled, and success states explicit.
- Ensure text fits at supported viewport sizes.
- Validate interactive work in a browser when the project can run locally.

## Acceptance Checklist

- The changed workflow is reachable without hidden steps.
- Controls have clear states and affordances.
- Keyboard and screen-reader behavior are not degraded.
- Responsive layouts avoid overlap and horizontal scrolling.
- Browser validation is recorded in the final handoff.
