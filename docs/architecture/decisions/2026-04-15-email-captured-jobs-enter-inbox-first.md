# ADR 2026-04-15: Email-Captured Jobs Enter Inbox First

## Status

Accepted

## Decision

Jobs discovered in alerts, recruiter emails, or forwarded opportunity emails should have a low-friction path into Inbox before they become active work.

## Rationale

- Email is a common discovery channel, but an email mention is not yet an intentional application decision.
- Inbox preserves a lightweight judgment step before the job enters Active Work.
- The first implementation should remain user-initiated before heavier mailbox polling or provider integrations.
