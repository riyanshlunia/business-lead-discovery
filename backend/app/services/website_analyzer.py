from __future__ import annotations

import asyncio
import re
import time
from dataclasses import asdict, dataclass, field
from functools import partial
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


def _parse_html(html: str, base_url: str) -> dict:
    """CPU-bound HTML parsing — runs in a thread pool executor."""
    soup = BeautifulSoup(html, "html.parser")

    meta_title = None
    if soup.title and soup.title.text:
        stripped = soup.title.text.strip()
        meta_title = stripped or None

    meta_description = None
    description_tag = soup.find("meta", attrs={"name": re.compile("description", re.I)})
    if description_tag and description_tag.get("content"):
        meta_description = description_tag["content"].strip()

    image_count = len(soup.find_all("img"))
    form_count = len(soup.find_all("form"))
    mobile_viewport = bool(soup.find("meta", attrs={"name": re.compile("viewport", re.I)}))
    google_analytics = bool(re.search(r"googletagmanager|gtag\(|google-analytics", html, re.I))
    facebook_pixel = bool(re.search(r"facebook\.net/.*/fbevents\.js|fbq\(", html, re.I))

    urls: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.startswith("mailto:") or href.startswith("tel:"):
            urls.append(href)
            continue
        urls.append(urljoin(base_url, href))

    contact_page_found = any(
        "contact" in u.lower() or "about" in u.lower() for u in urls
    )

    return {
        "meta_title": meta_title,
        "meta_description": meta_description,
        "image_count": image_count,
        "form_count": form_count,
        "mobile_viewport": mobile_viewport,
        "google_analytics": google_analytics,
        "facebook_pixel": facebook_pixel,
        "urls": urls,
        "contact_page_found": contact_page_found,
    }


class WebsiteAnalyzer:
    # Shared client: connection pooling across all concurrent website fetches.
    _CLIENT_LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20)
    _TIMEOUT = httpx.Timeout(7.0, connect=3.0)
    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
    }

    def __init__(self, cache: InMemoryCache | None = None) -> None:
        self._cache = cache or InMemoryCache()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                follow_redirects=True,
                timeout=self._TIMEOUT,
                headers=self._HEADERS,
                limits=self._CLIENT_LIMITS,
            )
        return self._client

    async def close(self) -> None:
        """Close the shared client. Call when the analyzer is no longer needed."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def analyze(self, url: str) -> WebsiteAnalysisResult:
        normalized = self._normalize_url(url)
        cache_key = f"website-analysis:{normalized}"
        cached = await self._cache.get_json(cache_key)
        if cached:
            return WebsiteAnalysisResult(**cached)

        started = time.perf_counter()
        result = WebsiteAnalysisResult(url=normalized)
        client = await self._get_client()

        try:
            async with client.stream("GET", normalized) as response:
                result.final_url = str(response.url)
                result.https_enabled = response.url.scheme == "https"
                result.ssl_enabled = result.https_enabled
                base = result.final_url or normalized

                if response.status_code != 200:
                    await response.aread()
                    result.html = response.text
                    result.load_speed_ms = int((time.perf_counter() - started) * 1000)
                else:
                    content_type = response.headers.get("content-type", "").lower()
                    is_html = "text/html" in content_type or "xhtml" in content_type or not content_type
                    
                    if not is_html:
                        result.load_speed_ms = int((time.perf_counter() - started) * 1000)
                        result.html = ""
                    else:
                        chunks = []
                        bytes_read = 0
                        max_bytes = 256 * 1024
                        async for chunk in response.aiter_text():
                            chunks.append(chunk)
                            bytes_read += len(chunk.encode("utf-8", errors="ignore"))
                            if bytes_read >= max_bytes:
                                break
                        response_text = "".join(chunks)
                        result.load_speed_ms = int((time.perf_counter() - started) * 1000)
                        result.html = response_text

            if result.html:
                # Parse HTML in a thread pool to avoid blocking the event loop.
                # Use get_running_loop() — get_event_loop() is deprecated in Python 3.10+
                # and raises RuntimeError inside async context on Python 3.12.
                loop = asyncio.get_running_loop()
                parsed = await loop.run_in_executor(None, partial(_parse_html, result.html, base))
                result.meta_title = parsed["meta_title"]
                result.meta_description = parsed["meta_description"]
                result.image_count = parsed["image_count"]
                result.form_count = parsed["form_count"]
                result.mobile_viewport = parsed["mobile_viewport"]
                result.google_analytics = parsed["google_analytics"]
                result.facebook_pixel = parsed["facebook_pixel"]
                result.urls = parsed["urls"]
                result.contact_page_found = parsed["contact_page_found"]

            # Fetch robots.txt and sitemap.xml concurrently — fully independent.
            robots_url = urljoin(base, "/robots.txt")
            sitemap_url = urljoin(base, "/sitemap.xml")

            async def _check(check_url: str) -> bool:
                try:
                    r = await client.get(check_url)
                    return r.status_code == 200
                except Exception:
                    return False

            result.robots_txt, result.sitemap_xml = await asyncio.gather(
                _check(robots_url),
                _check(sitemap_url),
            )

        except Exception:
            await self._cache.set_json(cache_key, asdict(result), ttl_seconds=24 * 3600)
            return result

        await self._cache.set_json(cache_key, asdict(result), ttl_seconds=24 * 3600)
        return result

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url if "http" in url else f"https://{url}")
        return parsed.geturl()
