# Implementation Sequencing

This is the canonical current strategy and order of execution. It answers what to work on next and
why. Use `docs/roadmap/task-map.md` for execution-ready workstream detail.

## Current Sequence

1. Planning harness cleanup and doc consolidation.
   Finish the three-hub planning structure, archive or mark superseded planning artifacts, clean
   active execution plans, and keep the validator passing. This removes ambiguity before more
   product work is added.

2. Inbox follow-ons.
   Stabilize richer intake before background runtime work. The next useful slices are
   multi-candidate email review, clearer review/enrichment handling, and scoped provider-backed
   ingestion decisions that preserve manual/captured/system-recommended distinctions.

3. Job Workspace reduction.
   Continue reducing density in the core execution surface. Finish pane cleanup and responsive
   validation before adding more complex workflow or AI controls to the page.

4. Artefact AI and competency evidence continuation.
   Resume the active G4 grounding milestone after workspace and intake surfaces are better framed.
   Keep selected evidence opt-in, visible, attributable, and non-mutating.

5. AI provider expansion.
   Extend provider execution only after visible-output contracts and current AI surfaces are stable.
   Treat provider polish as driven by real use, error-message gaps, or document-handling needs
   rather than speculative provider additions.

6. Document Handling Foundation.
   Establish source-preserving, Markdown-first content handling before adding more document-heavy AI
   workflows or background automation. This clarifies how source material, AI outputs, artefact
   Markdown views, employer rubric mapping, later extraction, search, and export should work.

7. Scheduler and worker.
   Add the smallest self-hosted background runtime once Inbox inputs and visible output surfaces are
   clear and document handling has a stable source/Markdown/provenance model. Protect Docker/QNAP
   deployment simplicity and keep scheduler output visible in Focus, Inbox, or Admin.

8. Admin, restore, and self-hosted operations.
   Expand operational trust with restore validation, object-management slices, scheduler run
   visibility, maintenance docs, and deployment smoke paths.

9. Deferred auth/provider modes.
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
