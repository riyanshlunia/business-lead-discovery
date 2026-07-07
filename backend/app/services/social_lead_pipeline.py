"""
Social Lead Pipeline — orchestrates the full Social Lead Finder pipeline:
1. Generate search queries (QueryEngine)
2. Fetch SERP results (GoogleSearchFetcher)
3. Deduplicate by domain
4. Enrich via WebsiteAnalyzer (reused)
5. Extract contacts via ContactExtractor (reused)
6. Score via LeadScorer (reused)
7. Persist to social_leads table
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.entities import JobStatus, SocialLead, SocialSearch
from app.services.contact_extractor import ContactExtractor
from app.services.google_search_fetcher import DiscoveredBusiness, GoogleSearchFetcher
from app.services.lead_scorer import LeadScorer
from app.services.query_engine import QueryEngine
from app.services.website_analyzer import WebsiteAnalyzer

logger = logging.getLogger(__name__)
settings = get_settings()


class SocialLeadPipeline:
    def __init__(self) -> None:
        self._query_engine = QueryEngine()
        self._fetcher = GoogleSearchFetcher()
        self._analyzer = WebsiteAnalyzer()
        self._extractor = ContactExtractor()
        self._scorer = LeadScorer()

    async def run(self, search_id: int) -> None:
        """
        Entry point — called from background task. Opens its own DB session.
        """
        from app.database.session import async_session_factory

        async with async_session_factory() as session:
            search = await session.get(SocialSearch, search_id)
            if not search:
                return

            # Mark running
            search.status = JobStatus.running
            search.started_at = datetime.now(timezone.utc)
            search.progress = 5
            await session.commit()

            try:
                await self._execute(session, search)
                search.status = JobStatus.completed
                search.finished_at = datetime.now(timezone.utc)
                search.progress = 100
            except Exception as exc:
                logger.exception("SocialLeadPipeline failed for search %d: %s", search_id, exc)
                search.status = JobStatus.failed
                search.error_message = str(exc)[:1000]
                search.finished_at = datetime.now(timezone.utc)

            await session.commit()

    async def _execute(self, session: AsyncSession, search: SocialSearch) -> None:
        # ── Step 1: Generate queries ──────────────────────────────────────────
        filters = search.filters or {}
        query_objs = self._query_engine.generate(
            industry=search.industry,
            location=search.location,
            keywords=search.keywords,
            sources=list(search.sources) if search.sources else None,
            services=filters.get("services"),
            tech_stack=filters.get("tech_stack"),
            company_size=filters.get("company_size"),
            limit=40,
        )
        search.query_summary = f"{len(query_objs)} queries generated"
        search.progress = 10
        await session.commit()

        # ── Step 2: Fetch SERPs ───────────────────────────────────────────────
        query_tuples = [(q.query, q.platform) for q in query_objs]
        candidates: list[DiscoveredBusiness] = await self._fetcher.fetch_all(
            query_tuples, max_results_per_query=10
        )
        logger.info("Social search %d: fetched %d raw candidates", search.id, len(candidates))

        search.progress = 40
        await session.commit()

        # ── Step 3: Deduplicate by domain ─────────────────────────────────────
        seen_domains: set[str] = set()
        unique: list[DiscoveredBusiness] = []
        for c in candidates:
            domain = self._domain(c.website or c.profile_url or "")
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                unique.append(c)
        # Also deduplicate by name (case-insensitive)
        seen_names: set[str] = set()
        deduped: list[DiscoveredBusiness] = []
        for c in unique:
            key = c.name.lower().strip()
            if key not in seen_names:
                seen_names.add(key)
                deduped.append(c)

        # Trim to target_limit
        subset = deduped[: search.target_limit]
        logger.info("Social search %d: %d unique candidates after dedup", search.id, len(subset))

        search.progress = 50
        await session.commit()

        # ── Step 4: Enrich websites concurrently ──────────────────────────────
        websites_to_analyze = list(dict.fromkeys([c.website for c in subset if c.website]))
        sem = asyncio.Semaphore(settings.lead_concurrency)

        async def analyze(url: str):
            async with sem:
                res = await self._analyzer.analyze(url)
                contacts = self._extractor.extract(
                    (res.html or "") + "\n" + "\n".join(res.urls)
                )
                return url, res, contacts

        analysis_results: dict[str, tuple] = {}
        if websites_to_analyze:
            raw = await asyncio.gather(
                *[analyze(u) for u in websites_to_analyze], return_exceptions=True
            )
            for item in raw:
                if isinstance(item, Exception):
                    continue
                url, res, contacts = item
                analysis_results[url] = (res, contacts)

        await self._analyzer.close()

        search.progress = 80
        await session.commit()

        # ── Step 5: Persist leads ─────────────────────────────────────────────
        persisted = 0
        for candidate in subset:
            website_result = None
            contacts = None

            if candidate.website and candidate.website in analysis_results:
                website_result, contacts = analysis_results[candidate.website]

            # Score
            score = self._scorer.score(
                website_exists=bool(candidate.website),
                ssl_enabled=bool(website_result and website_result.ssl_enabled),
                social_presence_count=sum(
                    len(v) for v in (contacts.social_links.values() if contacts else [])
                ) if contacts else 0,
                contact_count=(
                    len(contacts.emails) + len(contacts.phones) + len(contacts.whatsapp)
                ) if contacts else 0,
                seo_signals=(
                    int(bool(website_result.meta_title)) + int(bool(website_result.meta_description))
                ) if website_result else 0,
                performance_score=(
                    max(0, 100 - (website_result.load_speed_ms or 1000) // 20)
                ) if website_result else 0,
                review_count=None,
                rating=None,
            )

            # Confidence: based on how much data we got
            confidence = 30  # base for being found in search
            if candidate.website:
                confidence += 20
            if contacts and contacts.emails:
                confidence += 20
            if contacts and contacts.phones:
                confidence += 15
            if website_result and website_result.ssl_enabled:
                confidence += 10
            if candidate.description:
                confidence += 5

            lead = SocialLead(
                search_id=search.id,
                name=candidate.name[:255],
                source_platform=candidate.source_platform[:64],
                profile_url=(candidate.profile_url or "")[:2048] or None,
                website=(candidate.website or "")[:1024] or None,
                email=(contacts.emails[0] if contacts and contacts.emails else None),
                phone=(contacts.phones[0] if contacts and contacts.phones else None),
                linkedin=self._pick_social(contacts, "linkedin") if contacts else None,
                facebook=self._pick_social(contacts, "facebook") if contacts else None,
                instagram=self._pick_social(contacts, "instagram") if contacts else None,
                twitter=self._pick_social(contacts, "twitter") if contacts else None,
                github=self._pick_social(contacts, "github") if contacts else None,
                youtube=self._pick_social(contacts, "youtube") if contacts else None,
                industry=search.industry,
                description=(candidate.description or "")[:2000] or None,
                services=[],
                technologies=[],
                confidence_score=min(100, confidence),
                lead_score=score.lead_opportunity_score,
                digital_score=score.digital_presence_score,
                has_website=bool(candidate.website),
                has_ssl=bool(website_result and website_result.ssl_enabled),
                has_email=bool(contacts and contacts.emails),
                has_phone=bool(contacts and contacts.phones),
                raw_payload={
                    "raw_title": candidate.raw_title,
                    "profile_url": candidate.profile_url,
                },
            )
            session.add(lead)
            persisted += 1

        search.total_found = persisted
        search.progress = 95
        await session.commit()

    @staticmethod
    def _domain(url: str) -> str:
        try:
            return urlparse(url).netloc.replace("www.", "").lower()
        except Exception:
            return ""

    @staticmethod
    def _pick_social(contacts, platform: str) -> str | None:
        if not contacts or not contacts.social_links:
            return None
        urls = contacts.social_links.get(platform, [])
        return urls[0][:1024] if urls else None
