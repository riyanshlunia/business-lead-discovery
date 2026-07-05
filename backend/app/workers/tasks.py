from __future__ import annotations

import logging
from app.database.session import async_session_factory
from app.services.pipeline import LeadGenerationPipeline

logger = logging.getLogger(__name__)


async def run_lead_job_task(job_id: int) -> None:
    logger.info(f"Starting background lead generation job {job_id}")
    pipeline = LeadGenerationPipeline()
    try:
        async with async_session_factory() as session:
            await pipeline.run(session, job_id)
        logger.info(f"Successfully finished background lead generation job {job_id}")
    except Exception as e:
        logger.error(f"Error running lead generation job {job_id}: {e}", exc_info=True)
