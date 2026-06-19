"""
website_finder.py
-----------------
Discovers and validates official business websites using:
  1. OSM-provided URLs (confidence-scored, not blindly trusted)
  2. Multi-query DuckDuckGo search (15–20 results per query)
  3. Multi-signal validation (name, address, phone, email, meta, logo, schema)
  4. Alternate domain retries (.com / .in / .co.in)
  5. Optional Playwright render for JS-heavy sites

WebsiteChecker is NOT modified — this module only returns the best verified URL.
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass

from src.scraper.website_validator import (
    ACCEPT_THRESHOLD,
    MAYBE_THRESHOLD,
    ValidationResult,
    alternate_domain_urls,
    base_domain,
    log_rejection,
    validate_candidate,
)

logger = logging.getLogger(__name__)

# ── Aggregator / directory domains — skip but NEVER stop searching ────────────
SKIP_DOMAINS = {
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "linkedin.com", "youtube.com", "tiktok.com", "snapchat.com",
    "google.com", "maps.google.com", "maps.apple.com",
    "tripadvisor.com", "tripadvisor.in", "tripadvisor.co.uk",
    "justdial.com", "indiamart.com", "tradeindia.com",
    "zomato.com", "swiggy.com", "dineout.co.in",
    "yelp.com", "foursquare.com",
    "openstreetmap.org", "wikipedia.org", "wikimedia.org",
    "amazon.com", "amazon.in", "flipkart.com",
    "makemytrip.com", "goibibo.com", "booking.com",
    "bing.com", "yahoo.com", "reddit.com", "quora.com",
    "sulekha.com", "yellowpages.in", "trustpilot.com",
    "hotels.com", "expedia.com", "airbnb.com", "agoda.com",
    "trivago.com", "kayak.com", "priceline.com",
    "lonelyplanet.com", "holidayiq.com", "holidify.com",
    "cleartrip.com", "easeMytrip.com", "easemytrip.com",
    "oyo.com", "treebo.com", "fabhotels.com",
    "glassdoor.com", "indeed.com", "naukri.com",
    "bbc.com", "cnn.com", "ndtv.com", "timesofindia.com",
}

SEARCH_RESULTS_PER_QUERY = 20

DISCOVERY_FIELD_DEFAULTS = {
    "Discovery Method": "",
    "Confidence Score": "",
    "Validation Signals": "",
    "Search Query Used": "",
    "Discovery Status": "No Official Website Found",
}


@dataclass
class FindResult:
    website_url: str | None
    discovery_method: str
    confidence_score: float
    validation_signals: str
    search_query_used: str
    final_status: str


def _is_allowed_domain(url: str) -> bool:
    domain = base_domain(url)
    if not domain:
        return False
    for skip in SKIP_DOMAINS:
        if domain == skip or domain.endswith("." + skip):
            return False
    return True


def _generate_search_queries(
    business_name: str,
    location: str,
    record_location: str,
    phone: str = "",
) -> list[str]:
    """Progressively broader search queries."""
    name = business_name.strip()
    city = location.strip()
    addr = record_location.strip()

    queries = [
        f'"{name}" {city} official website',
        f"{name} {city}",
        f'"{name}" {city}',
        f"{name} official website",
        f"{name} contact",
        f"{name} address",
        f"{name} {city} hotel website",
        f"{name} official site",
    ]

    if addr and addr.lower() != city.lower():
        queries.append(f"{name} {addr}")
        # Locality = middle segment of comma-separated address
        parts = [p.strip() for p in addr.split(",") if p.strip()]
        if len(parts) >= 2:
            queries.append(f"{name} {parts[0]} {city}")
            queries.append(f"{name} {parts[-1]}")

    if phone:
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 10:
            queries.append(f"{name} {digits[-10:]}")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        key = q.lower()
        if key not in seen:
            seen.add(key)
            unique.append(q)
    return unique


def _status_label(confidence: float) -> str:
    if confidence >= ACCEPT_THRESHOLD:
        return "Official Website Found"
    if confidence >= MAYBE_THRESHOLD:
        return "Official Website Found (Moderate Confidence)"
    return "No Official Website Found"


def _format_signals(result: ValidationResult) -> str:
    if not result.signals_matched:
        return ""
    return ", ".join(f"✓ {s}" for s in result.signals_matched)


class WebsiteFinder:
    """
    Finds official business websites via OSM tags and multi-query DuckDuckGo search.
    Every candidate is scored with multi-signal confidence validation.
    """

    def __init__(self, delay: float = 1.2, debug: bool | None = None):
        self.delay = delay
        self._last_call = 0.0
        if debug is None:
            debug = os.getenv("WEBSITE_FINDER_DEBUG", "").lower() in ("1", "true", "yes")
        self.debug = debug

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_call = time.time()

    def _search_ddg(self, query: str) -> list[str]:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.warning("duckduckgo-search not installed; skipping website lookup.")
            return []

        self._throttle()
        try:
            logger.info("Calling DuckDuckGo search for query: %s", query)
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=SEARCH_RESULTS_PER_QUERY))
            logger.info("Returned from DuckDuckGo search for query: %s", query)
        except Exception as exc:
            logger.warning("DuckDuckGo search failed for '%s': %s", query, exc)
            return []

        urls: list[str] = []
        for r in results:
            href = r.get("href", "")
            if href and _is_allowed_domain(href):
                urls.append(href)
        return urls

    def _evaluate_url(
        self,
        url: str,
        business_name: str,
        search_location: str,
        record_location: str,
        phone: str,
        email: str,
    ) -> ValidationResult:
        return validate_candidate(
            url=url,
            business_name=business_name,
            location=record_location,
            search_location=search_location,
            osm_phone=phone,
            osm_email=email,
        )

    def _validate_osm_url(self, record: dict, search_location: str) -> FindResult | None:
        url = record.get("Website URL")
        if not url or str(url).strip() in ("", "nan", "None"):
            return None

        url = str(url).strip()
        if not url.startswith("http"):
            url = "https://" + url
        if not _is_allowed_domain(url):
            return None

        name = record.get("Business Name", "")
        result = self._evaluate_url(
            url, name, search_location,
            record.get("Location", search_location),
            record.get("Phone Number", ""),
            record.get("Email Address", ""),
        )
        log_rejection(url, result, self.debug)

        if result.is_acceptable:
            return FindResult(
                website_url=result.url,
                discovery_method="OSM Tag",
                confidence_score=result.confidence,
                validation_signals=_format_signals(result),
                search_query_used="",
                final_status=_status_label(result.confidence),
            )
        return None

    def find(self, record: dict, search_location: str) -> FindResult:
        """
        Discover the best official website for a business record.
        Returns FindResult with metadata even when no website is found.
        """
        name = record.get("Business Name", "")
        location = record.get("Location", search_location)
        phone = record.get("Phone Number", "")
        email = record.get("Email Address", "")

        if not name or name.strip() in ("", "Unknown Business"):
            return FindResult(None, "", 0.0, "", "", "No Official Website Found")

        # ── Try existing OSM URL first ────────────────────────────────────
        osm_result = self._validate_osm_url(record, search_location)
        if osm_result and osm_result.confidence_score >= ACCEPT_THRESHOLD:
            return osm_result

        best: ValidationResult | None = None
        best_method = ""
        best_query = ""

        if osm_result:
            best = ValidationResult(
                url=osm_result.website_url or "",
                confidence=osm_result.confidence_score,
                signal_scores={},
                signals_matched=[s.strip("✓ ") for s in osm_result.validation_signals.split(",") if s],
                rejection_reasons=[],
                status="moderate" if osm_result.confidence_score < ACCEPT_THRESHOLD else "accepted",
            )
            best_method = "OSM Tag"
            best_query = ""

        # ── Multi-query DuckDuckGo search ─────────────────────────────────
        queries = _generate_search_queries(name, search_location, location, phone)
        seen_urls: set[str] = set()

        for q_idx, query in enumerate(queries, start=1):
            if best and best.confidence >= ACCEPT_THRESHOLD:
                break

            candidate_urls = self._search_ddg(query)
            if self.debug:
                print(f"  [Query #{q_idx}] '{query}' → {len(candidate_urls)} candidates")

            for href in candidate_urls:
                domain = base_domain(href)
                if domain in seen_urls:
                    continue
                seen_urls.add(domain)

                urls_to_try = [href] + alternate_domain_urls(href)

                for try_url in urls_to_try:
                    try_domain = base_domain(try_url)
                    if try_domain in seen_urls and try_url != href:
                        continue
                    seen_urls.add(try_domain)

                    result = self._evaluate_url(
                        try_url, name, search_location, location, phone, email
                    )
                    log_rejection(try_url, result, self.debug)

                    method = (
                        f"DuckDuckGo Search #{q_idx}"
                        if try_url == href
                        else "Alternate Domain"
                    )

                    if best is None or result.confidence > best.confidence:
                        best = result
                        best_method = method
                        best_query = query

                    if result.confidence >= ACCEPT_THRESHOLD:
                        break

                if best and best.confidence >= ACCEPT_THRESHOLD:
                    break

        if best and best.is_acceptable:
            return FindResult(
                website_url=best.url,
                discovery_method=best_method or "DuckDuckGo Search",
                confidence_score=best.confidence,
                validation_signals=_format_signals(best),
                search_query_used=best_query,
                final_status=_status_label(best.confidence),
            )

        # Return best attempt metadata even on failure (aids debugging)
        fail_conf = best.confidence if best else 0.0
        if self.debug and best:
            print(f"  ✗ No acceptable website for '{name}' (best: {fail_conf:.0f}%)")

        return FindResult(
            website_url=None,
            discovery_method=best_method,
            confidence_score=fail_conf,
            validation_signals=_format_signals(best) if best else "",
            search_query_used=best_query,
            final_status="No Official Website Found",
        )

    def _apply_discovery_fields(self, record: dict, result: FindResult) -> None:
        record["Website URL"] = result.website_url
        record["Discovery Method"] = result.discovery_method
        record["Confidence Score"] = str(int(result.confidence_score)) if result.confidence_score else ""
        record["Validation Signals"] = result.validation_signals
        record["Search Query Used"] = result.search_query_used
        record["Discovery Status"] = result.final_status

    def enrich_records(self, records: list[dict], location: str) -> list[dict]:
        """
        For every record, discover/validate website and attach discovery metadata.
        """
        for record in records:
            for k, v in DISCOVERY_FIELD_DEFAULTS.items():
                record.setdefault(k, v)

        to_process = [r for r in records if r.get("Business Name")]
        found_count = 0

        if to_process:
            print(f"[WebsiteFinder] Processing {len(to_process)} businesses...")
            for record in to_process:
                name = record.get("Business Name", "")
                result = self.find(record, location)
                self._apply_discovery_fields(record, result)

                if result.website_url:
                    found_count += 1
                    print(
                        f"  ✓ {name}: {result.website_url} "
                        f"({result.confidence_score:.0f}% — {result.discovery_method})"
                    )
                else:
                    print(f"  – {name}: not found (best confidence: {result.confidence_score:.0f}%)")

            print(f"[WebsiteFinder] Found {found_count}/{len(to_process)} official websites.")

        return records


# Backward-compatible helper for external imports
def validate_osm_website(url: str, business_name: str) -> str | None:
    """Legacy wrapper — uses confidence scoring instead of strict title/domain checks."""
    if not url or str(url).strip() in ("", "nan", "None"):
        return None
    finder = WebsiteFinder(debug=False)
    record = {"Business Name": business_name, "Website URL": url, "Location": ""}
    result = finder._validate_osm_url(record, "")
    return result.website_url if result else None
