from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class SocialAccountRead(BaseModel):
    platform: str
    url: str
    handle: str | None = None


class EmailRead(BaseModel):
    address: str
    source: str
    is_primary: bool


class WebsiteRead(BaseModel):
    url: str
    final_url: str | None
    ssl_enabled: bool
    https_enabled: bool
    meta_title: str | None
    meta_description: str | None
    image_count: int
    contact_page_found: bool
    form_count: int
    load_speed_ms: int | None
    mobile_viewport: bool
    google_analytics: bool
    facebook_pixel: bool
    robots_txt: bool
    sitemap_xml: bool


class LeadScoreRead(BaseModel):
    digital_presence_score: int
    lead_opportunity_score: int
    explanation: dict


class BusinessRead(BaseModel):
    id: int
    name: str
    website: str | None
    phone_number: str | None
    website_phones: list[str] = Field(default_factory=list)
    address: str | None
    category: str | None
    rating: float | None
    review_count: int | None
    latitude: float | None
    longitude: float | None
    google_maps_url: str
    business_status: str | None
    opening_hours: str | None
    created_at: datetime
    website_record: WebsiteRead | None = None
    social_accounts: list[SocialAccountRead] = Field(default_factory=list)
    emails: list[EmailRead] = Field(default_factory=list)
    lead_score: LeadScoreRead | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def extract_website_phones(cls, data: Any) -> Any:
        """Pull website_phones out of raw_payload for convenient API access."""
        if hasattr(data, "raw_payload") and isinstance(data.raw_payload, dict):
            # Will be set as attribute — pydantic will pick it up
            if not hasattr(data, "website_phones") or not data.website_phones:
                object.__setattr__(data, "website_phones", data.raw_payload.get("website_phones", []))
        elif isinstance(data, dict) and "raw_payload" in data:
            data.setdefault("website_phones", data["raw_payload"].get("website_phones", []))
        return data

