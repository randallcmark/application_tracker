# Contributing

Application Tracker is being rebuilt as a clean, self-hosted product. Keep changes small, documented, and safe to publish.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Common Commands

```bash
make test
make lint
make check
make run
```

If you are not using `make`, the equivalent commands are:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/uvicorn app.main:app --reload
```

## Working Agreements

- Do not commit local databases, uploaded artefacts, resumes, cover letters, screenshots, or private job-search data.
- Keep runtime data under `data/` or another ignored path.
- Prefer small commits with one clear purpose.
- Update `project_tracker/PUBLIC_SELF_HOSTED_ROADMAP.md` when roadmap status or scope changes.
- Add or update tests for behavior changes.
- Keep the default app useful without external services.

## GitHub Sync

The intended remote is:

```text
https://github.com/randallcmark/application_tracker.git
```

After authenticating locally with GitHub CLI:

```bash
gh auth login -h github.com
git push -u origin main
```

