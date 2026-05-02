# Execution Plan: UI Density, Layout, And AI Surface Cleanup

Status: Active

Owner: Agent

Created: 2026-05-02

Last Updated: 2026-05-02

## Goal

Use the latest UI QA backlog as triage input to make the main authenticated surfaces cleaner,
denser, and more action-oriented while preserving existing product flows.

## Non-Goals

- changing product workflow semantics
- changing persistence, auth, owner scoping, or route contracts
- implementing all QA items in one change
- adding new explanatory copy to replace removed copy

## Context

- Origin input: `/Users/markrandall/Documents/application_tracker_ui_qa_backlog.md`
- `docs/PRODUCT_VISION.md`
- `docs/roadmap/implementation-sequencing.md`
- `docs/roadmap/task-map.md`
- `docs/agent/ui-ux-rules.md`
- `docs/design/DESIGN_SYSTEM.md`
- `docs/exec-plans/active/job-workspace-reduction.md`

Repository docs are the durable source of truth; the external QA backlog remains triage input.

## Acceptance Criteria

- Redundant page eyebrow and obvious subtitle copy are removed from main authenticated surfaces.
- Focus, Inbox, Board, and Job Workspace density work is sliced and reviewable.
- AI surfaces stay visible, optional, attributable, and non-mutating.
- Artefact Markdown preview quality work stays behind the existing Markdown access contract.
- Layout changes include route tests where markup contracts matter and browser validation when feasible.

## Plan

1. Global copy-density cleanup for Focus, Inbox, Board, Add Job, Paste Email, Settings, Artefacts,
   and Competency Evidence is complete.
2. Focus density and actionability is complete for counters, repeated labels, Recent Prospects,
   right rail ordering, and the compact hybrid priority model.
3. Inbox card and right-rail cleanup is complete.
4. Board cleanup is complete: counts live in lane headers and redundant lane subtext is removed.
5. Job Workspace polish is complete for the current QA-defined cleanup scope. UI-014 through
   UI-020 are either implemented directly or, for UI-017, moved into a dedicated section-workbench
   execution plan.
6. Larger follow-on work now continues through dedicated plans rather than this cleanup stream:
   Job Detail section workbenches, document-handling follow-ons, and future evidence/workspace
   refinement.

## Progress Log

- 2026-05-02: Created active workstream from the structured UI QA backlog. Task A is the next
  implementation slice.
- 2026-05-02: Completed Task A compact authenticated page headers.
- 2026-05-02: Completed the Focus density/actionability pass. Summary counters are now actionable,
  all five fit on one desktop row, repeated "Focus queue" labels are removed, Recent Prospects spans
  the full desktop grid with row-style items, and the right rail now prioritizes Where to Resume
  before AI.
- 2026-05-02: Completed Inbox card and right-rail cleanup. Cards now use a compact desktop
  main/actions layout, metadata uses horizontal space more efficiently, and the right rail keeps a
  queued count plus concise review guidance without duplicate header actions.
- 2026-05-02: Completed Board density cleanup. The duplicate workflow summary band is removed,
  lane counts now live in the column headers, and redundant lane-description subtext is gone.
- 2026-05-02: Completed the first Job Workspace polish slice. Left-rail/back-link density is
  reduced, Active Documents rows use width more effectively, document AI menus have stronger
  stacking, and Document Actions is shorter and more direct.
- 2026-05-02: Completed the remaining Job Workspace AI cleanup. The AI rail now shows useful fit
  content first, strips boilerplate fit-summary preambles, hides provider metadata from the primary
  reading area, and the help panel now exposes real actions instead of misleading pseudo-links.
- 2026-05-02: Completed the Competency Evidence workspace redesign. Evidence creation now uses a
  full-width workspace with employer rubric mapping beside it, while the saved library sits below
  as a separate reusable surface.
- 2026-05-02: Completed the first artefact Markdown preview quality pass. Derived previews now keep
  paragraphs, simple headings, and list structure instead of collapsing into one flat text blob.
- 2026-05-02: Split UI-017 into the dedicated active plan
  `docs/exec-plans/active/job-detail-section-workbenches.md` so larger section redesign work stays
  deliberate and reviewable.

## Decisions

- Start with global copy-density cleanup because it is low-risk and reduces layout pressure across
  several affected pages.
- Do not treat the external QA backlog as canonical after this plan is created.
- Focus keeps a compact hybrid priority model: actionable top counters, central queue cards, and a
  smaller right-rail resume card. Larger structural changes should wait for real-use feedback.

## Validation

Commands to run before completing slices:

```sh
bash scripts/validate-harness.sh
git diff --check
```

Run focused route tests for touched surfaces. Run browser validation for layout-affecting slices
when the local app can be exercised.

## Risks

- Copy cleanup can remove useful orientation if applied mechanically. Preserve helper text where it
  explains a non-obvious workflow or risk.
- Job Workspace changes can regress bounded-pane behavior without desktop and mobile validation.
