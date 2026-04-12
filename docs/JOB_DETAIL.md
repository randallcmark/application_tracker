# Job Detail

Job detail pages are available at:

```text
http://127.0.0.1:8000/jobs/job-uuid
```

The page requires a logged-in browser session and is owner-scoped. Another user's job returns
`404`.

New jobs can be created from:

```text
http://127.0.0.1:8000/jobs/new
```

## Current Behavior

- Shows the captured job title, company, status, board position, source, location, salary,
  captured timestamp, source URL, and apply URL.
- Shows the captured description.
- Creates manual jobs from the browser.
- Edits job details after capture or manual creation through focused section editors.
- Shows the job timeline, including `stage_change` events recorded from board movement.
- Adds notes to the timeline, with an optional follow-up date.
- Uploads, lists, and downloads job-level artefacts.
- Marks a job applied and creates or updates the application record.
- Schedules interviews and shows scheduled interview records.
- Archives a job with an optional timeline note.
- Restores an archived job to an active board status with an optional timeline note.
- Links back to `/board`.

## Browser Test

1. Start the app:

```bash
source .venv/bin/activate
make run
```

2. Sign in at:

```text
http://127.0.0.1:8000/login
```

3. Open the board:

```text
http://127.0.0.1:8000/board
```

4. Click a card title.

5. Confirm the detail page shows the job fields and timeline.

6. Use Add job from the board, create a manual job, and confirm it opens the new detail page.

7. Open the relevant edit selector for a section, change only one field such as title, location, URL,
   salary, or description, and confirm the corrected value remains after reload without clearing the
   other fields.

8. Upload a resume or cover letter artefact and confirm it appears in Artefacts with a download link.

9. Add a note with a follow-up date and confirm it appears in the timeline.

10. Use Mark Applied and confirm the page shows an application record and a timeline event.

11. Schedule an interview and confirm the page shows an interview record and timeline event.

12. Use Archive and confirm the job is archived with a timeline event.

13. Open the archived job detail page, use Unarchive, choose an active status, and confirm the
   job returns to that status with a timeline event.

14. Move another job to a different stage on the board, then open the detail page again and confirm the
   new `stage_change` event appears in the timeline.
