# Google Maps Lead Generation Platform

A modular SaaS scaffold for discovering Google Maps businesses, enriching them with website and contact data, scoring lead quality, and exporting results.

## Stack

- Frontend: Next.js, React, TailwindCSS, Shadcn-style UI primitives, TanStack Query, AG Grid
- Backend: FastAPI, Python 3.12, SQLAlchemy 2, Celery, Redis, Playwright, httpx, BeautifulSoup
- Database: PostgreSQL
- Deployment: Docker, Docker Compose

## Services

- `frontend`: user interface for creating jobs, monitoring progress, and viewing results
- `backend`: FastAPI API for job creation, polling, and exports
- `worker`: Celery worker running the scraper pipeline with Playwright
- `postgres`: relational storage
- `redis`: broker, result backend, and cache

## Quick Start

1. Copy `.env.example` to `.env` and adjust secrets.
2. Start the stack with Docker Compose.
3. Open the frontend, create a job like `Hotels in Mumbai`, and wait for the worker to finish.

## Notes

- Scraping only happens in background workers.
- The maps module discovers businesses only.
- Website analysis, contact extraction, and lead scoring are isolated services and can be replaced independently.
