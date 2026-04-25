# UI Surface Map

This document is a high-level map of the current server-rendered product surfaces.
It is intended for design and UX review, not implementation detail.

It answers four questions:

1. What pages exist today?
2. What is on each page?
3. What actions can the user take from that page?
4. What API call or form post is triggered, and what result comes back into the UI?

## Product Structure Today

The product is currently organized around these user-visible surfaces:

- `Focus`: a personal prioritization page
- `Inbox`: intake queue for captured or suggested opportunities
- `Board`: workflow view across statuses
- `Job Workspace`: the main execution surface for one opportunity
- `Artefacts`: reusable document library
- `Capture`: setup for bookmarklet/browser intake
- `Settings`: profile, AI provider setup, and capture token management
- `Help`: product guidance
- `Admin`: self-hosted operations and capture token management
- `Login` / `Setup`: auth entry points

## Shared Layout Pattern

Most authenticated pages share the same shell:

- top bar:
  - product brand
  - primary navigation: `Focus`, `Inbox`, `Board`
  - optional contextual chip
  - page-level actions
  - user menu
- page hero:
  - kicker
  - title
  - subtitle
- page body:
  - single column, split layout, or workspace layout
- recurring surface types:
  - hero panel
  - page panel
  - emphasis panel
  - soft panel
  - visible AI output cards

## Current AI Placement

AI is currently present on these surfaces:

- `Focus`
  - one optional AI nudge in the aside
- `Inbox review`
  - AI review support actions in the aside
  - visible AI output panel in the main column
- `Job Workspace`
  - visible AI output panel in the main column
  - AI generation actions in the aside
  - AI artefact help in the artefact section
- `Artefacts`
  - no direct generation controls
  - provenance from AI-generated drafts saved as artefacts is visible

This is the area most likely to need design control and consolidation.

---

## Page Inventory

| Page | Route | Primary purpose | Main user mode |
| --- | --- | --- | --- |
| Focus | `GET /focus` | Decide what deserves attention now | Prioritize |
| Inbox | `GET /inbox` | Review captured opportunities before they become active work | Triage |
| Inbox Review | `GET /inbox/{job_uuid}/review` | Clean up one candidate before accepting or dismissing | Review |
| Board | `GET /board` | Scan active opportunities by workflow status | Manage flow |
| Add Job | `GET /jobs/new` | Create an intentional manual job entry | Add intentionally |
| Job Workspace | `GET /jobs/{job_uuid}` | Execute work for one opportunity | Do the work |
| Artefacts | `GET /artefacts` | Manage reusable working assets | Reuse / maintain |
| Capture Setup | `GET /api/capture/bookmarklet` | Configure browser capture | Configure intake |
| Settings | `GET /settings` | Maintain profile, AI, and capture tokens | Configure self |
| Help | `GET /help` | Explain product model and setup | Learn |
| Admin | `GET /admin` | Self-hosted admin and capture operations | Operate |
| Login | `GET /login` | Sign in | Authenticate |
| Setup | `GET /setup` | Create first admin | Bootstrap |

---

## 1. Focus

**Route**

- `GET /focus`

**Purpose**

- Personal prioritization surface
- Decides what should be handled now, not a workflow dashboard

**Current page regions**

- hero/title area
- metrics/stat band
- follow-up queue card
- stale jobs card
- recent jobs card
- upcoming interviews card
- aside with:
  - target/profile summary
  - AI nudge
  - setup/profile prompts when profile is thin

**Primary user actions**

- open a job from any focus list
- trigger AI nudge for the selected Focus target

**API/form actions**

- `POST /focus/ai-nudge`

**UI result**

- stores a visible AI `recommendation`
- re-renders Focus with success/error flash
- output appears in the Focus aside for the selected target job

**Current AI footprint**

- small and controlled compared with other surfaces
- one recommendation area only

---

## 2. Inbox

### 2.1 Inbox List

**Route**

- `GET /inbox`

**Purpose**

