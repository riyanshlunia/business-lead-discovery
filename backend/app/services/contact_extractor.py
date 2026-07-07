from __future__ import annotations

import re
from dataclasses import dataclass, field


EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{2,4}\)?[\s\-]?)?\d{3,5}[\s\-]?\d{3,5}")
MAILTO_RE = re.compile(r"mailto:([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})", re.IGNORECASE)
TEL_RE = re.compile(r"tel:([\d\s+\-().]{7,})", re.IGNORECASE)
SOCIAL_PATTERNS = {
    "facebook": re.compile(r"https?://(?:www\.)?facebook\.com/[A-Za-z0-9_.-]+", re.IGNORECASE),
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/[A-Za-z0-9_.-]+", re.IGNORECASE),
    "linkedin": re.compile(r"https?://(?:www\.)?linkedin\.com/[A-Za-z0-9_./-]+", re.IGNORECASE),
    "twitter": re.compile(r"https?://(?:www\.)?(?:twitter\.com|x\.com)/[A-Za-z0-9_./-]+", re.IGNORECASE),
    "youtube": re.compile(r"https?://(?:www\.)?youtube\.com/[A-Za-z0-9_./-]+", re.IGNORECASE),
    "tiktok": re.compile(r"https?://(?:www\.)?tiktok\.com/[A-Za-z0-9_./-]+", re.IGNORECASE),
}


@dataclass(slots=True)
class ContactExtractionResult:
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    whatsapp: list[str] = field(default_factory=list)
    social_links: dict[str, list[str]] = field(default_factory=dict)


class ContactExtractor:
    def extract(self, text: str) -> ContactExtractionResult:
        # Emails: from mailto: links first (most reliable), then regex scan
        mailto_emails = {m.lower() for m in MAILTO_RE.findall(text)}
        regex_emails = {m.lower() for m in EMAIL_RE.findall(text)}
        emails = sorted(mailto_emails | regex_emails)

        # Phones: from tel: links first (most reliable), then regex scan
        tel_phones = {self._normalize_phone(m) for m in TEL_RE.findall(text)}
        regex_phones = {self._normalize_phone(m) for m in PHONE_RE.findall(text)}
        # Filter out very short matches (noise)
        phones = sorted({p for p in (tel_phones | regex_phones) if len(re.sub(r"\D", "", p)) >= 7})

        social_links: dict[str, list[str]] = {platform: [] for platform in SOCIAL_PATTERNS}
        for platform, pattern in SOCIAL_PATTERNS.items():
            social_links[platform] = sorted(set(pattern.findall(text)))

        whatsapp = sorted(set(re.findall(r"https?://(?:wa\.me|api\.whatsapp\.com)/[A-Za-z0-9_./?=&-]+", text, re.IGNORECASE)))
        return ContactExtractionResult(emails=emails, phones=phones, whatsapp=whatsapp, social_links=social_links)

    def _normalize_phone(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

