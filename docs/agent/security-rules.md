# Security Rules

Use this file for authentication, authorization, secrets, data handling, dependency, deployment, and network changes.

## Rules

- Do not weaken auth, authorization, isolation, or validation to make a task pass.
- Do not log secrets, tokens, credentials, or sensitive personal data.
- Validate untrusted input at boundaries.
- Prefer allowlists over blocklists for sensitive operations.
- Keep secret names in docs; keep secret values out of the repository.
- Treat dependency and supply-chain changes as security-sensitive.
- Record security tradeoffs in an execution plan or architecture decision record.

## Required Review Points

For security-sensitive work, check:

- who can access the changed path;
- what data crosses the boundary;
- what happens on malformed input;
- what is logged;
- what external systems are called;
- what tests or checks prove the intended constraint.

Primary repo references:

- `docs/AUTHENTICATION.md`
- `docs/API_TOKENS_AND_CAPTURE.md`
- `docs/architecture/boundaries.md`
- `docs/architecture/decisions/`

## Escalation

Ask for human judgment when a task requires changing security posture, accepting a new class of risk, bypassing validation, or handling credentials not already documented for local development.
