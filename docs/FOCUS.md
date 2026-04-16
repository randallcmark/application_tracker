# Focus

Focus is the default logged-in home surface:

```text
http://127.0.0.1:8000/focus
```

It is intentionally small in the first version. It uses existing data only and does not require scheduler, Inbox, or AI support.

## What It Shows

- A profile-completion prompt when the user has not filled in their job-search profile.
- Due and overdue follow-ups from job timeline notes.
- Stale active jobs that have not changed recently.
- Upcoming interviews.
- Recent saved or interested jobs.
- Summary counts for due follow-ups, stale jobs, upcoming interviews, and active jobs.

Archived jobs and other users' jobs are hidden.

## Navigation

Authenticated root requests now redirect to `/focus`.

The board remains available at:

```text
http://127.0.0.1:8000/board
```

Focus links directly to job detail pages, Board, Add job, Capture setup, Profile, Settings, and Admin for admins.

## Test Instructions

1. Log in.
2. Open `/`.
3. Confirm the browser lands on `/focus`.
4. Confirm `/focus` shows empty states if there are no jobs or follow-ups.
5. Add a profile at `/settings#profile` and confirm the profile prompt disappears.
6. Add jobs, follow-ups, or interviews and confirm they appear on Focus.
