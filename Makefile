.PHONY: check lint run test

PYTHON ?= .venv/bin/python
UVICORN ?= .venv/bin/uvicorn

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

check: lint test

run:
	$(UVICORN) app.main:app --reload

