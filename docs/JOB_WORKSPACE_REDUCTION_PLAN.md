# Job Workspace Reduction Plan

## Purpose

This document defines the resumable redesign plan for reducing Job Workspace
page height, controlling AI density, and improving interaction focus without
changing workflow semantics or owner-scoped behavior.

Use this document as the authoritative plan for Job Workspace reduction work.
It is intended to survive context compaction and multi-session implementation.

## Problem Statement

The current Job Workspace is functional but still too large and visually dense.
The main issues are structural:

- too many sections are open at once in the main column;
- quick actions occupy permanent page space even though they are utilities;
- AI assessment and long-form job description content can dominate the page;
- role summary content is duplicated across multiple sections;
- lower-page utility panels are useful but are not visible early enough or are
  consuming expanded space when a compact summary would be more effective.

The goal is to make Job Workspace feel like a focused execution surface rather
than a long stitched-together document.

## Design Principles

This work must preserve the existing product guardrails:

- the page remains a working surface for one opportunity;
- the board is not reintroduced as the strategic center;
- AI remains visible, optional, and non-mutating;
- owner scoping, upload safety, and route compatibility are preserved;
- the design should reduce noise by changing interaction structure first,
  rather than by relying on spacing-only tweaks.

## Target Interaction Model

### 1. Left rail as the primary navigator

The left rail section list remains in place and keeps its counts/completion
signals:

- Overview
- Application
- Interviews
- Follow-ups
- Tasks
- Notes
- Documents

The center column becomes single-surface:

- only one primary section is expanded at a time;
- the active section is selected from the left rail;
- the selected section can later be mirrored by top tabs if needed, but the
  left rail is the canonical control in the first pass.

### 2. Quick Actions become utility UI

Quick Actions should not permanently add page height.

They move from an always-open left-rail card to an overlay utility panel that:

- is launched from a left-rail or header trigger;
- contains workflow and utility shortcuts;
- can be opened when needed without remaining on screen constantly.

### 3. Long-form reference content is constrained

These surfaces should preserve content without consuming uncontrolled height:

- AI overall assessment;
- job description / role description;
- other long-form reference blocks as needed.

Default behavior:

- fixed-height panels;
- internal scroll;
- optional expand affordance later if needed.

### 4. Duplicate summary content is removed

The current overlap between `Role & Notes` and role summary content inside
`Overview` should be removed.

Default rule:

- `Overview` owns the role summary;
- `Notes` owns note-taking and activity context;
- there should not be two expanded summary sections showing the same narrative.

### 5. Utility information moves toward micro vs expanded cards

Utility blocks such as:

- Application state and route
- Activity / provenance
- Artefacts
- Workspace tools

should support two display modes:

- `micro`: compact indicators, counts, signals, next-needed hints;
- `expanded`: detailed forms and actions.

The first implementation does not include freeform user-custom layout. It
introduces the size model and a fixed default arrangement first.

## Implementation Phases

### Phase 1: Height Reduction and Focus

Goal: sharply reduce perceived page size and visual noise without changing
underlying workflows.

#### Phase 1A: Single-surface main pane

Implement left-rail-driven section switching so only one primary section is
expanded in the center column at a time.

Requirements:

- active section is controlled by request state, not client-only hidden logic;
- left rail counts and completion indicators stay visible;
- existing routes and forms continue to work inside the selected section;
- default section is `overview`;
- AI flash/status redirects should preserve the active section where possible.

Suggested technical shape:

- `GET /jobs/{job_uuid}?section=overview`
- `render_job_detail(..., active_section="overview")`
- section nav emits route links instead of local page anchors
- inactive sections are not rendered as expanded blocks in the center column

Acceptance criteria:

- the center column shows one primary section at a time;
- switching section does not break existing form flows;
- left rail remains the persistent page map;
- the page height is materially reduced on ordinary jobs.

#### Phase 1B: Quick Actions overlay

Replace the always-open Quick Actions card with an overlay panel.

Requirements:

- launched by a clear button in the left rail or top actions;
- contains the existing utility actions;
- actions continue to link or target the same destinations;
- overlay closes cleanly and does not destabilize layout;
- responsive fallback remains usable on smaller screens.

