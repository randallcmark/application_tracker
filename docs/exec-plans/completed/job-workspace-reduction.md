# Execution Plan: Job Workspace Reduction

Status: Completed

Owner: Agent

Created: 2026-04-28

Last Updated: 2026-05-02

## Goal

Reduce Job Workspace density so users can execute application work from one calm surface with clearer pane structure, less duplication, and better mobile behavior.

## Non-Goals

- redesigning the whole product shell
- changing workflow semantics unrelated to workspace usability
- introducing hidden AI automation

## Context

- `docs/JOB_WORKSPACE_REDUCTION_PLAN.md`
- `docs/JOB_DETAIL.md`
- `docs/PRODUCT_VISION.md`
- `docs/roadmap/implementation-sequencing.md`
- `docs/roadmap/task-map.md`
- `docs/design/DESIGN_SYSTEM.md`
- `docs/product/user-journeys.md`
- `docs/exec-plans/completed/ui-density-layout-ai-cleanup.md`

## Acceptance Criteria

- Remaining pane cleanup work is sliced and resumable.
- Validation includes route tests plus desktop/mobile browser checks.
- Duplicate summary blocks and utility clutter are reduced intentionally, not cosmetically.

## Plan

1. Continue from the current reduction-plan phases instead of inventing new UI structure.
2. Tackle pane cleanup in small sections with regression coverage.
3. Validate responsive behavior after each layout-affecting slice.
4. Keep the design system as the visual source of truth.
5. Incorporate UI QA backlog items UI-014 through UI-020 as targeted polish:
   compact Back to Board/left navigation, improve AI panel density and usefulness, make AI help
   affordances honest or actionable, redesign section workbenches through separate slices, fix
   Active Documents filename wrapping/menu stacking, and compress Document Actions.

## Progress Log

- 2026-04-28: Created active workstream from the existing reduction plan.
- 2026-05-01: Completed the first cleanup pass for the remaining Tasks, Notes, and Documents panes.
  Tasks now render as one primary workspace surface, Notes has a clearer activity/note/journal
  structure, and Documents separates active documents from document actions before local AI work.
- 2026-05-01: Ran in-browser validation against Overview, Tasks, Notes, and Documents at the
  available narrow viewport. Fixed a mobile shell overflow where the user menu could cover topbar
  actions; confirmed one active workspace surface per selected section and reachable Notes/Documents
  controls.
- 2026-05-01: Added desktop bounded-pane shell behavior. At desktop widths the app window is fixed
  to the viewport, shared main/aside regions scroll internally, and wide Job Workspace layouts give
  the left rail, center pane, and AI rail their own scroll containers instead of scrolling the whole
  page. Route marker validation covered Focus, Inbox, Board, Job Workspace, Artefacts, Competencies,
  Settings, and Help.
- 2026-05-02: Folded the latest UI QA backlog into workspace reduction. UI-014 through UI-020 now
  define the next targeted Job Workspace polish areas after global copy-density cleanup.
- 2026-05-02: Completed the first workspace QA polish slice for UI-014, UI-018, UI-019, and
  UI-020. Back to Board is now a compact link, the left rail starts higher, Active Documents rows
  give filenames more usable width, the document AI menu stacks above adjacent rails more reliably,
  and Document Actions is shorter with direct desktop actions.
- 2026-05-02: Completed the remaining workspace QA cleanup for UI-015 and UI-016. The AI rail now
  prioritizes useful fit content, boilerplate fit-summary preambles are stripped, provider metadata
  is removed from the primary reading area, and the help panel exposes real actions instead of
  pseudo-clickable guidance.
- 2026-05-02: Split UI-017 into the dedicated active plan
  `docs/exec-plans/completed/job-detail-section-workbenches.md` so larger section redesign work does
  not get folded into incremental pane polish.

## Decisions

- Use the current reduction plan as the canonical backlog for workspace cleanup.
- Keep the external QA backlog as origin input only; this plan and the UI density plan are the
  repository-owned sources for workspace polish.

## Validation

Commands to run before completion:

```sh
make test
```

## Risks

- Workspace cleanup can easily regress mobile behavior or reintroduce duplicated actions without browser validation.
