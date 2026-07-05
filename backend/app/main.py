from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from alembic import command
from alembic.config import Config

from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()

configure_logging()

print("CORS ORIGINS:", settings.cors_origin_list)

# -----------------------------
# Run Alembic migrations
# -----------------------------
try:
    print("Running database migrations...")

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

    command.upgrade(alembic_cfg, "head")

    print("Database migrations completed successfully.")
except Exception as e:
    print("Failed to run migrations:")
    print(e)
    raise

# -----------------------------
# Create FastAPI app
# -----------------------------
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # We'll tighten this later
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(jobs_router, prefix=settings.api_v1_prefix)