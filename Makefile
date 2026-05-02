.PHONY: check create-admin docker-check docker-down docker-import-smoke docker-logs docker-ps docker-restart docker-up lint migrate package-firefox-extension qnap-deploy qnap-logs qnap-ps run test

PYTHON ?= .venv/bin/python
UVICORN ?= .venv/bin/uvicorn
FIREFOX_EXTENSION_ZIP ?= dist/application-tracker-firefox.zip
QNAP_SSH_TARGET ?= qnap
QNAP_APP_DIR ?= /share/Container/application_tracker
QNAP_COMPOSE_CMD ?= sudo docker compose

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

check: lint test

migrate:
	.venv/bin/alembic upgrade head

create-admin:
	$(PYTHON) -m app.cli users create-admin --email "$$EMAIL"

package-firefox-extension:
	mkdir -p dist
	cd extensions/firefox && zip -r ../../$(FIREFOX_EXTENSION_ZIP) .

run:
	$(UVICORN) app.main:app --reload

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

docker-restart:
	docker compose down
	docker compose up -d --build

docker-ps:
	docker compose ps

docker-logs:
	docker compose logs --tail=120 app

docker-check:
	docker compose build
	docker compose up -d
	docker compose ps
	docker compose logs --tail=80 app

docker-import-smoke:
	docker build -t application-tracker-import-smoke .

qnap-deploy:
	./scripts/deploy_qnap.sh

qnap-ps:
	ssh "$(QNAP_SSH_TARGET)" 'cd "$(QNAP_APP_DIR)" && $(QNAP_COMPOSE_CMD) ps'

qnap-logs:
	ssh "$(QNAP_SSH_TARGET)" 'cd "$(QNAP_APP_DIR)" && $(QNAP_COMPOSE_CMD) logs --tail=120 app'
