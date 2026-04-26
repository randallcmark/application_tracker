# Competency Evidence UX

This is the design reference for the competency evidence and STAR workflow.

## Surface Principles

- Treat competency evidence as a quiet working library.
- Avoid long text walls in default views.
- Use compact cards for scanning and focused panels for editing.
- Keep AI actions visibly separate from saved user evidence.
- Do not make job workspaces heavier; add small hooks into the evidence library instead.

## Library Card, Compact

Each card should show:

- title;
- competency/theme;
- strength: seed, working, strong;
- one short result line when present;
- tags;
- source signal if the entry came from a job, artefact, or AI output.

The card should not show all STAR text by default.

## Entry Detail

Use segmented blocks:

- Situation
- Task
- Action
- Result
- Evidence notes

Each block should be bounded and readable. The detail view can be a focused page or an overlay once
the interaction pattern is proven.

## Guided Creation

The creation workflow should be step-based or grouped, not one large questionnaire.

Suggested grouping:

1. Competency and title.
2. STAR evidence.
3. Result and credibility.
4. Tags and source context.

## Existing-Surface Hooks

Job Workspace:

- small action: `Create evidence from this role`

Documents / artefact AI workspace:

- small action: `Create evidence from this artefact`

Draft generation:

- later opt-in selector: `Use competency evidence`

## AI Behaviour

AI may help shape an entry or draft a STAR response, but saved evidence remains user-controlled.
AI output should be visible and inspectable before anything is persisted into the evidence library.
