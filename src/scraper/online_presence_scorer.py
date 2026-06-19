"""
Online Presence Scorer
======================
Computes a 0-100 Digital Presence Score for each business by evaluating:
  - Website quality          (0-35 pts)
  - Social media signals     (0-45 pts total: FB/IG/TW/LI/YT/Wiki/TA)
  - Contact info             (0-10 pts)
  - OSM map listing          (always +10 pts — they exist on OSM)

Score breakdown
---------------
  OSM map listing   : +10  (always, since we got them from OSM)
  Good Website      : +35
  Poor Website      : +20
  Has Website       : +15   (URL listed but couldn't verify quality)
  No Website        :  +0
  Facebook          : +12
  Instagram         : +12
  Twitter/X         :  +8
  LinkedIn          :  +8
  YouTube           :  +5
  Wikipedia page    :  +5
  TripAdvisor       :  +5
  Phone number      :  +5
  Email address     :  +5
  ─────────────────────────
  Max total         : 110 → capped at 100

Lead Opportunity Score = 100 - Digital Presence Score
(Businesses with the weakest online presence = highest value leads)
"""


class OnlinePresenceScorer:

    WEBSITE_POINTS = {
        "Good Website": 35,
        "Poor Website": 20,
        "Has Website":  15,
        "No Website":    0,
    }

    SOCIAL_POINTS = {
        "Facebook URL":    12,
        "Instagram URL":   12,
        "Twitter URL":      8,
        "LinkedIn URL":     8,
        "YouTube URL":      5,
        "Wikipedia URL":    5,
        "TripAdvisor URL":  5,
    }

    CONTACT_POINTS = {
        "Phone Number":  5,
        "Email Address": 5,
    }

    OSM_LISTING_BONUS = 10  # They're already on the map — base visibility

    def score(self, row: dict, website_status: str) -> dict:
        """
        Compute presence signals and return an enriched dict with:
          - 'Digital Presence Score'   (0-100)
          - 'Lead Opportunity Score'   (0-100, inverse)
          - 'Presence Breakdown'       (human-readable summary string)
          - 'Social Channels'          (comma-separated list of active platforms)
        """
        pts = self.OSM_LISTING_BONUS

        # ── Website ──────────────────────────────────────────────────────
        pts += self.WEBSITE_POINTS.get(website_status, 0)

        # ── Social media ─────────────────────────────────────────────────
        active_socials = []
        for platform, bonus in self.SOCIAL_POINTS.items():
            val = row.get(platform) or ""
            if val and str(val).strip() not in ("", "nan", "None"):
                pts += bonus
                # Pretty label for display
                label = platform.replace(" URL", "")
                active_socials.append(label)

        # ── Contact info ──────────────────────────────────────────────────
        for field, bonus in self.CONTACT_POINTS.items():
            val = row.get(field) or ""
            if val and str(val).strip() not in ("", "nan", "None"):
                pts += bonus

        # ── Cap at 100 ────────────────────────────────────────────────────
        digital_score   = min(pts, 100)
        opportunity_score = 100 - digital_score

        # ── Human-readable breakdown ──────────────────────────────────────
        breakdown_parts = [f"Website: {website_status}"]
        if active_socials:
            breakdown_parts.append(f"Social: {', '.join(active_socials)}")
        else:
            breakdown_parts.append("Social: None found")

        has_phone = bool((row.get("Phone Number") or "").strip())
        has_email = bool((row.get("Email Address") or "").strip())
        contact_parts = []
        if has_phone: contact_parts.append("Phone")
        if has_email: contact_parts.append("Email")
        breakdown_parts.append(f"Contact: {', '.join(contact_parts) if contact_parts else 'None'}")

        return {
            "Digital Presence Score": digital_score,
            "Lead Opportunity Score": opportunity_score,
            "Social Channels":        ", ".join(active_socials) if active_socials else "",
            "Presence Breakdown":     " | ".join(breakdown_parts),
        }

    @staticmethod
    def opportunity_to_priority(opportunity_score: int) -> str:
        """Maps Opportunity Score → High / Medium / Low priority tier."""
        if opportunity_score >= 70:
            return "High"
        elif opportunity_score >= 40:
            return "Medium"
        else:
            return "Low"


if __name__ == "__main__":
    scorer = OnlinePresenceScorer()

    no_web = scorer.score({"Phone Number": "", "Email Address": ""}, "No Website")
    print("No web, no socials:", no_web)

    rich = scorer.score({
        "Phone Number": "+91-999",
        "Email Address": "info@xyz.com",
        "Facebook URL": "https://facebook.com/xyz",
        "Instagram URL": "https://instagram.com/xyz",
    }, "Good Website")
    print("Rich presence:", rich)
