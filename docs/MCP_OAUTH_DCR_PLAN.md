# MCP OAuth 2.0 and Dynamic Client Registration Plan

## Purpose

This document adds an explicit prerequisite for MCP support: Application Tracker must support an OAuth 2.0 based authorization model with Dynamic Client Registration before exposing MCP tools beyond local experimentation.

MCP clients are external agent applications. They should not receive static app tokens copied manually into arbitrary clients as the long-term integration model. They need a standards-based registration and authorization flow that allows clients to request scoped access, users to approve that access, and Application Tracker to revoke or audit it later.

---

## Decision

OAuth 2.0 with Dynamic Client Registration is a prerequisite for production-quality MCP support.

The MCP tool taxonomy can be planned independently, but runtime MCP access should be gated behind OAuth/DCR-compatible client registration and scoped authorization.

---

## Why this matters

MCP changes the trust boundary:

- an external AI client may read jobseeker data
- an external AI client may create visible outputs
- later clients may request state-changing permissions
- headless operation may bypass UI review moments

A simple static token is not enough for the long-term model because the app needs to know:

- which client registered
- which user authorized it
- which scopes were granted
- when the client last used access
- which redirect URIs or callback channels are allowed
- how to revoke access
- how to rotate credentials
- how to audit client-created outputs

---

## OAuth roles

For MCP integration, Application Tracker should act as the authorization server and resource server for its own data.

Conceptual roles:

```text
Jobseeker
  authorizes access

MCP Client
  external AI client or local agent process

Application Tracker Authorization Server
  registers clients, issues tokens, manages consent

Application Tracker Resource Server
  serves MCP tools/resources subject to scopes
```

In a small self-hosted deployment these roles may run inside the same FastAPI app, but they should remain conceptually separate.

---

## Dynamic Client Registration requirement

Dynamic Client Registration allows an MCP-capable client to register itself with Application Tracker before requesting authorization.

The registration record should include, where applicable:

```text
client_id
client_name
client_uri
redirect_uris
grant_types
response_types
scope
contacts
logo_uri optional
token_endpoint_auth_method
created_at
updated_at
revoked_at
```

The app should not assume every MCP client is preconfigured manually.

---

## Authorization flow direction

For user-facing MCP clients, prefer Authorization Code with PKCE.

This supports:

- user consent
- scoped authorization
- no static secret embedded in local clients
- safer local and desktop client flows

For local development, a constrained development mode may exist, but it must be clearly marked as non-production.

---

## Scope mapping

OAuth scopes should map directly to MCP permission scopes.

Initial scopes:

```text
mcp:read_profile
mcp:read_jobs
mcp:read_artefacts
mcp:read_competencies
mcp:read_focus
mcp:write_ai_outputs
```

Deferred scopes:

```text
mcp:write_notes
mcp:write_artefacts
mcp:write_competency_evidence
mcp:mutate_workflow
mcp:admin
```

Default consent should grant the smallest useful scope set.

For the first production-quality MCP slice, this likely means:

```text
mcp:read_profile
mcp:read_jobs
mcp:read_artefacts
mcp:read_competencies
mcp:read_focus
mcp:write_ai_outputs
```

State-changing scopes should not be included in default consent.

---

## Token model

Tokens should be scoped, revocable, and auditable.

At minimum, track:

```text
access_token hash
refresh_token hash if refresh is supported
client_id
owner_id
scopes
issued_at
expires_at
revoked_at
last_used_at
```

Do not store raw token values after issuance.

---

## Consent model

The jobseeker should see a consent screen that explains:

- client name
- requested scopes
- what the client can read
- what the client can write
- whether the client can mutate workflow state
- revocation path

Consent copy should avoid vague language like “access your account.” It should describe Application Tracker domain objects.

Example:

```text
This client can read your job summaries, artefact previews, Focus queue, and competency evidence summaries. It can save visible Markdown AI outputs. It cannot change job status, delete records, or overwrite artefacts.
```

---

## Client management UI

Application Tracker should eventually expose a client/token management UI where the user can:

- view registered MCP clients
- view scopes granted
- see last-used time
- revoke access
- rotate credentials where applicable
- inspect MCP-created outputs

This may live under Settings or Admin.

---

## Development mode

For early local testing, a temporary local-only development mode may be acceptable, but it should not be confused with production MCP support.

Development mode constraints:

- disabled by default
- localhost or private LAN only
- clear warning in docs
- no public exposure
- no mutation tools
- use seeded/local token only if necessary

The production path remains OAuth 2.0 + DCR.

---

## Impact on MCP implementation sequence

OAuth/DCR changes the MCP task order.

Before implementing runtime MCP tools, the project should add:

1. OAuth/DCR architecture decision
2. client registration model
3. authorization/consent model
4. scope model
5. token storage/revocation model
6. client management UI plan
7. test plan for scope enforcement

Only after that should production MCP tools be exposed.

A local prototype may still be possible, but it must be labelled as local-only and non-production.

---

## Acceptance criteria for production MCP auth

Production-quality MCP support requires:

- Dynamic Client Registration support or a deliberate documented equivalent for self-hosted deployments
- Authorization Code with PKCE for user-facing clients where applicable
- scoped access tokens
- token expiry and revocation
- registered client records
- user consent screen
- client management/revocation UI
- owner scoping on every tool/resource
- audit logging for MCP writes
- tests for insufficient scope and revoked clients

---

## Decision statement

MCP runtime support must not be treated as a simple API-token feature. Application Tracker should plan MCP around OAuth 2.0, Dynamic Client Registration, scoped authorization, consent, token revocation, and auditability. Static tokens may be acceptable only for constrained local development and must not define the production security model.
