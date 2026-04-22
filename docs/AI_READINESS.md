# AI Readiness

AI support is intentionally split into two parts:

- durable, visible records that can be reviewed by the user;
- future provider execution that may create those records.

This slice now implements durable records, provider placeholders, and the first explicit Job
Workspace generation loop. It does not store API keys or silently mutate jobs, profiles, artefacts,
or workflow state.

## Provider Placeholders

Open User Settings from the username menu:

```text
http://127.0.0.1:8000/settings#ai
```

Supported placeholder providers:

- OpenAI;
- Anthropic;
- OpenAI-compatible local endpoint.

Fields:

- provider;
- label;
- base URL;
- model name;
- enabled flag.

The enabled flag only permits explicit user-triggered generation. The first execution path supports
enabled OpenAI-compatible local endpoints. OpenAI and Anthropic remain placeholders in this slice.

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

## First Visible Execution Slice

Job Workspace now renders visible AI output records and exposes explicit generation actions for:

- fit summary;
- recommendation.

Generation is:

- user-triggered only;
- visible on the same Job Workspace page;
- tied to a configured enabled provider;
- non-mutating with respect to workflow state.

If no usable provider is enabled, the user sees a visible error on return to Job Workspace.

## Contract

- AI is optional.
- AI output is inspectable.
- AI never silently changes jobs, artefacts, profile data, or workflow state.
- External calls must not happen unless a provider is explicitly configured and the user triggers an
  action.
