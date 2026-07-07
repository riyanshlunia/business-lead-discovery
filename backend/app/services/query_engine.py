"""
Google Query Engine — generates advanced search queries for each platform/industry/location
combination. Supports industries, services, technology stacks, and company types.
No I/O; pure computation.
"""
from __future__ import annotations

import itertools
import random
from dataclasses import dataclass


# ── Platform site-operators ───────────────────────────────────────────────────
PLATFORM_SITES: dict[str, str] = {
    "linkedin":     "site:linkedin.com/company",
    "reddit":       "site:reddit.com",
    "crunchbase":   "site:crunchbase.com/organization",
    "wellfound":    "site:wellfound.com/company",
    "producthunt":  "site:producthunt.com",
    "googlemaps":   "site:google.com/maps",
    "github":       "site:github.com",
    "builtwith":    "site:builtwith.com",
    "wappalyzer":   "site:wappalyzer.com",
    "techcrunch":   "site:techcrunch.com",
    "indeed":       "site:indeed.com/cmp",
    "clutch":       "site:clutch.co",
    "goodfirms":    "site:goodfirms.co",
    "twitter":      "site:twitter.com",
    "facebook":     "site:facebook.com",
}

# Additional high-value directories for broader discovery
DIRECTORY_SITES = [
    "site:crunchbase.com",
    "site:clutch.co",
    "site:goodfirms.co",
    "site:g2.com",
    "site:trustpilot.com",
    "site:yelp.com",
    "site:yellowpages.com",
    "site:bbb.org",
    "site:capterra.com",
    "site:getapp.com",
]

# Modifiers to increase query variation
COMPANY_MODIFIERS = [
    "agency",
    "company",
    "services",
    "solutions",
    "consultancy",
    "firm",
    "studio",
    "inc",
    "llc",
]

# Industry-specific search patterns
INDUSTRY_TEMPLATES: dict[str, list[str]] = {
    "healthcare": ['"medical practice"', '"health clinic"', '"hospital"', '"healthcare provider"'],
    "real estate": ['"real estate agency"', '"property management"', '"realty"', '"realtor"'],
    "manufacturing": ['"manufacturing company"', '"industrial"', '"production facility"'],
    "education": ['"school"', '"university"', '"coaching institute"', '"training center"'],
    "finance": ['"financial services"', '"accounting firm"', '"fintech"', '"investment"'],
    "restaurants": ['"restaurant"', '"food service"', '"catering"', '"cafe"'],
    "hotels": ['"hotel"', '"hospitality"', '"resort"', '"accommodation"'],
    "construction": ['"construction company"', '"contractor"', '"builder"', '"civil engineering"'],
    "logistics": ['"logistics company"', '"freight"', '"supply chain"', '"transportation"'],
    "automobile": ['"auto dealership"', '"car dealer"', '"automotive"', '"vehicle service"'],
    "retail": ['"retail store"', '"ecommerce"', '"online shop"', '"boutique"'],
    "legal": ['"law firm"', '"legal services"', '"attorney"', '"solicitor"'],
    "agriculture": ['"farming"', '"agribusiness"', '"agricultural"'],
    "recruitment": ['"staffing agency"', '"recruitment firm"', '"headhunter"'],
    "marketing": ['"marketing agency"', '"digital marketing"', '"advertising agency"'],
    "saas": ['"saas company"', '"software startup"', '"cloud software"'],
    "startups": ['"startup"', '"early stage"', '"seed funded"'],
}

# Service-based search terms
SERVICE_OPERATORS: dict[str, list[str]] = {
    "ai_chatbot": ['"AI chatbot"', '"conversational AI"', '"chatbot development"'],
    "ai_voice": ['"AI voice agent"', '"voice AI"'],
    "web_development": ['"web development"', '"website development"'],
    "mobile_app": ['"mobile app development"', '"iOS app"', '"Android app"'],
    "seo": ['"SEO services"', '"search engine optimization"'],
    "crm": ['"CRM development"', '"CRM software"'],
    "ecommerce": ['"ecommerce development"', '"shopify"', '"woocommerce"'],
    "digital_marketing": ['"digital marketing"', '"social media marketing"'],
    "ui_ux": ['"UI UX design"', '"user experience"'],
    "branding": ['"branding agency"', '"brand identity"', '"logo design"'],
    "cloud_devops": ['"cloud services"', '"DevOps"', '"AWS"', '"Azure"'],
}

# Technology stack terms
TECH_OPERATORS: dict[str, str] = {
    "react": "React",
    "vue": "Vue.js",
    "angular": "Angular",
    "nextjs": "Next.js",
    "nodejs": "Node.js",
    "python": "Python",
    "django": "Django",
    "fastapi": "FastAPI",
    "shopify": "Shopify",
    "wordpress": "WordPress",
    "aws": "AWS",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "flutter": "Flutter",
    "react_native": "React Native",
}


@dataclass
class SearchQuery:
    query: str
    platform: str
    category: str  # "directory" | "social" | "broad" | "industry" | "service"


