from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass, field
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.cache import InMemoryCache


@dataclass(slots=True)
class WebsiteAnalysisResult:
    url: str
    final_url: str | None = None
    ssl_enabled: bool = False
    https_enabled: bool = False
    meta_title: str | None = None
    meta_description: str | None = None
    image_count: int = 0
    contact_page_found: bool = False
    form_count: int = 0
    load_speed_ms: int | None = None
    mobile_viewport: bool = False
    google_analytics: bool = False
    facebook_pixel: bool = False
    robots_txt: bool = False
    sitemap_xml: bool = False
    html: str | None = None
    urls: list[str] = field(default_factory=list)


class WebsiteAnalyzer:
    def __init__(self, cache: InMemoryCache | None = None) -> None:
        self._cache = cache or InMemoryCache()

    async def analyze(self, url: str) -> WebsiteAnalysisResult:
        normalized = self._normalize_url(url)
        cache_key = f"website-analysis:{normalized}"
        cached = await self._cache.get_json(cache_key)
        if cached:
            return WebsiteAnalysisResult(**cached)

        started = time.perf_counter()
        timeout = httpx.Timeout(20.0, connect=10.0)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            )
        }
        result = WebsiteAnalysisResult(url=normalized)

        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout, headers=headers) as client:
            try:
                response = await client.get(normalized)
                result.final_url = str(response.url)
                result.https_enabled = response.url.scheme == "https"
                result.ssl_enabled = result.https_enabled
                result.load_speed_ms = int((time.perf_counter() - started) * 1000)

                soup = BeautifulSoup(response.text, "html.parser")
                result.html = response.text
                result.meta_title = self._text_or_none(soup.title.text if soup.title else None)
                description_tag = soup.find("meta", attrs={"name": re.compile("description", re.I)})
                if description_tag and description_tag.get("content"):
                    result.meta_description = description_tag["content"].strip()
                result.image_count = len(soup.find_all("img"))
                result.form_count = len(soup.find_all("form"))
                result.mobile_viewport = bool(soup.find("meta", attrs={"name": re.compile("viewport", re.I)}))
                result.google_analytics = bool(re.search(r"googletagmanager|gtag\(|google-analytics", response.text, re.I))
                result.facebook_pixel = bool(re.search(r"facebook\.net/.*/fbevents\.js|fbq\(", response.text, re.I))
                result.urls = self._collect_urls(soup, result.final_url or normalized)
                result.contact_page_found = any("contact" in candidate.lower() or "about" in candidate.lower() for candidate in result.urls)
            except (httpx.HTTPError, Exception):
                # If main page request fails, save empty result & return
                await self._cache.set_json(cache_key, asdict(result), ttl_seconds=24 * 3600)
                return result

            try:
                robots = await client.get(urljoin(result.final_url or normalized, "/robots.txt"))
                result.robots_txt = robots.status_code == 200
            except (httpx.HTTPError, Exception):
                result.robots_txt = False

            try:
                sitemap = await client.get(urljoin(result.final_url or normalized, "/sitemap.xml"))
                result.sitemap_xml = sitemap.status_code == 200
            except (httpx.HTTPError, Exception):
                result.sitemap_xml = False

        await self._cache.set_json(cache_key, asdict(result), ttl_seconds=24 * 3600)
        return result

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url if "http" in url else f"https://{url}")
        return parsed.geturl()

    def _collect_urls(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        urls: list[str] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            # Keep mailto: and tel: links — contact_extractor parses them
            if href.startswith("mailto:") or href.startswith("tel:"):
                urls.append(href)
                continue
            urls.append(urljoin(base_url, href))
        return urls

    def _text_or_none(self, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
