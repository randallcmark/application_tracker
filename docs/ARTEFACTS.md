# Artefacts

Artefacts are files used during a job search: resumes, cover letters, application notes,
interview prep, attestations, and other reusable working materials.

The first library surface is available at:

```text
http://127.0.0.1:8000/artefacts
```

The page requires a logged-in browser session and is owner-scoped.

## Current Behavior

- Lists all artefacts owned by the logged-in user.
- Shows filename, kind, size, updated timestamp, linked job, and linked company when available.
- Links back to the owning job workspace.
- Provides an owner-scoped download path:

```text
http://127.0.0.1:8000/artefacts/artefact-uuid/download
```

- Keeps existing job-level upload and download behavior intact.

## Current Limitations

- Upload still happens from a job workspace.
- Artefacts are not yet reusable across multiple jobs.
- Metadata is limited to the existing fields: kind, filename, content type, size, checksum, storage
  key, and existing job/application/interview links.
- Purpose, version labels, notes, outcome linkage, and many-to-many job associations remain planned
  follow-on work.

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

3. Open any job workspace:

```text
http://127.0.0.1:8000/board
```

4. Upload an artefact from the job workspace.

5. Open:

```text
http://127.0.0.1:8000/artefacts
```

6. Confirm the artefact appears with its linked job and download action.

7. Download the artefact from the library and confirm it matches the uploaded file.
