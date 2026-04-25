# Job Workspace V1 Archive

This document preserves the immediately previous Job Workspace redesign before the v2 reference refresh.

## Recovery Reference

- Git checkpoint: `6110bbe`
- Renderer entry point:
  - [job_detail.py](/Users/markrandall/GitHub/application_tracker/app/api/routes/job_detail.py)
- Prior design direction:
  - three-column workspace with:
    - left rail summary/navigation/health
    - main column distributed operational sections
    - right rail visible AI assistant plus visible AI output list

## Why It Was Archived

The v1 layout improved structure versus the older workspace, but it still had two problems:

1. AI content remained too globally visible across the page.
2. Layout density and hierarchy were still inconsistent, especially between operational content and AI content.

## What To Recover If Needed

If this version needs to be revisited, recover from git at or before:

- `6110bbe`

That checkpoint contains:

- reusable Job Workspace section builders
- left/middle/right rail layout contract
- UI contract test coverage for the v1 layout

## Replaced By

- external reference:
  - `/Users/markrandall/Documents/job_workspace_v2_design_reference.html`
- current design intent:
  - one persistent AI rail summary
  - artefact-local AI workspace
  - calmer main workspace surface
