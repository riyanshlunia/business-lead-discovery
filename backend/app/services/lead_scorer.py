from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LeadScoreResult:
    digital_presence_score: int
    lead_opportunity_score: int
    explanation: dict[str, int | str]


class LeadScorer:
    def score(
        self,
        *,
        website_exists: bool,
        ssl_enabled: bool,
        social_presence_count: int,
        contact_count: int,
        seo_signals: int,
        performance_score: int,
        review_count: int | None,
        rating: float | None,
    ) -> LeadScoreResult:
        digital_presence = 0
        digital_presence += 22 if website_exists else 0
        digital_presence += 18 if ssl_enabled else 0
        digital_presence += min(social_presence_count * 8, 20)
        digital_presence += min(contact_count * 8, 16)
        digital_presence += min(seo_signals * 8, 16)
        digital_presence += min(performance_score, 8)
        digital_presence = max(0, min(100, digital_presence))

        opportunity = 100 - digital_presence
        if not website_exists:
            opportunity += 10
        if not ssl_enabled:
            opportunity += 6
        if contact_count == 0:
            opportunity += 10
        if social_presence_count == 0:
            opportunity += 8
        if review_count is not None and review_count < 20:
            opportunity += 4
        if rating is not None and rating >= 4.3:
            opportunity -= 6
        opportunity = max(0, min(100, opportunity))

        explanation = {
            "website_exists": "yes" if website_exists else "no",
            "ssl_enabled": int(ssl_enabled),
            "social_presence_count": social_presence_count,
            "contact_count": contact_count,
            "seo_signals": seo_signals,
            "performance_score": performance_score,
        }
        return LeadScoreResult(digital_presence, opportunity, explanation)
