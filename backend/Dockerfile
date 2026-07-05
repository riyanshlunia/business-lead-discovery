FROM mcr.microsoft.com/playwright/python:v1.61.0-noble

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY pyproject.toml ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# Upgrade pip and install the app
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e "."

# Install Playwright chromium browser
RUN playwright install chromium

# Single stage CMD running migrations and starting the FastAPI server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]