class QueryEngine:
    """
    Generates a diverse set of Google search queries for the given parameters.
    Returns a deduplicated list of SearchQuery objects, sorted for quality.
    """

    def generate(
        self,
        industry: str,
        location: str,
        keywords: str | None = None,
        sources: list[str] | None = None,
        services: list[str] | None = None,
        tech_stack: list[str] | None = None,
        company_size: str | None = None,
        limit: int = 40,
    ) -> list[SearchQuery]:
        queries: list[SearchQuery] = []
        active_platforms = sources or list(PLATFORM_SITES.keys())
        industry_lower = industry.lower()

        # 1. Platform-specific site: queries
        for platform in active_platforms:
            site_op = PLATFORM_SITES.get(platform)
            if not site_op:
                continue
            # Base query
            queries.append(SearchQuery(
                query=f'{site_op} "{industry}" "{location}"',
                platform=platform,
                category="social",
            ))
            # With keyword
            if keywords:
                queries.append(SearchQuery(
                    query=f'{site_op} "{industry}" "{keywords}" "{location}"',
                    platform=platform,
                    category="social",
                ))
            # With modifier
            mod = random.choice(COMPANY_MODIFIERS)
            queries.append(SearchQuery(
                query=f'{site_op} {industry} {mod} {location}',
                platform=platform,
                category="social",
            ))
            # Company size hint
            if company_size:
                queries.append(SearchQuery(
                    query=f'{site_op} "{industry}" {location} "{company_size} employees"',
                    platform=platform,
                    category="social",
                ))

        # 2. Industry-specific templates
        industry_terms = []
        for key, terms in INDUSTRY_TEMPLATES.items():
            if key in industry_lower or industry_lower in key:
                industry_terms = terms
                break
        if not industry_terms:
            industry_terms = [f'"{industry}"']

        for term in industry_terms[:2]:
            queries.append(SearchQuery(
                query=f'{term} {location} contact email',
                platform="google",
                category="industry",
            ))
            queries.append(SearchQuery(
                query=f'intitle:{term} {location} "about us"',
                platform="google",
                category="industry",
            ))

        # 3. Service-based queries
        if services:
            for svc in services[:3]:
                svc_lower = svc.lower().replace(" ", "_")
                svc_terms = SERVICE_OPERATORS.get(svc_lower, [f'"{svc}"'])
                for term in svc_terms[:1]:
                    queries.append(SearchQuery(
                        query=f'{term} company {location}',
                        platform="google",
                        category="service",
                    ))
                    queries.append(SearchQuery(
                        query=f'site:clutch.co {term} {location}',
                        platform="clutch",
                        category="service",
                    ))

        # 4. Technology stack queries
        if tech_stack:
            for tech in tech_stack[:3]:
                tech_label = TECH_OPERATORS.get(tech.lower(), tech)
                queries.append(SearchQuery(
                    query=f'"{tech_label}" {industry} company {location}',
                    platform="google",
                    category="service",
                ))
                queries.append(SearchQuery(
                    query=f'site:github.com "{tech_label}" "{industry}" {location}',
                    platform="github",
                    category="service",
                ))

        # 5. Directory-based discovery
        for site in DIRECTORY_SITES:
            queries.append(SearchQuery(
                query=f'{site} {industry} {location}',
                platform="directory",
                category="directory",
            ))
            if keywords:
                queries.append(SearchQuery(
                    query=f'{site} "{keywords}" {location}',
                    platform="directory",
                    category="directory",
                ))

        # 6. Broad Google queries (no site: — discovers company websites directly)
        broad_templates = [
            f'"{industry}" agency {location} site:*.com',
            f'"{industry}" company {location} -site:linkedin.com -site:facebook.com',
            f'intitle:"{industry}" inurl:contact {location}',
            f'"{industry}" {location} contact email',
            f'"{industry}" services {location} "about us"',
            f'"{industry}" {location} "our services" "contact us"',
            f'"{industry}" {location} inurl:about email phone',
        ]
        if keywords:
            broad_templates += [
                f'"{keywords}" {industry} {location}',
                f'"{keywords}" company {location} email',
                f'"{keywords}" {location} "hire us" OR "contact us"',
            ]
        for tmpl in broad_templates:
            queries.append(SearchQuery(query=tmpl, platform="google", category="broad"))

        # 7. Location + industry combos without quotes
        for mod in COMPANY_MODIFIERS[:4]:
            queries.append(SearchQuery(
                query=f'{industry} {mod} {location}',
                platform="google",
                category="broad",
            ))

        # Deduplicate by query string
        seen: set[str] = set()
        unique: list[SearchQuery] = []
        for q in queries:
            if q.query not in seen:
                seen.add(q.query)
                unique.append(q)

        # Prioritise social/directory over broad
        priority_order = {"social": 0, "industry": 1, "service": 1, "directory": 2, "broad": 3}
        unique.sort(key=lambda q: priority_order.get(q.category, 4))

        return unique[:limit]
