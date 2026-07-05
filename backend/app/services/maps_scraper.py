from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import quote_plus

from playwright.async_api import Page, async_playwright


@dataclass(slots=True)
class MapBusinessCandidate:
    name: str
    google_maps_url: str
    website: str | None = None
    phone_number: str | None = None
    address: str | None = None
    category: str | None = None
    rating: float | None = None
    review_count: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    business_status: str | None = None
    opening_hours: str | None = None
    raw_payload: dict = field(default_factory=dict)


class CaptchaDetectedError(RuntimeError):
    pass


class GoogleMapsScraper:
    def __init__(self, headless: bool = True) -> None:
        self._headless = headless

    async def discover_businesses(self, industry: str, location: str, limit: int = 100, progress_callback = None) -> list[MapBusinessCandidate]:
        query = f"{industry} in {location}"
        search_url = f"https://www.google.com/maps/search/{quote_plus(query)}"
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self._headless)
            context = await browser.new_context(viewport={"width": 1440, "height": 1100})
            page = await context.new_page()
            try:
                if progress_callback:
                    await progress_callback(5)
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await self._dismiss_cookie_banner(page)
                self._assert_no_captcha(await page.content())
                await page.wait_for_timeout(4000)
                if progress_callback:
                    await progress_callback(10)
                candidates = await self._collect_cards(page, limit)
                if progress_callback:
                    await progress_callback(20)
                await self._enrich_candidates(page, candidates, progress_callback)
                return candidates
            finally:
                await context.close()
                await browser.close()

    async def _enrich_candidates(self, page: Page, candidates: list[MapBusinessCandidate], progress_callback = None) -> None:
        for idx, candidate in enumerate(candidates):
            try:
                # Navigate directly to the business URL — avoids the virtual-scroll
                # problem where off-screen card DOM nodes are removed by Google Maps.
                await page.goto(candidate.google_maps_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2500)
                self._assert_no_captcha(await page.content())

                panel = page.locator('div[role="main"]').first
                if await panel.count() == 0:
                    panel = page.locator('div[class*="m6QErb"], div[class*="widget-pane"]').first
                if await panel.count() == 0:
                    continue

                panel_text = await panel.inner_text()
                candidate.raw_payload["panel_text"] = panel_text

                candidate.website = await self._extract_website(page)
                candidate.phone_number = self._extract_phone(panel_text)
                candidate.address = self._extract_address(panel_text)
                candidate.rating, candidate.review_count = self._extract_rating(panel_text)
                candidate.business_status = self._extract_status(panel_text)
                candidate.category = self._extract_category(panel_text)
            except Exception:
                continue
            finally:
                if progress_callback:
                    pct = 20 + int(((idx + 1) / len(candidates)) * 40)
                    await progress_callback(min(60, pct))

    async def _extract_website(self, page: Page) -> str | None:
        # Primary: data-item-id="authority" is the official website button in Maps
        loc = page.locator('a[data-item-id="authority"]').first
        if await loc.count():
            href = await loc.get_attribute("href")
            if href and href.startswith("http"):
                return href
        # Secondary: aria-label containing "website" (localized fallback)
        loc = page.locator('a[aria-label*="website" i], a[aria-label*="Website" i]').first
        if await loc.count():
            href = await loc.get_attribute("href")
            if href and href.startswith("http"):
                return href
        # Tertiary: data-tooltip containing "website"
        loc = page.locator('a[data-tooltip*="website" i]').first
        if await loc.count():
            href = await loc.get_attribute("href")
            if href and href.startswith("http"):
                return href
        return None

    def _extract_phone(self, text: str) -> str | None:
        match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}', text)
        return match.group(0).strip() if match else None

    def _extract_address(self, text: str) -> str | None:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        # Look for lines that look like street addresses
        address_keywords = ("street", "st.", "road", "rd.", "ave", "avenue", "blvd", "lane", "ln.",
                            "drive", "dr.", "floor", "suite", "apt", "nagar", "colony", "sector",
                            "phase", "block", "district", "near", "opp", "opposite")
        for line in lines:
            lower = line.lower()
            if any(kw in lower for kw in address_keywords) and len(line) > 10:
                return line
        # Fallback: first line with a digit that's long enough and not a phone/rating
        for line in lines:
            if (any(c.isdigit() for c in line) and len(line) > 15
                    and not re.match(r'^[\d.,()+\-\s]+$', line)):
                return line
        return None

    def _extract_rating(self, text: str) -> tuple[float | None, int | None]:
        if not text:
            return None, None
        # Handle formats like "4.5 \n (123)" or "4.5 (123)"
        match = re.search(r'(\d[\.,]\d)[\s\n]*\((\d[\d,]*)\)', text)
        if match:
            return float(match.group(1).replace(",", ".")), int(match.group(2).replace(",", ""))
        # Handle formats like "4.5 \n 123 reviews"
        match = re.search(r'(\d[\.,]\d)[\s\n]*(\d[\d,]*)\+?\s*reviews?', text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ".")), int(match.group(2).replace(",", ""))
        match = re.search(r'(\d[\.,]\d)[\s\n]*[★⭐]', text)
        if match:
            return float(match.group(1).replace(",", ".")), None
        
        # Fallback: look for a standalone line that is a valid rating (1.0 to 5.0) in the first 10 non-empty lines
        lines = [line.strip() for line in text.split("\n") if line.strip()][:10]
        for line in lines:
            if re.match(r'^[1-5][\.,][0-9]$', line):
                return float(line.replace(",", ".")), None
                
        return None, None

    def _extract_status(self, text: str) -> str | None:
        for status in ["Open", "Closed", "Temporarily closed", "Permanently closed"]:
            if status.lower() in text.lower():
                return status
        return None

    def _extract_category(self, text: str) -> str | None:
        raw_cat = self._extract_category_raw(text)
        if not raw_cat:
            return None
        # Clean unicode private use area, control characters, middots, bullets, etc.
        cleaned = re.sub(r'[\uE000-\uF8FF\u0000-\u001F\u007F-\u009F\uFFFD\u2022\u00B7]', '', raw_cat)
        cleaned = re.sub(r'[·•]', '', cleaned)
        return cleaned.strip()

    def _extract_category_raw(self, text: str) -> str | None:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for i, line in enumerate(lines):
            if line.startswith("·"):
                return line.lstrip("· ").strip()
            # If the line contains a rating, the category is often the next line
            if re.match(r'^\d[\.,]\d$', line) or re.match(r'^\([\d,]+\)$', line):
                # The category is likely 1-2 lines down
                for j in range(1, 4):
                    if i + j < len(lines):
                        candidate = lines[i + j]
                        if candidate and not re.match(r'^[\d.,()+\-\s]+$', candidate) and "reviews" not in candidate.lower() and candidate != "·":
                            # Exclude addresses or status
                            if not any(kw in candidate.lower() for kw in ["open", "closed", "street", "road", "ave", "floor", "near"]):
                                return candidate
        # Fallback to the 2nd or 3rd line if no rating is found
        if len(lines) >= 3:
             candidate = lines[1] if lines[1] != "·" else lines[2]
             if not any(c.isdigit() for c in candidate):
                  return candidate
        return None

    async def _close_detail_panel(self, page: Page) -> None:
        try:
            btn = page.locator('button[aria-label="Close"]').first
            if await btn.count():
                await btn.click(timeout=2000)
        except Exception:
            pass

    async def _collect_cards(self, page: Page, limit: int) -> list[MapBusinessCandidate]:
        results: list[MapBusinessCandidate] = []
        seen: set[str] = set()

        for _ in range(8):
            cards = await page.locator('a[href*="/maps/place/"]').evaluate_all(
                "elements => elements.map(element => ({ href: element.href, text: element.textContent || '' }))"
            )
            for card in cards:
                href = card.get("href")
                text = (card.get("text") or "").strip()
                if not href or href in seen or not text:
                    continue
                seen.add(href)
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                results.append(
                    MapBusinessCandidate(
                        name=lines[0][:255] if lines else "Unknown",
                        google_maps_url=href,
                        raw_payload={"card_text": text},
                    )
                )
                if len(results) >= limit:
                    return results

            feed = page.locator('div[role="feed"]')
            if await feed.count() == 0:
                break
            await feed.evaluate("node => node.scrollBy(0, node.scrollHeight)")
            await page.wait_for_timeout(1500)
            self._assert_no_captcha(await page.content())

        return results

    async def _dismiss_cookie_banner(self, page: Page) -> None:
        for label in ["Accept all", "I agree", "Reject all"]:
            locator = page.get_by_role("button", name=label)
            try:
                if await locator.count():
                    await locator.first.click(timeout=2000)
                    break
            except Exception:
                continue

    def _assert_no_captcha(self, html: str) -> None:
        lowered = html.lower()
        if "captcha" in lowered or "unusual traffic" in lowered or "/sorry/" in lowered:
            raise CaptchaDetectedError("Google Maps captcha detected")
