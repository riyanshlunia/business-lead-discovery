import logging
import requests
import re

logger = logging.getLogger(__name__)

class WebsiteChecker:
    def __init__(self):
        self.timeout = 8

    def check_website(self, url):
        """
        Analyzes whether a business has a website and its quality.

        Logic:
          - If no URL provided at all  → 'No Website'
          - If URL provided but request completely fails (DNS/conn error) → 'Has Website'
            (The business HAS listed a website; we just can't reach it right now)
          - If URL provided, responds with non-200 status → 'Poor Website'
          - If URL provided, 200 OK but thin content → 'Poor Website'
          - If URL provided, 200 OK with rich content  → 'Good Website'

        Returns: 'No Website' | 'Has Website' | 'Poor Website' | 'Good Website'
        """
        # No URL at all — business truly has no web presence listed
        if not url or str(url).strip() in ("", "nan", "None"):
            return "No Website"

        url = str(url).strip()
        if not url.startswith("http"):
            url = "https://" + url

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            logger.info("Calling website HTTP check for %s", url)
            response = requests.get(
                url,
                timeout=self.timeout,
                headers=headers,
                allow_redirects=True,
            )
            logger.info("Returned from website HTTP check for %s", url)

            if response.status_code == 200:
                content = response.text
                content_length = len(content)
                lower = content.lower()

                # Heuristics for quality assessment
                has_contact   = bool(re.search(r"contact|email|phone|whatsapp|reach us", lower))
                has_nav       = bool(re.search(r"<nav|navbar|menu|header", lower))
                has_images    = lower.count("<img") >= 3
                has_meta_desc = bool(re.search(r'<meta[^>]+description', lower))

                quality_score = (
                    (1 if content_length > 5000 else 0)
                    + (1 if has_contact else 0)
                    + (1 if has_nav else 0)
                    + (1 if has_images else 0)
                    + (1 if has_meta_desc else 0)
                )

                if quality_score >= 3:
                    return "Good Website"
                else:
                    return "Poor Website"

            elif response.status_code in (301, 302, 303, 307, 308):
                # Redirect but ultimately failed — still has a website
                return "Has Website"
            else:
                # Server responded with error (404, 500, etc.) — site exists but broken
                return "Poor Website"

        except requests.exceptions.ConnectionError:
            # DNS lookup failed or connection refused — domain may be dead,
            # but the business DID list a website URL → "Has Website"
            return "Has Website"
        except requests.exceptions.Timeout:
            # Server too slow — it's there, just slow → "Has Website"
            return "Has Website"
        except requests.exceptions.TooManyRedirects:
            return "Has Website"
        except Exception:
            # Any other error — we know a URL was listed
            return "Has Website"


if __name__ == "__main__":
    checker = WebsiteChecker()
    print(checker.check_website("https://example.com"))      # Good/Poor Website
    print(checker.check_website("https://thisdomaindoesnotexist999.com"))  # Has Website
    print(checker.check_website(None))                        # No Website
    print(checker.check_website(""))                          # No Website
