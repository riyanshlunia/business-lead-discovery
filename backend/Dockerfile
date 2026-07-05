FROM mcr.microsoft.com/playwright/python:v1.61.0-noble AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY pyproject.toml ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[dev]"

FROM base AS migrate
CMD ["alembic", "upgrade", "head"]

FROM base AS worker
CMD ["celery", "-A", "app.workers.celery_app:celery_app", "worker", "--loglevel=INFO", "--concurrency=2"]

# LAST STAGE = API
FROM base
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]