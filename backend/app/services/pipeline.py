from __future__ import annotations

import asyncio
from dataclasses import asdict

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import get_settings
from app.models.entities import Business, Email, Job, JobStatus, LeadScore, SocialAccount, Website
from app.services.contact_extractor import ContactExtractor
from app.services.job_service import JobService
from app.services.lead_scorer import LeadScorer
from app.services.maps_scraper import GoogleMapsScraper, MapBusinessCandidate
from app.services.website_analyzer import WebsiteAnalyzer

settings = get_settings()


class LeadGenerationPipeline:
    def __init__(self) -> None:
        self._job_service = JobService()
        self._maps_scraper = GoogleMapsScraper(headless=settings.playwright_headless)
        self._website_analyzer = WebsiteAnalyzer()
        self._contact_extractor = ContactExtractor()
        self._lead_scorer = LeadScorer()

    async def run(self, session: AsyncSession, job_id: int) -> None:
        job = await session.get(Job, job_id)
        if job is None:
            return
        await self._job_service.set_job_status(session, job_id, JobStatus.running)

        lock = asyncio.Lock()
        last_progress = job.progress or 0

        async def progress_callback(progress_val: int):
            nonlocal last_progress
            async with lock:
                if progress_val > last_progress:
                    last_progress = progress_val
                    job.progress = progress_val
                    await session.commit()

        try:
            candidates = await self._maps_scraper.discover_businesses(
                job.industry, job.location, job.target_limit, progress_callback
            )
            await self._persist_candidates(session, job, candidates)
            await self._job_service.set_job_status(session, job_id, JobStatus.completed)
        except Exception as exc:
            await self._fail_job(job_id, str(exc))
            raise

    async def _fail_job(self, job_id: int, error_message: str) -> None:
        from app.database.session import async_session_factory
        async with async_session_factory() as session:
            await self._job_service.set_job_status(session, job_id, JobStatus.failed, error_message=error_message)

    async def _persist_candidates(self, session: AsyncSession, job: Job, candidates: list[MapBusinessCandidate]) -> None:
        subset = candidates[: job.target_limit]

        # 1. Gather all unique websites to analyze
        websites_to_analyze = list(dict.fromkeys([c.website for c in subset if c.website]))

        # 2. Analyze + extract contacts concurrently with a semaphore limit.
        #    Contact extraction is pure CPU/regex work on already-downloaded HTML —
        #    no I/O, no session — so it's free to run inside the concurrent gather.
        #    NOTE: Do NOT touch the session inside analyze_with_sem — SQLAlchemy
        #    AsyncSession is NOT safe for concurrent access.
        sem = asyncio.Semaphore(settings.lead_concurrency)

        async def analyze_with_sem(url: str):
            async with sem:
                res = await self._website_analyzer.analyze(url)
                contacts = self._contact_extractor.extract(
                    (res.html or "") + "\n" + "\n".join(res.urls)
                )
                return url, res, contacts

        # return_exceptions=True prevents one bad URL from killing the entire job.
        analysis_results: dict[str, tuple] = {}
        try:
            if websites_to_analyze:
                raw = await asyncio.gather(
                    *[analyze_with_sem(url) for url in websites_to_analyze],
                    return_exceptions=True,
                )
                for item in raw:
                    if isinstance(item, Exception):
                        continue  # skip failed URLs gracefully
                    url, res, contacts = item
                    analysis_results[url] = (res, contacts)
        finally:
            # Release the shared httpx connection pool.
            await self._website_analyzer.close()

        # Single progress commit after all analysis is done (safe — sequential).
        job.progress = 80
        await session.commit()

        # 3. Persist everything sequentially (SQLAlchemy session writes must be sequential)
        for idx, candidate in enumerate(subset):
            business = await self._upsert_business(session, job.id, candidate)
            if candidate.website and candidate.website in analysis_results:
                website_result, contacts = analysis_results[candidate.website]
                await self._upsert_website(session, business.id, website_result.url, website_result)
                await self._upsert_contacts(session, business.id, contacts.emails, contacts.phones, contacts.whatsapp, contacts.social_links)
                # Merge website-extracted phone into business if Maps didn't find one
                if not business.phone_number and contacts.phones:
                    business.phone_number = contacts.phones[0]
                # Store all additional phones in raw_payload
                if contacts.phones:
                    business.raw_payload = {**(business.raw_payload or {}), "website_phones": contacts.phones}
                lead_score = self._lead_scorer.score(
                    website_exists=True,
                    ssl_enabled=website_result.ssl_enabled,
                    social_presence_count=sum(len(items) for items in contacts.social_links.values()),
                    contact_count=len(contacts.emails) + len(contacts.phones) + len(contacts.whatsapp),
                    seo_signals=int(bool(website_result.meta_title)) + int(bool(website_result.meta_description)),
                    performance_score=max(0, 100 - (website_result.load_speed_ms or 1000) // 20),
                    review_count=candidate.review_count,
                    rating=candidate.rating,
                )
            else:
                lead_score = self._lead_scorer.score(
                    website_exists=False,
                    ssl_enabled=False,
                    social_presence_count=0,
                    contact_count=1 if candidate.phone_number else 0,
                    seo_signals=0,
                    performance_score=0,
                    review_count=candidate.review_count,
                    rating=candidate.rating,
                )
            await self._upsert_lead_score(session, business.id, lead_score)

        # Single commit for all persisted businesses — N commits → 1 round-trip.
        job.progress = 100
        await session.commit()

    async def _upsert_business(self, session: AsyncSession, job_id: int, candidate: MapBusinessCandidate) -> Business:
        # Sanitize and truncate string fields to fit database column limits
        candidate.name = candidate.name[:255] if candidate.name else "Unknown"
        candidate.website = candidate.website[:1024] if candidate.website else None
        candidate.phone_number = candidate.phone_number[:64] if candidate.phone_number else None
        candidate.address = candidate.address[:10000] if candidate.address else None
        candidate.category = candidate.category[:255] if candidate.category else None
        candidate.google_maps_url = candidate.google_maps_url[:2048] if candidate.google_maps_url else ""
        candidate.business_status = candidate.business_status[:128] if candidate.business_status else None

        statement = select(Business).where(Business.google_maps_url == candidate.google_maps_url)
        result = await session.execute(statement)
        business = result.scalar_one_or_none()
        if business:
            business.job_id = job_id
            business.name = candidate.name
            business.website = candidate.website
            business.phone_number = candidate.phone_number
            business.address = candidate.address
            business.category = candidate.category
            business.rating = candidate.rating
            business.review_count = candidate.review_count
            business.latitude = candidate.latitude
            business.longitude = candidate.longitude
            business.business_status = candidate.business_status
            business.opening_hours = candidate.opening_hours
            business.raw_payload = candidate.raw_payload
        else:
            business = Business(job_id=job_id, **asdict(candidate))
            session.add(business)
        await session.flush()
        return business

    async def _upsert_website(self, session: AsyncSession, business_id: int, url: str, analysis) -> None:
        payload = asdict(analysis)
        payload.pop("html", None)
        payload.pop("urls", None)
        payload.pop("url", None)  # already passed explicitly
        stmt = (
            pg_insert(Website)
            .values(business_id=business_id, url=url, **payload)
            .on_conflict_do_update(
                index_elements=[Website.business_id],
                set_={"url": url, **payload},
            )
        )
        await session.execute(stmt)

    async def _upsert_contacts(
        self,
        session: AsyncSession,
        business_id: int,
        emails: list[str],
        phones: list[str],
        whatsapp: list[str],
        social_links: dict[str, list[str]],
    ) -> None:
        await session.execute(delete(Email).where(Email.business_id == business_id))
        await session.execute(delete(SocialAccount).where(SocialAccount.business_id == business_id))
        for index, email in enumerate(emails):
            session.add(Email(business_id=business_id, address=email, source="website", is_primary=index == 0))
        for platform, urls in social_links.items():
            for url in urls:
                session.add(SocialAccount(business_id=business_id, platform=platform, url=url, handle=None))
        for wa_url in whatsapp:
            session.add(SocialAccount(business_id=business_id, platform="whatsapp", url=wa_url, handle=None))
        await session.flush()

    async def _upsert_lead_score(self, session: AsyncSession, business_id: int, score) -> None:
        stmt = (
            pg_insert(LeadScore)
            .values(
                business_id=business_id,
                digital_presence_score=score.digital_presence_score,
                lead_opportunity_score=score.lead_opportunity_score,
                explanation=score.explanation,
            )
            .on_conflict_do_update(
                index_elements=[LeadScore.business_id],
                set_={
                    "digital_presence_score": score.digital_presence_score,
                    "lead_opportunity_score": score.lead_opportunity_score,
                    "explanation": score.explanation,
                },
            )
        )
        await session.execute(stmt)
