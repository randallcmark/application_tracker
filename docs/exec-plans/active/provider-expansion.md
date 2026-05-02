# Execution Plan: AI Provider Expansion

Status: Active

Owner: Agent

Created: 2026-04-28

Last Updated: 2026-05-01

## Goal

Extend provider execution beyond the current OpenAI-compatible and Gemini paths, with Anthropic and related provider-mode follow-on work treated as explicit slices.

## Non-Goals

- changing the visible-output contract
- mandatory AI configuration
- unrelated artefact or workspace redesign

## Context

- `docs/PRODUCT_VISION.md`
- `docs/roadmap/implementation-sequencing.md`
- `docs/roadmap/task-map.md`
- `docs/AI_READINESS.md`
- `docs/agent/ai-feature-rules.md`

## Acceptance Criteria

- Provider additions are documented, validated, and owner-scoped.
- Error handling, disabled-provider behavior, and configuration docs remain explicit.
- Tests cover parsing, settings, and fallback behavior.
- Only one AI provider can be active for a user at a time.
- Standard providers require the minimum viable user input:
  - OpenAI: API token and optional friendly label, followed by selecting a discovered model.
  - Gemini: API token and optional friendly label, followed by selecting a discovered model.
  - Anthropic: API token and optional friendly label, followed by selecting a discovered model.
- Standard provider service details are preconfigured in code, including default endpoint and
  sensible default model where the provider supports it.
- Custom OpenAI-compatible providers expose the additional user-managed fields needed to work:
  friendly label, base URL, API token, and selected or manually entered model name.
- The settings UI distinguishes standard providers from custom providers so users are not asked for
  endpoint details unless the provider mode actually requires them.
- Standard providers discover model choices from their model-list APIs after the key is saved.
- Custom OpenAI-compatible discovery is best-effort and falls back to manual model entry when a
  local endpoint or gateway cannot list models.

## Plan

1. Confirm next provider priorities from the roadmap.
1. Confirm next provider priorities from the roadmap.
2. Normalize provider configuration so standard providers are configured from prefilled service
   details plus minimal user-owned inputs.
3. Discover available models after key save, then require explicit model selection before enabling.
4. Add one provider/mode slice at a time with validation and docs.
5. Preserve shared visibility, provenance, and failure-mode conventions.
6. Update routing docs if validation or risk posture changes.

## Progress Log

- 2026-04-28: Created active provider-expansion workstream.
- 2026-05-01: Added provider setup success criteria: one active provider per user, standard
  providers preconfigured with published service details, and custom OpenAI-compatible endpoints
  requiring only the extra fields needed for a workable endpoint.
- 2026-05-01: Implemented the Anthropic provider slice through the Messages API. Standard provider
  setup now uses preconfigured service endpoints/default models, and custom OpenAI-compatible setup
  retains explicit base URL/model fields.
- 2026-05-01: Added authenticated model discovery for OpenAI, Gemini, Anthropic, and best-effort
  OpenAI-compatible endpoints. Settings now uses a two-step setup: save key/discover models, then
  enable one selected model. Custom endpoint discovery failures preserve manual model entry.

## Decisions

- Treat provider expansion as separate from artefact-AI feature sequencing.
- Prefer minimum viable provider setup over asking users for provider internals. Standard providers
  should mostly require an API token; custom endpoints carry the extra endpoint/model burden.
- Use stable default model ids for standard providers as preselection hints when providers return
  them:
  `gpt-5.2`, `gemini-2.5-flash`, and `claude-sonnet-4-20250514`.
- Treat model availability as API-key scoped. Discovery requires the saved token because account
  entitlement, region, beta access, or billing state may affect returned models.

## Validation

Commands to run before completion:

```sh
make test
```

Latest focused validation:

```sh
.venv/bin/ruff check app/services/ai.py app/api/routes/session_ui.py app/db/models/ai_provider_setting.py tests/test_ai_service.py tests/test_session_ui_routes.py tests/test_database_baseline.py migrations/versions/20260501_0013_ai_provider_model_discovery.py
PYTHONPATH=. .venv/bin/pytest tests/test_ai_service.py tests/test_session_ui_routes.py tests/test_database_baseline.py
PYTHONPATH=. .venv/bin/pytest tests/test_job_detail_routes.py::test_job_detail_ai_generation_uses_openai_provider_with_saved_key tests/test_job_detail_routes.py::test_job_detail_ai_generation_uses_gemini_provider_with_saved_key tests/test_job_detail_routes.py::test_job_detail_ai_generation_uses_anthropic_provider_with_saved_key
```

## Risks

- Provider-specific branching can make the AI surface harder to verify unless contracts stay centralized.
