"""
Google Search Fetcher — fetches public Google SERP pages using httpx (no browser required),
extracts candidate business names + URLs from result snippets, and returns deduplicated candidates.

Rate limiting: asyncio.Semaphore + random jitter. No login bypass; pure public-page scraping.
If Google blocks (CAPTCHA/429), the fetcher skips that query and continues with others.
"""
from __future__ import annotations

import asyncio
import logging
import random
import re
from dataclasses import dataclass
from urllib.parse import quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Rotate user agents to reduce rate-limiting probability
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

# Domains to filter out from extracted URLs (aggregators, not actual businesses)
_SKIP_DOMAINS = frozenset({
    "google.com", "google.co.uk", "google.co.in",
    "linkedin.com", "facebook.com", "twitter.com", "instagram.com",
    "youtube.com", "wikipedia.org", "reddit.com",
    "yelp.com", "yellowpages.com", "trustpilot.com",
    "maps.google.com", "support.google.com",
    "amazon.com", "ebay.com",
})


@dataclass
class DiscoveredBusiness:
    name: str
    website: str | None
    profile_url: str | None
    source_platform: str
    description: str | None
    raw_title: str


class GoogleSearchFetcher:
    """
    Uses Google web search to discover business candidates from search result pages.
    """

    _TIMEOUT = httpx.Timeout(10.0, connect=5.0)
    _LIMITS = httpx.Limits(max_connections=10, max_keepalive_connections=5)
    # Semaphore: max 3 concurrent Google requests to avoid triggering rate limits
    _SEM = asyncio.Semaphore(3)

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self._TIMEOUT,
                limits=self._LIMITS,
                headers={"Accept-Language": "en-US,en;q=0.9"},
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def fetch_query(self, query: str, platform: str, num: int = 10) -> list[DiscoveredBusiness]:
        """Fetch one Google search query and return extracted business candidates."""
        url = f"https://www.google.com/search?q={quote_plus(query)}&num={num}&hl=en"
        ua = random.choice(_USER_AGENTS)

        async with self._SEM:
            # Random jitter 0.3–1.5s between requests — mimics human pacing
            await asyncio.sleep(random.uniform(0.3, 1.5))
            try:
                client = self._get_client()
                resp = await client.get(url, headers={"User-Agent": ua})

                if resp.status_code in (429, 503):
                    logger.warning("Google rate-limited for query: %s — skipping", query[:60])
                    return []
                if resp.status_code != 200:
                    logger.warning("Google returned %d for query: %s", resp.status_code, query[:60])
                    return []

                # Check for CAPTCHA page
                if "detected unusual traffic" in resp.text.lower() or "/sorry/" in str(resp.url):
                    logger.warning("Google CAPTCHA triggered — pausing this query: %s", query[:60])
                    return []

                return self._parse_results(resp.text, platform, query)

            except Exception as exc:
                logger.warning("Fetch failed for query '%s': %s", query[:60], exc)
                return []

    def _parse_results(self, html: str, platform: str, query: str) -> list[DiscoveredBusiness]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[DiscoveredBusiness] = []

        # Google search result containers
        for g in soup.select("div.g, div[data-sokoban-container]"):
            try:
                # Title
                title_el = g.select_one("h3")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 3:
                    continue

                # URL
                link_el = g.select_one("a[href]")
                raw_href = link_el["href"] if link_el else ""
                profile_url = self._clean_url(str(raw_href))
                if not profile_url:
                    continue

                # Description snippet
                snippet_el = g.select_one("div.VwiC3b, span.aCOpRe, div[data-sncf]")
                description = snippet_el.get_text(strip=True) if snippet_el else None

                # Determine if URL is a direct business website or a platform profile
                parsed = urlparse(profile_url)
                domain = parsed.netloc.replace("www.", "")
                is_business_site = domain not in _SKIP_DOMAINS

                website = profile_url if is_business_site else None
                company_name = self._extract_company_name(title, domain)

                results.append(DiscoveredBusiness(
                    name=company_name,
                    website=website,
                    profile_url=profile_url,
                    source_platform=platform,
                    description=description,
                    raw_title=title,
                ))
            except Exception:
                continue

        return results

    def _clean_url(self, href: str) -> str | None:
        """Strip Google's redirect wrapper and return the real URL."""
        if href.startswith("/url?q="):
            href = href[7:]
            if "&" in href:
                href = href.split("&")[0]
        if not href.startswith("http"):
            return None
        try:
            parsed = urlparse(href)
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
        except Exception:
            return None

    def _extract_company_name(self, title: str, domain: str) -> str:
        """
        Best-effort extract company name from the result title.
        Google titles are often "Company Name | Service | Location" or "Company Name - Description".
        """
        # Strip common suffixes after separator
        for sep in [" | ", " - ", " – ", " — ", " · "]:
            if sep in title:
                title = title.split(sep)[0].strip()
                break

        # If result is very short just use it as-is; otherwise fall back to domain
        name = title.strip()
        if len(name) < 2:
            name = domain.replace(".com", "").replace(".co.uk", "").replace("-", " ").title()
        return name[:255]

    async def fetch_all(
        self,
        queries: list[tuple[str, str]],  # list of (query_string, platform)
        max_results_per_query: int = 10,
    ) -> list[DiscoveredBusiness]:
        """Fetch all queries concurrently (respecting semaphore) and return merged results."""
        tasks = [self.fetch_query(q, p, max_results_per_query) for q, p in queries]
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)

        all_results: list[DiscoveredBusiness] = []
        for item in results_nested:
            if isinstance(item, list):
                all_results.extend(item)
        return all_results
