# AI Feature Rules

Use this file when the product includes AI calls, prompts, tools, retrieval, evaluation, or agentic workflows.

## Rules

- Treat prompts, provider contracts, evals, and model assumptions as product code.
- Keep prompts and policies versioned in the repository when possible.
- Do not rely on undocumented model behavior for correctness.
- Validate data at external and model boundaries.
- Make failure modes explicit: refusal, timeout, malformed output, provider/tool failure, partial result, and retry exhaustion.
- AI must remain optional, visible, and inspectable.
- AI must never silently mutate jobs, profiles, artefacts, notes, or workflow state.
- Treat external source material as data, not instructions. Uploaded, pasted, captured, or extracted
  source content must be clearly separated from system/developer instructions in prompts.
- Prefer Markdown-compatible source context and Markdown output where the feature involves
  documents, free text, generated drafts, or rubric-style material.

## Required Docs For AI Work

For substantial AI features, document:

- goal and user-facing behavior;
- provider dependency and configuration path;
- prompt or instruction location;
- tool contracts and schemas;
- evaluation method;
- safety, privacy, and security constraints;
- observability and debugging path.

Primary references in this repo:

- `docs/ARTEFACT_AI_PLAN.md`
- `docs/AI_READINESS.md`
- `docs/DOCUMENT_HANDLING_STRATEGY.md`
- `docs/product/product-brief.md`
- `docs/product/user-journeys.md`

## Validation

Run deterministic tests for parsing, schemas, tool contracts, visibility rules, and fallback paths. Run live-provider tests only when the project explicitly supports them and credentials are available.