- Queue of captured opportunities that are not yet active work

**Current page regions**

- hero/title area
- list of inbox cards
  - source label
  - confidence label
  - title
  - company/location
  - source action
  - captured timestamp
  - actions
- aside with:
  - triage guidance
  - review habits

**Primary user actions**

- accept candidate
- open review page
- dismiss candidate
- paste email
- add manual job

**API/form actions**

- `POST /inbox/{job_uuid}/accept`
- `POST /inbox/{job_uuid}/dismiss`
- `GET /inbox/{job_uuid}/review`
- `GET /inbox/email/new`
- `GET /jobs/new`

**UI result**

- accepted item moves into active work
- dismissed item is archived/removed from active queue
- review opens the detailed triage surface

### 2.2 Inbox Review

**Route**

- `GET /inbox/{job_uuid}/review`

**Purpose**

- Clean up extracted fields and decide whether to promote or dismiss one candidate

**Current page regions**

- main column:
  - candidate fields form
  - visible AI output panel
- aside:
  - AI review support
  - captured provenance
  - promote/dismiss controls

**Primary user actions**

- save reviewed fields
- open full Job Workspace
- generate AI fit summary
- generate AI next step
- accept to interested
- dismiss and archive

**API/form actions**

- `POST /inbox/{job_uuid}/review`
- `POST /inbox/{job_uuid}/ai-outputs`
- `POST /inbox/{job_uuid}/accept`
- `POST /inbox/{job_uuid}/dismiss`

**UI result**

- saved fields update the inbox candidate only
- AI output appears in the visible AI panel
- accept promotes into active workflow
- dismiss removes from active consideration

**Current AI footprint**

- one visible AI output panel
- one AI action panel
- this is a meaningful AI surface, but still bounded

### 2.3 Email Paste / Intake

**Routes**

- `GET /inbox/email/new`
- `POST /inbox/email`
- `POST /api/inbox/email-captures`

**Purpose**

- Manual intake of job-related email content into Inbox

**Current page regions**

- paste form
- instructions about provenance and review-before-accept

**Primary user actions**

- paste email content
- submit for extraction into Inbox

**UI result**

- creates or updates an Inbox candidate
- user returns to Inbox / Inbox review flow

---

## 3. Board

**Route**

- `GET /board`

**Purpose**

- Workflow view across job statuses
- Not the strategic center; this is the flow-management page

**Current page regions**

- hero/title area
- workflow tabs:
  - Prospects
  - In Progress
  - Outcomes
  - All Active
  - Archived
- metrics/stat band by status
- board content:
  - lane layout for denser workflow views
  - list layout for simpler views
- job cards with:
  - title
  - company/location/salary/source
  - stage age
  - follow-up indicator
  - next action buttons

**Primary user actions**

- change board workflow tab
- open job workspace
- move jobs between statuses from card actions

**API/form actions**

- workflow view is query-driven: `GET /board?workflow=...`
- status transitions are driven through Job Workspace routes or board-specific actions depending on implementation path

**UI result**

- re-renders board by workflow
- reflects updated job state

**Current AI footprint**

- none directly on Board today

---

## 4. Add Job

**Route**

- `GET /jobs/new`
- `POST /jobs/new`

**Purpose**

- Intentional manual job entry

**Current page regions**

- single form with:
  - title
  - company
  - status
  - source/apply URLs
  - location
  - remote policy
  - salary fields
  - description
  - initial note

**Primary user actions**

- create a manual job

**UI result**

- creates a new job and redirects into Job Workspace

---

## 5. Job Workspace

**Route**

- `GET /jobs/{job_uuid}`

**Purpose**

- Main execution surface for one opportunity
- This is currently the densest page in the product

**Current page organization**

### Main column

1. workspace hero
   - editable title
   - company / location / salary / stage pill
2. next action panel
3. role overview
   - editable structured fields
4. role description
   - editable description
   - markdown-rendered display
5. application readiness
6. visible AI output
7. applications and interviews

### Aside

