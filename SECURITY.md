# Security

Application Tracker stores sensitive job-search data, including resumes, cover letters, salary expectations, recruiter communications, interview notes, and outcomes.

## Current Security Status

This clean rebuild is not yet ready for exposed public internet deployment.

Safe current assumptions:

- local development;
- private LAN or trusted homelab testing;
- no real personal data unless the deployment is protected and backed up.

Do not expose the application directly to the internet until real authentication, authorization, CSRF protection, and deployment hardening are implemented.

## Security Goals

Before the first public self-hosted release:

- production mode must not use placeholder auth;
- users must not be able to read or modify another user's records;
- browser capture must use scoped API tokens;
- server-rendered form submissions must be protected if session cookies are used;
- uploaded artefacts must be stored safely and never served by raw filesystem path;
- backup and restore instructions must be documented;
- external AI or API providers must be disabled by default.

## Reporting Issues

Until the project has a public issue template, document suspected security issues privately before publishing exploit details.

Recommended report content:

- affected route or feature;
- expected behavior;
- observed behavior;
- reproduction steps;
- whether private data exposure is possible.

