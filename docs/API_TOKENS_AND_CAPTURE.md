# API Tokens And Capture

API tokens are intended for browser extensions, bookmarklets, and local automation.

Tokens are scoped. The first supported scope is:

```text
capture:jobs
```

Token secrets are shown once when created. The database stores only a hash.

## Create A Token

Log in with a browser session first:

```bash
curl -i \
  -c cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"your-password"}' \
  http://127.0.0.1:8000/auth/login
```

Create a token:

```bash
curl -s \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"name":"Browser extension","scopes":["capture:jobs"]}' \
  http://127.0.0.1:8000/auth/api-tokens
```

Response:

```json
{
  "uuid": "token-uuid",
  "name": "Browser extension",
  "scopes": ["capture:jobs"],
  "token": "ats_secret_shown_once"
}
```

Store the `token` value somewhere safe. It cannot be retrieved again.

## Revoke A Token

```bash
curl -i \
  -X DELETE \
  -b cookies.txt \
  http://127.0.0.1:8000/auth/api-tokens/token-uuid
```

Revocation is owner-scoped. A logged-in user cannot revoke another user's token.

## Capture A Job

Use the token as a bearer token:

```bash
curl -i \
  -H "Authorization: Bearer ats_secret_shown_once" \
  -H "Content-Type: application/json" \
  -d '{
    "source_url": "https://jobs.example.com/product-manager",
    "apply_url": "https://jobs.example.com/product-manager/apply",
    "title": "Product Manager",
    "company": "Example Co",
    "location": "Remote",
    "description": "Own the roadmap.",
    "selected_text": "Interesting role",
    "source_platform": "example_jobs",
    "raw_extraction_metadata": {"extractor": "generic"}
  }' \
  http://127.0.0.1:8000/api/capture/jobs
```

New captures return `201` and `created: true`.

Duplicate captures with the same `source_url` for the same user update the existing job,
return `200`, and include `created: false`.

Response:

```json
{
  "uuid": "job-uuid",
  "title": "Product Manager",
  "company": "Example Co",
  "status": "saved",
  "source_url": "https://jobs.example.com/product-manager",
  "apply_url": "https://jobs.example.com/product-manager/apply",
  "created": true
}
```
