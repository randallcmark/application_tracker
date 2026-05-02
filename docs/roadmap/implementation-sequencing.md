# Implementation Sequencing

This is the canonical current strategy and order of execution. It answers what to work on next and
why. Use `docs/roadmap/task-map.md` for execution-ready workstream detail.

## Current Sequence

Planning harness cleanup is complete enough to leave active execution. Keep the validator passing
and historical plans archived, but resume product work from the current active workstreams below.

1. UI density, layout, and AI surface cleanup.
   Incorporate the latest QA backlog as an active polish workstream before more feature expansion.
   Start with global page-heading copy reduction, then move through Focus, Inbox, Board, and Job
   Workspace density fixes while preserving Focus as the product anchor and Job Workspace as the
   execution surface.

2. Inbox follow-ons.
   Stabilize richer intake before background runtime work. The next useful slices are
   multi-candidate email review, clearer review/enrichment handling, and scoped provider-backed
   ingestion decisions that preserve manual/captured/system-recommended distinctions.

3. Job Workspace reduction.
   Continue reducing density in the core execution surface. Finish pane cleanup and responsive
   validation before adding more complex workflow or AI controls to the page. The current QA-driven
   cleanup pass is complete enough that the next workspace work should move through the dedicated
   section-workbench plan instead of more opportunistic pane edits.

4. Job Detail section workbenches.
   Redesign Application, Interviews, Follow-Ups, Tasks, and Notes as compact workbenches one
   section at a time. Start with a clear section contract before larger layout changes.

5. Artefact AI and competency evidence continuation.
   Resume the active G4 grounding milestone after workspace and intake surfaces are better framed.
   Keep selected evidence opt-in, visible, attributable, and non-mutating.

6. AI provider expansion.
   Extend provider execution only after visible-output contracts and current AI surfaces are stable.
   Treat provider polish as driven by real use, error-message gaps, or document-handling needs
   rather than speculative provider additions.

7. Document Handling Foundation.
   Establish source-preserving, Markdown-first content handling before adding more document-heavy AI
   workflows or background automation. This clarifies how source material, AI outputs, artefact
   Markdown views, employer rubric mapping, later extraction, search, and export should work. The
   current no-schema phase now has a formal artefact Markdown access contract, so the next slice
   should build on that boundary rather than extending ad hoc previews.

8. Scheduler and worker.
   Add the smallest self-hosted background runtime once Inbox inputs and visible output surfaces are
   clear and document handling has a stable source/Markdown/provenance model. Protect Docker/QNAP
   deployment simplicity and keep scheduler output visible in Focus, Inbox, or Admin.

9. Admin, restore, and self-hosted operations.
   Expand operational trust with restore validation, object-management slices, scheduler run
   visibility, maintenance docs, and deployment smoke paths.

10. Deferred auth/provider modes.
   Resume OIDC, proxy auth, or broader provider modes only after the higher-priority workflow and
   operations work is stable.

## Sequencing Rules

- Prefer work that clarifies current user workflows before work that automates or schedules them.
- Do not add hidden automation before the review surface, provenance, and failure mode are explicit.
- Keep AI optional and visible; provider expansion should not drive product sequencing by itself.
- Put document-heavy automation behind source preservation, safe Markdown rendering, and visible
  provenance.
- Protect local-first and self-hosted deployment simplicity when adding background runtime.
- Move completed execution plans out of `docs/exec-plans/active/` promptly so active work remains
  easy to scan.

## How To Resume Work

1. Read `docs/PRODUCT_VISION.md`.
2. Read this file to confirm priority order.
3. Read `docs/roadmap/task-map.md` for the current workstream breakdown.
4. Open only the active execution plan and supporting feature docs for the selected workstream.
