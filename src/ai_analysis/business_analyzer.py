import os
from openai import OpenAI


class BusinessAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        else:
            self.client = None

    def analyze_opportunity(self, business_name, industry, website_status,
                            social_channels="", digital_score=None):
        """
        Uses AI to generate a business opportunity analysis.

        Parameters
        ----------
        business_name   : str
        industry        : str
        website_status  : 'No Website' | 'Has Website' | 'Poor Website' | 'Good Website'
        social_channels : comma-separated active platforms, e.g. "Facebook, Instagram"
        digital_score   : int 0-100 — overall digital presence score
        """
        if not self.client:
            return self._heuristic_analysis(
                business_name, industry, website_status, social_channels, digital_score
            )

        status_desc = self._status_to_description(website_status)
        social_desc = (
            f"Active on: {social_channels}." if social_channels
            else "No social media presence detected."
        )
        score_desc = (
            f"Overall digital presence score: {digital_score}/100."
            if digital_score is not None else ""
        )

        prompt = (
            f"Business: '{business_name}' | Industry: '{industry}'\n"
            f"Website: {status_desc}\n"
            f"Social media: {social_desc}\n"
            f"{score_desc}\n\n"
            f"Write a sharp 1-2 sentence pitch on what digital service they need most. "
            f"Be specific and factual — do NOT contradict the presence data above."
        )

        try:
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a concise digital marketing expert. "
                            "Always base your advice strictly on the provided data."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=90,
                temperature=0.6,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return self._heuristic_analysis(
                business_name, industry, website_status, social_channels, digital_score
            )

    @staticmethod
    def _status_to_description(website_status):
        descriptions = {
            "No Website":   "NO website at all — zero web presence.",
            "Has Website":  "Has a website URL listed, but it was unreachable during our scan (may be slow/down/geo-blocked).",
            "Poor Website": "Has a LIVE website, but it is poor quality — thin content, missing contact info, or outdated.",
            "Good Website": "Has a GOOD, functional website with solid content and contact info.",
        }
        return descriptions.get(website_status, f"Unknown: {website_status}")

    def _heuristic_analysis(self, business_name, industry, website_status,
                            social_channels="", digital_score=None):
        """Rule-based fallback when AI API is unavailable."""
        has_social = bool(social_channels and social_channels.strip())

        if website_status == "No Website" and not has_social:
            return (
                f"{business_name} has zero digital presence — no website, no social media. "
                f"Massive opportunity: pitch a full digital starter pack (website + social setup + local SEO)."
            )
        elif website_status == "No Website" and has_social:
            return (
                f"{business_name} is active on {social_channels} but has no website. "
                f"Great fit for a professional landing page to convert their social audience."
            )
        elif website_status == "Has Website" and not has_social:
            return (
                f"{business_name} has a website but it was unreachable, and no social media was found. "
                f"Pitch a site audit/rebuild plus social media setup."
            )
        elif website_status == "Has Website":
            return (
                f"{business_name} has a website (currently unreachable) and is on {social_channels}. "
                f"Recommend a hosting upgrade, site audit, and social ad campaigns."
            )
        elif website_status == "Poor Website" and not has_social:
            return (
                f"{business_name} has a weak website and no social media — high opportunity. "
                f"Pitch a full redesign, SEO, and a social media management package."
            )
        elif website_status == "Poor Website":
            return (
                f"{business_name} has a poor website but maintains {social_channels}. "
                f"Focus pitch on a modern redesign and linking social traffic to a better site."
            )
        else:  # Good Website
            if has_social:
                return (
                    f"{business_name} has a solid web and social presence ({social_channels}). "
                    f"Pitch advanced SEO, paid ads, or custom software to deepen their edge."
                )
            return (
                f"{business_name} has a good website but limited social presence. "
                f"Pitch social media management and an integrated content marketing strategy."
            )


if __name__ == "__main__":
    analyzer = BusinessAnalyzer()
    cases = [
        ("ABC Hotel",    "Hotels",   "No Website",   "",                     5),
        ("XYZ Cafe",     "Cafes",    "Has Website",  "Facebook, Instagram",  42),
        ("Great Dental", "Dentists", "Poor Website", "Facebook",             38),
        ("TopShop",      "Retail",   "Good Website", "Instagram, Twitter",   78),
    ]
    for name, ind, ws, social, score in cases:
        print(f"\n[{ws}] {name}:")
        print(analyzer.analyze_opportunity(name, ind, ws, social, score))