Acceptance criteria:

- quick actions are accessible within one click;
- they do not contribute permanent page height;
- overlay behavior remains stable on desktop and mobile widths.

#### Phase 1C: Long-form content constraints and deduplication

Constrain the AI assessment and job description surfaces, and remove duplicate
role summary content.

Requirements:

- AI assessment body has a fixed default height with internal scroll;
- role description display has a fixed default height with internal scroll;
- duplicate `Role & Notes` section is removed or absorbed into `Overview`;
- markdown rendering remains intact;
- editing remains available without forcing permanent full-height display.

Acceptance criteria:

- long AI output does not stretch the right rail indefinitely;
- long job descriptions do not dominate the page by default;
- duplicate role summary is gone;
- the page remains readable and editable.

### Phase 2 Follow-On Note: Utility Card Model Reassessment

This is no longer the next active implementation phase.

The page restructure changed enough that the original micro/expanded card plan
should not be treated as implementation-ready. Revisit it only after the
individual section panes settle.

Before returning here, complete pane-specific cleanup for:

- `Application`
- `Interviews`
- `Follow-ups`
- `Tasks`
- `Notes`
- `Documents`

Current checkpoint:

- first pane-cleanup pass implemented for `Application`, `Interviews`, `Follow-ups`, `Tasks`,
  `Notes`, and `Documents`;
- these panes now use calmer titles, clearer workflow grouping, explicit workbench markers, and a
  single primary rendered surface per selected section;
- browser validation has been run at the available narrow viewport; the first polish fix tightened
  topbar user-menu wrapping so Job Workspace actions remain visible on mobile-width screens;
- desktop bounded-pane behavior is now implemented in the shared shell and wide Job Workspace:
  the app window anchors to the viewport, shared main/aside regions scroll internally, and the
  workspace left rail, center pane, and AI rail become independent scroll containers when the
  three-column layout is active;
- remaining follow-on work is broader desktop/manual validation if a larger browser viewport is
  available, then only targeted usability polish found from that pass.

Any later utility-card work should start from the stabilised shared workspace
frame rather than from the older pre-reduction page structure.

### Phase 3: Optional Enhancements

Future enhancements after the fixed interaction model proves itself:

- optional mirrored top tabs;
- richer expand/collapse transitions;
- persisted card ordering or pinned utilities;
- snap-to-grid customization if the fixed model proves too rigid.

## Test Strategy

This redesign must be locked by UI contract tests so future changes do not
reintroduce bloat or inconsistency.

### Route/UI contract coverage

Add or update tests for:

- left-rail section navigator rendering;
- active-section state reflected in rendered markup;
- only one primary section rendered as expanded main content at a time;
- quick actions overlay markers and trigger presence;
- AI assessment constrained container markers;
- constrained job description container markers;
- duplicate role summary removed.

### Cross-page shell regression coverage

Keep existing shared-shell tests green so Job Workspace changes do not break:

- topbar/nav layout;
- shell hero contract;
- right-rail consistency.

### Focused browser-polish contract coverage

For Job Workspace specifically, preserve coverage for:

- artefact AI menu behavior;
- local AI workspace structure;
- responsive collapse markers and ordering.

## Execution Order

1. Write and maintain this plan. Implemented.
2. Phase 1A: single-surface main pane.
3. Phase 1B: quick actions overlay.
4. Phase 1C: constrained long-form content and duplicate removal.
5. Regression coverage updates for all Phase 1 changes.
6. Pane-by-pane cleanup checkpoint after the new interaction model is proven in
   the browser.
7. Reassess any later utility-card model only after the pane cleanup pass.

## Resume Notes

When resuming this work:

1. Read this document first.
2. Read `docs/PRODUCT_VISION.md`, `docs/roadmap/implementation-sequencing.md`, and
   `docs/roadmap/task-map.md`.
3. Inspect `app/api/routes/job_detail.py` and
   `tests/test_job_workspace_ui_contract.py`.
4. Continue from the earliest incomplete phase/sub-slice.

Current status at creation:

- plan recorded;
- next implementation target is Phase 1A: single-surface main pane.
