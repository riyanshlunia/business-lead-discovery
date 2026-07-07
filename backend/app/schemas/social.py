"""
Pydantic schemas for the Social Lead Finder API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SocialSearchCreate(BaseModel):
    industry: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=255)
    keywords: str | None = Field(default=None, max_length=512)
    sources: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=20, ge=0, le=500)  # ge=0 allows clearing field


class SocialSearchRead(BaseModel):
    id: int
    status: str
    industry: str
    location: str
    keywords: str | None
    sources: list
    filters: dict
    query_summary: str | None
    target_limit: int
    progress: int
    total_found: int
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class SocialLeadRead(BaseModel):
    id: int
    search_id: int
    name: str
    source_platform: str
    profile_url: str | None
    website: str | None
    email: str | None
    phone: str | None
    linkedin: str | None
    facebook: str | None
    instagram: str | None
    twitter: str | None
    github: str | None
    youtube: str | None
    address: str | None
    city: str | None
    state: str | None
    country: str | None
    industry: str | None
    services: list
    employee_estimate: str | None
    description: str | None
    technologies: list
    google_rating: float | None
    review_count: int | None
    last_activity: str | None
    confidence_score: int
    lead_score: int
    digital_score: int
    has_website: bool
    has_ssl: bool
    has_email: bool
    has_phone: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SavedSearchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    industry: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=255)
    keywords: str | None = Field(default=None, max_length=512)
    sources: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)


class SavedSearchRead(BaseModel):
    id: int
    name: str
    industry: str
    location: str
    keywords: str | None
    sources: list
    filters: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyticsRead(BaseModel):
    total_searches: int
    total_leads: int
    qualified_leads: int
    avg_lead_score: float
    avg_confidence: float
    platform_distribution: dict[str, int]
    status_distribution: dict[str, int]
    top_industries: list[dict[str, Any]]
