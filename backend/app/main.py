from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.social import router as social_router, saved_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()

configure_logging()

print("CORS ORIGINS:", settings.cors_origin_list)

app = FastAPI(title=settings.app_name, version="0.1.0")

# Root health check endpoint for platform deployment (e.g. Railway)
@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

# Dynamic CORS Configuration
origins = settings.cors_origin_list
allow_all = "*" in origins or not origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(jobs_router, prefix=settings.api_v1_prefix)
app.include_router(social_router, prefix=settings.api_v1_prefix)
app.include_router(saved_router, prefix=settings.api_v1_prefix)