1. external links
2. AI actions
   - fit summary
   - next step recommendation
3. workflow/state
4. move status
5. artefacts
   - linked artefacts
   - AI artefact help
   - attach existing artefact
   - upload artefact
6. schedule interview
7. mark applied
8. external workflow actions
   - application started
   - blocker
   - return note
9. archive / unarchive
10. add note
11. provenance
12. journal/timeline

**Primary user actions**

- inline edit core job fields
- move status
- record application/interview events
- add notes
- upload/link artefacts
- open external links
- generate AI outputs
- generate artefact suggestions
- generate tailoring guidance
- generate drafts
- save drafts as artefacts

**Core API/form actions**

- editing / workflow:
  - `PATCH /api/jobs/{job_uuid}`
  - `POST /jobs/{job_uuid}/status`
  - `POST /jobs/{job_uuid}/mark-applied`
  - `POST /jobs/{job_uuid}/application-started`
  - `POST /jobs/{job_uuid}/blockers`
  - `POST /jobs/{job_uuid}/return-note`
  - `POST /jobs/{job_uuid}/interviews`
  - `POST /jobs/{job_uuid}/notes`
  - `POST /jobs/{job_uuid}/archive`
  - `POST /jobs/{job_uuid}/unarchive`
- AI job guidance:
  - `POST /jobs/{job_uuid}/ai-outputs`
- artefacts:
  - `POST /jobs/{job_uuid}/artefacts`
  - `POST /jobs/{job_uuid}/artefact-links`
  - `POST /jobs/{job_uuid}/artefact-suggestions`
  - `POST /jobs/{job_uuid}/artefacts/{artefact_uuid}/tailoring-guidance`
  - `POST /jobs/{job_uuid}/artefacts/{artefact_uuid}/drafts`
  - `POST /jobs/{job_uuid}/ai-outputs/{output_id}/save-draft`

**AI outputs currently visible here**

- `fit_summary`
- `recommendation`
- `artefact_suggestion`
- `tailoring_guidance`
- `draft`

**Current AI/UI observation**

- this is the surface with the most accumulation
- AI is currently mixed into:
  - general job guidance
  - artefact selection
  - artefact tailoring
  - draft creation
- it is functional, but visually dense and likely the main candidate for design simplification

---

## 6. Artefacts

**Route**

- `GET /artefacts`

**Purpose**

- Library of reusable working assets

**Current page regions**

- artefact card grid
- each card shows:
  - kind
  - filename
  - size and updated time
  - purpose
  - version
  - notes
  - linked jobs
  - provenance block for saved AI drafts
  - metadata editor
  - download action

**Primary user actions**

- review existing assets
- edit artefact metadata
- download artefact

**API/form actions**

- `POST /artefacts/{artefact_uuid}/metadata`
- `GET /artefacts/{artefact_uuid}/download`

**UI result**

- metadata updates in place
- artefact provenance is visible if the asset came from an AI draft

**Current AI footprint**

- indirect rather than active
- provenance from AI-generated drafts is shown here

---

## 7. Capture Setup

**Route**

- `GET /api/capture/bookmarklet`

**Purpose**

- Configure browser-based capture

**Current page regions**

1. create capture token
2. generate bookmarklet
   - tracker URL
   - token input
   - live bookmarklet link
3. generated code textarea

**Primary user actions**

- create token in Settings/Admin
- paste token here
- generate bookmarklet
- drag bookmarklet to bookmarks bar

**Backing API**

- capture action itself posts to:
  - `POST /api/capture/jobs`

**UI result**

- on a live job page, bookmarklet captures:
  - page URL
  - page title
  - selected text
  - body text
  - raw HTML
  - JSON-LD job posting if present
- creates or updates a captured job, usually flowing into Inbox

---

## 8. Settings

**Route**

- `GET /settings`

**Purpose**

- Personal configuration: profile, AI, capture tokens

**Current page regions**

1. job-search profile
2. AI readiness
   - setup help
   - provider form
   - provider summary table
