import asyncio
import pytest
from unittest.mock import AsyncMock
from app.services.pipeline import LeadGenerationPipeline
from app.models.entities import Job


@pytest.mark.asyncio
async def test_pipeline_progress_callback_concurrency() -> None:
    pipeline = LeadGenerationPipeline()
    
    # Mock session and job
    session = AsyncMock()
    job = Job(id=1, progress=0)
    session.get = AsyncMock(return_value=job)
    
    # Mock dependencies
    pipeline._job_service = AsyncMock()
    pipeline._persist_candidates = AsyncMock()
    
    # Capture the progress callback and call it concurrently
    async def mock_discover(industry, location, target_limit, progress_cb):
        if progress_cb:
            # Send progress updates concurrently
            await asyncio.gather(
                progress_cb(10),
                progress_cb(12),
                progress_cb(15),
                progress_cb(8),
            )
        return []
        
    pipeline._maps_scraper.discover_businesses = mock_discover
    
    # We want to check that session.commit() was called and never concurrently.
    # Because of `progress_val > last_progress`, and the inputs 10, 12, 15, 8:
    # 10 is > 0 -> commits.
    # 12 is > 10 -> commits.
    # 15 is > 12 -> commits.
    # 8 is < 15 -> does not commit.
    # So we expect exactly 3 commits from the progress callbacks.
    
    commit_calls = 0
    concurrent_calls = 0
    lock = asyncio.Lock()
    
    async def mock_commit():
        nonlocal commit_calls, concurrent_calls
        async with lock:
            concurrent_calls += 1
            if concurrent_calls > 1:
                pytest.fail("Concurrent commit detected!")
        await asyncio.sleep(0.01)  # simulate I/O
        async with lock:
            concurrent_calls -= 1
            commit_calls += 1

    session.commit = mock_commit
    
    await pipeline.run(session, 1)
    
    assert commit_calls == 3
