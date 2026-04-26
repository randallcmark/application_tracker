FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN pip install --no-cache-dir .
RUN python -c "import app.services.ai; import app.services.artefacts; import app.services.competency_evidence"

EXPOSE 8000

ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
