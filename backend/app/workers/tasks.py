from __future__ import annotations

import asyncio

from app.database.session import async_session_factory
from app.services.export_service import ExportService
from app.services.pipeline import LeadGenerationPipeline
from app.workers.celery_app import celery_app


@celery_app.task(name="run_lead_job", bind=True)
def run_lead_job(self, job_id: int) -> None:
    asyncio.run(_run_pipeline(job_id))


async def _run_pipeline(job_id: int) -> None:
    from app.core.config import get_settings
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
    LocalSessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    pipeline = LeadGenerationPipeline()
    try:
        async with LocalSessionFactory() as session:
            await pipeline.run(session, job_id)
    finally:
        await engine.dispose()


@celery_app.task(name="build_export", bind=True)
def build_export(self, job_id: int, format_name: str) -> bytes:
    return asyncio.run(_build_export(job_id, format_name))


async def _build_export(job_id: int, format_name: str) -> bytes:
    from app.core.config import get_settings
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
    LocalSessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    service = ExportService()
    try:
        async with LocalSessionFactory() as session:
            rows = await service.build_rows(session, job_id)
            if format_name == "csv":
                return service.to_csv(rows)
            if format_name == "excel":
                return service.to_excel(rows)
            raise ValueError(f"Unsupported export format: {format_name}")
    finally:
        await engine.dispose()
