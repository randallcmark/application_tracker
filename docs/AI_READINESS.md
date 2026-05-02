# AI Readiness

AI support is intentionally split into two parts:

- durable, visible records that can be reviewed by the user;
- future provider execution that may create those records.

This slice now implements durable records, provider configuration, and the first explicit Job
Workspace generation loop. Provider API keys are stored encrypted at rest. AI still does not
silently mutate jobs, profiles, artefacts, or workflow state.

## Provider Setup

Open User Settings from the username menu:

```text
http://127.0.0.1:8000/settings#ai
```

Supported providers:

- OpenAI;
- Gemini via Google AI Studio;
- Anthropic;
- OpenAI-compatible local endpoint.

Setup flow:

1. Save the provider API key and optional friendly label.
2. The app queries the provider's available models using that key.
3. Select one discovered model and enable it.

Fields:

- provider;
- label;
- base URL for custom OpenAI-compatible providers only;
- discovered models;
- selected model;
- enabled flag.

The enabled flag only permits explicit user-triggered generation. Execution currently supports:

- OpenAI via API key;
- Gemini via Google AI Studio API key;
- OpenAI-compatible local endpoints;
- Anthropic via API key.

Provider setup guidance:

- OpenAI API access uses an API key from the OpenAI platform, not a ChatGPT subscription login.
- OpenAI documents ChatGPT and API billing as separate systems:
  [Billing settings in ChatGPT vs Platform](https://help.openai.com/en/articles/9039756-billing-settings-in-chatgpt-vs-platform)
- OpenAI API key setup starts from the platform quickstart:
  [Developer quickstart](https://platform.openai.com/docs/quickstart/using-the-api)
- OpenAI model discovery uses:
  [List models](https://platform.openai.com/docs/api-reference/models/list)
- Gemini API key setup starts from Google AI Studio:
  [Using Gemini API keys](https://ai.google.dev/gemini-api/docs/api-key)
- Gemini model discovery uses:
  [Method: models.list](https://ai.google.dev/api/rest/generativelanguage/models/list)
- Gemini API reference:
  [Gemini API reference](https://ai.google.dev/docs/gemini_api_overview/)
- Anthropic API access uses an API key from the Anthropic Console:
  [Anthropic API overview](https://docs.anthropic.com/en/api/getting-started)
- Anthropic model discovery uses:
  [List Models](https://docs.anthropic.com/en/api/models-list)

## AI Output Records

The database can now store visible AI output records for:

- recommendation;
- fit summary;
- draft;
- profile observation;
- artefact suggestion.

Each output is owner-scoped and may be tied to a job, artefact, provider, model, and source context.
Future UI work should render these records where the user is working, such as the job workspace,
Inbox, Focus, or Artefact Library.

Detailed planning for artefact-aware AI work now lives in `docs/ARTEFACT_AI_PLAN.md`. The next
recommended artefact AI slice is existing artefact suggestion in Job Workspace before tailoring or
draft generation.

## First Visible Execution Slice

Job Workspace now renders visible AI output records and exposes explicit generation actions for:

- fit summary;
- recommendation.

Generation is:

- user-triggered only;
- visible on the same Job Workspace page;
- tied to a configured enabled provider;
- non-mutating with respect to workflow state.

If no usable provider is enabled, or a configured provider is missing a required key/model, the user
sees a visible error on return to Job Workspace.

Provider setup expectation:

- Exactly one provider is active for a user at a time.
- Standard providers should be workable from the minimum user-owned input:
  - OpenAI: API token and optional friendly label, then selected discovered model.
  - Gemini: API token and optional friendly label, then selected discovered model.
  - Anthropic: API token and optional friendly label, then selected discovered model.
- Published service details for standard providers, such as endpoint shape and default model, should
  be preconfigured by the app rather than requested from the user.
- Custom OpenAI-compatible providers require the additional user-managed connection fields:
  friendly label, base URL, API token, and selected or manually entered model name. Discovery is
  best-effort for custom endpoints because local and gateway APIs vary.

## Contract

- AI is optional.
- AI output is inspectable.
- AI never silently changes jobs, artefacts, profile data, or workflow state.
- External calls must not happen unless a provider is explicitly configured and the user triggers an
  action.
