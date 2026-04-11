# Kanban Board

The first board surface is available at:

```text
http://127.0.0.1:8000/board
```

It requires a logged-in browser session. The root path redirects logged-in users to `/board`;
anonymous users are sent to `/login`.

## Current Behavior

- Shows owner-scoped jobs only.
- Defaults to the `in_progress` workflow view.
- Provides workflow views:
  - `/board?workflow=prospects` for `saved` and `interested`.
  - `/board?workflow=in_progress` for `preparing`, `applied`, and `interviewing`.
  - `/board?workflow=outcomes` for `offer` and `rejected`.
  - `/board?workflow=all` for all active board statuses.
  - `/board?workflow=archived` for archived jobs.
- Hides `archived` jobs from active workflow views.
- Uses a compact workflow dropdown rather than large workflow buttons.
- Links to the manual add-job form at `/jobs/new`.
- Links each card title to a job detail page at `/jobs/{job_uuid}`.
- Groups cards into the selected workflow stages:
  - `saved`
  - `interested`
  - `preparing`
  - `applied`
  - `interviewing`
  - `offer`
  - `rejected`
- Shows how long each job has been in its current stage.
- Flags stale cards using conservative stage thresholds.
- Shows follow-up indicators from timeline notes with follow-up dates:
  - `Follow-up due today`
  - `Follow-up overdue`
  - `Follow-up YYYY-MM-DD`
- Provides a `Move to column` dropdown on each card.
- Persists stage changes with `PATCH /api/jobs/{job_uuid}/board`.
- Supports dragging cards within and across columns.
- Persists drag-and-drop ordering with `PATCH /api/jobs/board`.
- Records status changes in each job's timeline.

The card dropdown remains available as the keyboard-friendly fallback to drag-and-drop.

## Browser Test

1. Start the app:

```bash
source .venv/bin/activate
make run
```

2. In another terminal, create a user, log in, create a token, and capture a job using the smoke
   test in `docs/API_TOKENS_AND_CAPTURE.md`.

3. Open:

```text
http://127.0.0.1:8000/login
```

4. Sign in with the user credentials.

5. Use Add job and confirm the created job appears in the selected board stage.

6. Confirm the captured job appears in `Saved`.

7. Open the card title and confirm the detail page shows the job fields and timeline.

8. Return to the board and switch between `Prospects`, `In Progress`, `Outcomes`, `All Active`,
   and `Archived`.

9. Confirm each card shows `In stage: X days`, and stale cards include `stale`.

10. Drag the card to another stage, or use the `Move to column` dropdown.

11. Refresh the page and confirm the job remains in the new stage.

## Terminal Check

After moving a job in the browser, verify the persisted state:

```bash
curl -s \
  -b cookies.txt \
  "$BASE_URL/api/jobs/$JOB_UUID"
```

The response should include the updated `status`.