3. create API token
4. API token table

**Primary user actions**

- maintain profile context
- configure one active AI provider
- create/revoke capture tokens

**API/form actions**

- `POST /settings/profile`
- `POST /settings/ai-provider`
- `POST /settings/api-tokens`
- `POST /settings/api-tokens/{token_uuid}/revoke`

**UI result**

- profile updates shape future AI/context behavior
- AI provider setup affects explicit AI generation only
- new token is shown once and linked to Capture setup

**Current AI footprint**

- setup/config only
- no generated content on this page

---

## 9. Help

**Route**

- `GET /help`

**Purpose**

- Explain the product model and setup paths

**Current page regions**

- what the app is for
- daily workflow
- page-by-page explanations:
  - Focus
  - Inbox
  - Board
  - Job Workspace
  - Artefacts
  - Capture
- settings and privacy
- AI setup
- admin operations

**Primary user actions**

- read guidance
- jump to settings or capture setup

**Current AI footprint**

- guidance only

---

## 10. Admin

**Route**

- `GET /admin`

**Purpose**

- Self-hosted administrative operations

**Current page regions**

- system summary stats
- admin tasks
- create capture token
- API token table
- backup/download actions

**Primary user actions**

- review user/job/token counts
- create/revoke admin-side capture tokens
- access backup flow
- jump to capture setup

**API/form actions**

- `POST /admin/api-tokens`
- `POST /admin/api-tokens/{token_uuid}/revoke`
- `GET /admin/backup`

**Current AI footprint**

- none

---

## 11. Login / Setup

### Login

**Route**

- `GET /login`
- `POST /login`

**Purpose**

- Local sign-in

**Current page regions**

- email
- password
- submit

### Setup

**Route**

- `GET /setup`
- `POST /setup`

**Purpose**

- First-run bootstrap for initial admin

**Current page regions**

- email
- display name
- password
- confirm password
- submit

---

## Surface-to-Action Summary

| Surface | Most important actions today |
| --- | --- |
| Focus | Open target job, generate AI nudge |
| Inbox | Accept, Review, Dismiss, Paste email |
| Inbox Review | Save review, generate AI review help, Accept, Dismiss |
| Board | Open workspace, change workflow view, move statuses |
| Job Workspace | Edit, move status, manage artefacts, generate AI outputs, save AI drafts |
| Artefacts | Edit metadata, download, inspect provenance |
| Capture Setup | Generate bookmarklet configuration |
| Settings | Save profile, save AI provider, create/revoke tokens |
| Help | Read guidance, jump to setup pages |
| Admin | Operate tokens and backup |

---

## Design-Relevant Observations

These are factual observations about the current UI architecture, not redesign recommendations.

1. `Job Workspace` has become the most crowded surface.
   - It contains operational workflow, content editing, AI guidance, artefact management, provenance, and history in one page.

2. AI appears in multiple modes, not one.
   - guidance
   - triage support
   - artefact suggestion
   - tailoring guidance
   - draft generation

3. AI output is visible and persistent.
   - This is good for auditability, but it creates panel growth if not tightly grouped.

4. `Inbox Review` and `Job Workspace` now have parallel AI patterns.
   - Both include action controls plus visible AI output.

5. `Artefacts` is cleaner than `Job Workspace`.
   - It currently acts more like a library and provenance surface than a generative workspace.

6. The current information architecture is still coherent, but the visual hierarchy of AI versus core workflow is likely no longer controlled enough.

---

## Suggested Use With Design

For design review, the most useful pages to inspect first are:

1. `Focus`
2. `Inbox`
3. `Inbox Review`
4. `Board`
5. `Job Workspace`
6. `Artefacts`
7. `Settings`

Those pages cover:

- prioritization
- intake
- review
- workflow
- execution
- reusable assets
- configuration

If needed, this document can be followed by a second pass that maps:

- component patterns
- panel types
- button/action taxonomy
- AI-specific interaction patterns
- candidate simplification opportunities
