"""
Multi-signal website validation with confidence scoring.

Used by WebsiteFinder to decide whether a candidate URL belongs to a business.
WebsiteChecker is NOT modified — this module only discovers/validates URLs.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Confidence weights (must sum to 1.0) ─────────────────────────────────────
SIGNAL_WEIGHTS = {
    "name": 0.35,
    "address": 0.20,
    "phone": 0.20,
    "email": 0.10,
    "meta": 0.05,
    "logo": 0.05,
    "structured": 0.05,
}

ACCEPT_THRESHOLD = 80
MAYBE_THRESHOLD = 60
THIN_CONTENT_CHARS = 400
FETCH_TIMEOUT = 10
PLAYWRIGHT_TIMEOUT_MS = 15000

_REQ_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_GENERIC_STOP = {
    "the", "and", "for", "inn", "ltd", "pvt", "llc", "inc", "co",
    "hotel", "hotels", "resort", "resorts", "restaurant", "restaurants",
    "cafe", "cafes", "bar", "bars", "spa", "spas", "suites", "suite",
    "palace", "grand", "royal", "plaza", "club", "rooms",
    "guest", "house", "lodge", "lodging", "stay", "stays",
    "de", "la", "le", "of", "at", "by",
}


@dataclass
class PageSnapshot:
    final_url: str
    html: str
    title: str
    meta_description: str
    visible_text: str
    logo_alts: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    structured: list[dict[str, Any]] = field(default_factory=list)
    rendered_with_js: bool = False


@dataclass
class ValidationResult:
    url: str
    confidence: float
    signal_scores: dict[str, float]
    signals_matched: list[str]
    rejection_reasons: list[str]
    status: str  # accepted | moderate | rejected
    rendered_with_js: bool = False

    @property
    def is_acceptable(self) -> bool:
        return self.confidence >= MAYBE_THRESHOLD


# ── Text / token helpers ──────────────────────────────────────────────────────

def meaningful_tokens(name: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+", name.lower())
    return [w for w in words if len(w) >= 3 and w not in _GENERIC_STOP]


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def extract_phones(text: str) -> list[str]:
    patterns = [
        r"\+?\d[\d\s\-().]{8,}\d",
        r"\b\d{10}\b",
        r"\b\d{3}[\s\-]?\d{3}[\s\-]?\d{4}\b",
    ]
    found: set[str] = set()
    for pat in patterns:
        for m in re.finditer(pat, text):
            norm = normalize_phone(m.group())
            if len(norm) >= 10:
                found.add(norm)
    return list(found)


def extract_emails(text: str) -> list[str]:
    return list({m.lower() for m in re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)})


def parse_address_parts(location: str, search_location: str) -> dict[str, str]:
    loc = (location or "").strip()
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    postcode_m = re.search(r"\b\d{5,6}\b", loc)

    city = search_location.strip().lower()
    found_city = False
    for part in reversed(parts):
        if search_location.lower() in part.lower() or part.lower() in search_location.lower():
            city = part.lower()
            found_city = True
            break
    if not found_city and parts:
        city = parts[-1].lower()

    street = parts[0].lower() if parts else ""
    locality = parts[1].lower() if len(parts) > 2 else (parts[-1].lower() if len(parts) > 1 else "")

    return {
        "city": city,
        "locality": locality,
        "street": street,
        "postcode": postcode_m.group() if postcode_m else "",
        "full": loc.lower(),
    }


def fuzzy_token_score(tokens: list[str], text: str) -> float:
    if not tokens or not text:
        return 0.0
    text_l = text.lower()
    matched = sum(1 for t in tokens if t in text_l)
    overlap = (matched / len(tokens)) * 100

    best_seq = 0.0
    for chunk in re.split(r"[|\-–—•]", text_l):
        chunk = chunk.strip()
        if len(chunk) < 3:
            continue
        for t in tokens:
            best_seq = max(best_seq, SequenceMatcher(None, t, chunk).ratio())

    return min(100.0, max(overlap, best_seq * 100))


def base_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return re.sub(r"^www\.", "", host)
    except Exception:
        return ""


def alternate_domain_urls(url: str) -> list[str]:
    """Generate .com / .in / .co.in variants for the same domain stem."""
    domain = base_domain(url)
    if not domain:
        return []
    stem = domain.split(".")[0]
    if len(stem) < 3:
        return []
    variants: list[str] = []
    for tld in ("com", "in", "co.in", "net", "org"):
        for prefix in ("", "www."):
            variants.append(f"https://{prefix}{stem}.{tld}")
    seen: set[str] = set()
    out: list[str] = []
    for v in variants:
        if v not in seen and base_domain(v) != domain:
            seen.add(v)
            out.append(v)
    return out


# ── Page fetching & parsing ───────────────────────────────────────────────────

def _fetch_html_requests(url: str) -> tuple[str, str] | None:
    if not url.startswith("http"):
        url = "https://" + url
    try:
        logger.info("Calling website HTTP fetch for %s", url)
        resp = requests.get(
            url, headers=_REQ_HEADERS, timeout=FETCH_TIMEOUT, allow_redirects=True
        )
        logger.info("Returned from website HTTP fetch for %s", url)
        if resp.status_code >= 400:
            return None
        return resp.url, resp.text
    except requests.RequestException as exc:
        logger.debug("HTTP fetch failed for %s: %s", url, exc)
        return None


def _fetch_html_playwright(url: str) -> tuple[str, str] | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.debug("Playwright not installed; skipping JS render for %s", url)
        return None

    if not url.startswith("http"):
        url = "https://" + url

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            logger.info("Calling Playwright page.goto for %s", url)
            page.goto(url, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT_MS)
            logger.info("Returned from Playwright page.goto for %s", url)
            final_url = page.url
            html = page.content()
            browser.close()
            return final_url, html
    except Exception as exc:
        logger.debug("Playwright render failed for %s: %s", url, exc)
        return None


def _visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True))


def _parse_json_ld(soup: BeautifulSoup) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            raw = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(raw, list):
            items.extend(x for x in raw if isinstance(x, dict))
        elif isinstance(raw, dict):
            items.append(raw)
            if "@graph" in raw and isinstance(raw["@graph"], list):
                items.extend(x for x in raw["@graph"] if isinstance(x, dict))
    return items


def _flatten_structured(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    relevant_types = {
        "organization", "localbusiness", "hotel", "lodgingbusiness",
        "restaurant", "foodestablishment", "store",
    }
    out: list[dict[str, Any]] = []
    for item in items:
        t = item.get("@type", "")
        types = [t.lower()] if isinstance(t, str) else [x.lower() for x in t if isinstance(x, str)]
        if any(any(rt in ty for rt in relevant_types) for ty in types):
            out.append(item)
    return out


def build_snapshot(final_url: str, html: str, rendered_with_js: bool = False) -> PageSnapshot:
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    meta_desc = ""
    meta = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if meta and meta.get("content"):
        meta_desc = meta["content"].strip()
    if not meta_desc:
        og = soup.find("meta", property="og:description")
        if og and og.get("content"):
            meta_desc = og["content"].strip()

    visible = _visible_text(soup)
    logo_alts: list[str] = []
    for img in soup.find_all("img"):
        alt = (img.get("alt") or "").strip()
        src = (img.get("src") or "").lower()
        cls = " ".join(img.get("class") or []).lower()
        if alt and ("logo" in alt.lower() or "logo" in src or "logo" in cls):
            logo_alts.append(alt)

    structured_raw = _parse_json_ld(soup)
    structured = _flatten_structured(structured_raw)

    phones = extract_phones(visible)
    emails = extract_emails(visible)

    for sd in structured:
        if tel := sd.get("telephone"):
            phones.extend(extract_phones(str(tel)))
        if email := sd.get("email"):
            emails.extend(extract_emails(str(email)))

    return PageSnapshot(
        final_url=final_url,
        html=html,
        title=title,
        meta_description=meta_desc,
        visible_text=visible,
        logo_alts=logo_alts,
        phones=list(set(phones)),
        emails=list(set(emails)),
        structured=structured,
        rendered_with_js=rendered_with_js,
    )


def fetch_page_snapshot(url: str) -> PageSnapshot | None:
    """Fetch page via HTTP; retry with Playwright if content is too thin."""
    result = _fetch_html_requests(url)
    if not result:
        return None

    final_url, html = result
    snap = build_snapshot(final_url, html)

    if len(snap.visible_text) < THIN_CONTENT_CHARS:
        js_result = _fetch_html_playwright(final_url)
        if js_result:
            final_url, html = js_result
            snap = build_snapshot(final_url, html, rendered_with_js=True)

    return snap


# ── Signal scoring ────────────────────────────────────────────────────────────

def _score_name(business_name: str, snap: PageSnapshot) -> tuple[float, list[str]]:
    tokens = meaningful_tokens(business_name)
    if not tokens:
        return 0.0, []

    haystacks = [snap.title, snap.meta_description, snap.visible_text[:20000]]
    haystacks.extend(snap.logo_alts)
    for sd in snap.structured:
        if n := sd.get("name"):
            haystacks.append(str(n))

    scores = [fuzzy_token_score(tokens, h) for h in haystacks if h]
    best = max(scores) if scores else 0.0

    combined = " ".join(haystacks).lower()
    if business_name.lower() in combined:
        best = min(100.0, best + 12)

    matched: list[str] = []
    if best >= 40:
        matched.append("Business Name")
    if snap.meta_description and fuzzy_token_score(tokens, snap.meta_description) >= 40:
        matched.append("Meta Description")
    if any(t in snap.visible_text.lower() for t in tokens):
        matched.append("Page Content")
    footer_chunk = snap.visible_text[-3000:].lower()
    if any(t in footer_chunk for t in tokens):
        matched.append("Footer")

    return best, matched


def _score_address(addr: dict[str, str], snap: PageSnapshot) -> tuple[float, list[str]]:
    text = snap.visible_text.lower()
    points = 0.0
    matched: list[str] = []
    checks = [
        ("city", 35, "City"),
        ("locality", 25, "Locality"),
        ("street", 25, "Street"),
        ("postcode", 15, "Postcode"),
    ]
    for key, weight, label in checks:
        val = addr.get(key, "")
        if val and len(val) >= 3 and val in text:
            points += weight
            matched.append(label)

    for sd in snap.structured:
        sd_addr = sd.get("address")
        if isinstance(sd_addr, dict):
            sd_text = json.dumps(sd_addr).lower()
            if addr.get("city") and addr["city"] in sd_text:
                points = min(100.0, points + 20)
                if "City" not in matched:
                    matched.append("City")

    return min(100.0, points), matched


def _score_phone(osm_phone: str, snap: PageSnapshot) -> tuple[float, list[str]]:
    osm_norm = normalize_phone(osm_phone)
    if not osm_norm:
        return 0.0, []
    for p in snap.phones:
        if p == osm_norm or p.endswith(osm_norm) or osm_norm.endswith(p):
            return 100.0, ["Phone"]
    if osm_norm in re.sub(r"\D", "", snap.visible_text):
        return 90.0, ["Phone"]
    return 0.0, []


def _score_email(osm_email: str, snap: PageSnapshot, url: str) -> tuple[float, list[str]]:
    domain = base_domain(url)
    matched: list[str] = []
    score = 0.0

    if osm_email:
        osm_email = osm_email.lower().strip()
        if osm_email in snap.emails:
            return 100.0, ["Email"]
        if domain and osm_email.split("@")[-1] == domain:
            return 95.0, ["Email Domain"]

    for em in snap.emails:
        em_domain = em.split("@")[-1]
        if domain and (em_domain == domain or domain.endswith("." + em_domain)):
            score = max(score, 80.0)
            matched.append("Email Domain")

    tokens = meaningful_tokens(osm_email.split("@")[0] if osm_email and "@" in osm_email else "")
    if tokens and any(t in snap.visible_text.lower() for t in tokens):
        score = max(score, 60.0)

    return score, matched


def _score_logo(business_name: str, snap: PageSnapshot) -> tuple[float, list[str]]:
    tokens = meaningful_tokens(business_name)
    if not tokens or not snap.logo_alts:
        return 0.0, []
    for alt in snap.logo_alts:
        if fuzzy_token_score(tokens, alt) >= 50:
            return 100.0, ["Logo"]
    return 0.0, []


def _score_structured(business_name: str, snap: PageSnapshot) -> tuple[float, list[str]]:
    if not snap.structured:
        return 0.0, []
    tokens = meaningful_tokens(business_name)
    for sd in snap.structured:
        name = str(sd.get("name", ""))
        if tokens and fuzzy_token_score(tokens, name) >= 50:
            return 100.0, ["Structured Data"]
        if sd.get("telephone") or sd.get("address"):
            return 70.0, ["Structured Data"]
    return 0.0, []


def validate_candidate(
    url: str,
    business_name: str,
    location: str,
    search_location: str,
    osm_phone: str = "",
    osm_email: str = "",
    snapshot: PageSnapshot | None = None,
) -> ValidationResult:
    """Score a URL against business record signals. Returns confidence 0–100."""
    rejection_reasons: list[str] = []
    signals_matched: list[str] = []

    snap = snapshot or fetch_page_snapshot(url)
    if not snap:
        return ValidationResult(
            url=url,
            confidence=0.0,
            signal_scores={},
            signals_matched=[],
            rejection_reasons=["Could not fetch page"],
            status="rejected",
        )

    final_url = snap.final_url
    addr = parse_address_parts(location, search_location)

    name_score, name_signals = _score_name(business_name, snap)
    addr_score, addr_signals = _score_address(addr, snap)
    phone_score, phone_signals = _score_phone(osm_phone, snap)
    email_score, email_signals = _score_email(osm_email, snap, final_url)
    meta_score = fuzzy_token_score(meaningful_tokens(business_name), snap.meta_description)
    logo_score, logo_signals = _score_logo(business_name, snap)
    struct_score, struct_signals = _score_structured(business_name, snap)

    signal_scores = {
        "name": name_score,
        "address": addr_score,
        "phone": phone_score,
        "email": email_score,
        "meta": meta_score,
        "logo": logo_score,
        "structured": struct_score,
    }

    confidence = sum(signal_scores[k] * SIGNAL_WEIGHTS[k] for k in SIGNAL_WEIGHTS)

    for group in (name_signals, addr_signals, phone_signals, email_signals, logo_signals, struct_signals):
        for s in group:
            if s not in signals_matched:
                signals_matched.append(s)

    if name_score < 40:
        rejection_reasons.append(f"Business name similarity: {name_score:.0f}%")
    if addr_score < 20 and addr.get("city"):
        rejection_reasons.append("Address/city mismatch")
    if osm_phone and phone_score == 0:
        rejection_reasons.append("Phone not found on page")
    if confidence < MAYBE_THRESHOLD:
        rejection_reasons.append(f"Final confidence: {confidence:.0f}%")

    if confidence >= ACCEPT_THRESHOLD:
        status = "accepted"
    elif confidence >= MAYBE_THRESHOLD:
        status = "moderate"
    else:
        status = "rejected"

    return ValidationResult(
        url=final_url,
        confidence=round(confidence, 1),
        signal_scores={k: round(v, 1) for k, v in signal_scores.items()},
        signals_matched=signals_matched,
        rejection_reasons=rejection_reasons,
        status=status,
        rendered_with_js=snap.rendered_with_js,
    )


def log_rejection(url: str, result: ValidationResult, debug: bool = False) -> None:
    if not debug and result.status != "rejected":
        return
    lines = [f"Candidate: {url}"]
    if result.status == "rejected":
        lines.append("Rejected because:")
    else:
        lines.append(f"Accepted ({result.status}):")
    for key, val in result.signal_scores.items():
        lines.append(f"  {key}: {val}%")
    for reason in result.rejection_reasons:
        lines.append(f"  {reason}")
    lines.append(f"  Signals matched: {', '.join(result.signals_matched) or 'none'}")
    logger.debug("\n".join(lines))
    if debug and result.status == "rejected":
        print("\n".join(lines))
