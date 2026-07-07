from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    projects: Mapped[list[Project]] = relationship(back_populates="user", cascade="all,delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    industry: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="projects")
    jobs: Mapped[list[Job]] = relationship(back_populates="project", cascade="all,delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.queued, index=True)
    industry: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[str] = mapped_column(String(255), index=True)
    query: Mapped[str] = mapped_column(String(512))
    target_limit: Mapped[int] = mapped_column(Integer, default=100)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship(back_populates="jobs")
    businesses: Mapped[list[Business]] = relationship(back_populates="job", cascade="all,delete-orphan")


class Business(Base):
    __tablename__ = "businesses"
    __table_args__ = (UniqueConstraint("google_maps_url", name="uq_business_google_maps_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    website: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    google_maps_url: Mapped[str] = mapped_column(String(2048), index=True)
    business_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    opening_hours: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[Job] = relationship(back_populates="businesses")
    website_record: Mapped[Website | None] = relationship(back_populates="business", cascade="all,delete-orphan", uselist=False)
    social_accounts: Mapped[list[SocialAccount]] = relationship(back_populates="business", cascade="all,delete-orphan")
    emails: Mapped[list[Email]] = relationship(back_populates="business", cascade="all,delete-orphan")
    lead_score: Mapped[LeadScore | None] = relationship(back_populates="business", cascade="all,delete-orphan", uselist=False)


class Website(Base):
    __tablename__ = "websites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), unique=True)
    url: Mapped[str] = mapped_column(String(1024))
    final_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    ssl_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    https_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    meta_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_count: Mapped[int] = mapped_column(Integer, default=0)
    contact_page_found: Mapped[bool] = mapped_column(Boolean, default=False)
    form_count: Mapped[int] = mapped_column(Integer, default=0)
    load_speed_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mobile_viewport: Mapped[bool] = mapped_column(Boolean, default=False)
    google_analytics: Mapped[bool] = mapped_column(Boolean, default=False)
    facebook_pixel: Mapped[bool] = mapped_column(Boolean, default=False)
    robots_txt: Mapped[bool] = mapped_column(Boolean, default=False)
    sitemap_xml: Mapped[bool] = mapped_column(Boolean, default=False)
    analysis_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    business: Mapped[Business] = relationship(back_populates="website_record")


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(64), index=True)
    url: Mapped[str] = mapped_column(String(1024))
    handle: Mapped[str | None] = mapped_column(String(255), nullable=True)

    business: Mapped[Business] = relationship(back_populates="social_accounts")


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    address: Mapped[str] = mapped_column(String(320), index=True)
    source: Mapped[str] = mapped_column(String(64), default="website")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    business: Mapped[Business] = relationship(back_populates="emails")


class LeadScore(Base):
    __tablename__ = "lead_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), unique=True)
    digital_presence_score: Mapped[int] = mapped_column(Integer)
    lead_opportunity_score: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    business: Mapped[Business] = relationship(back_populates="lead_score")


class Export(Base):
    __tablename__ = "exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    format: Mapped[str] = mapped_column(String(32))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SocialSearch(Base):
    __tablename__ = "social_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.queued, index=True)
    industry: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[str] = mapped_column(String(255), index=True)
    keywords: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sources: Mapped[dict] = mapped_column(JSON, default=list)
    filters: Mapped[dict] = mapped_column(JSON, default=dict)
    query_summary: Mapped[str | None] = mapped_column(String(512), nullable=True)
    target_limit: Mapped[int] = mapped_column(Integer, default=20)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    total_found: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    leads: Mapped[list[SocialLead]] = relationship(back_populates="search", cascade="all,delete-orphan")


class SocialLead(Base):
    __tablename__ = "social_leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    search_id: Mapped[int] = mapped_column(ForeignKey("social_searches.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    source_platform: Mapped[str] = mapped_column(String(64), index=True)
    profile_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    website: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    linkedin: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    facebook: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    instagram: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    twitter: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    github: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    youtube: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    services: Mapped[dict] = mapped_column(JSON, default=list)
    employee_estimate: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    technologies: Mapped[dict] = mapped_column(JSON, default=list)
    google_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_activity: Mapped[str | None] = mapped_column(String(128), nullable=True)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    lead_score: Mapped[int] = mapped_column(Integer, default=0)
    digital_score: Mapped[int] = mapped_column(Integer, default=0)
    has_website: Mapped[bool] = mapped_column(Boolean, default=False)
    has_ssl: Mapped[bool] = mapped_column(Boolean, default=False)
    has_email: Mapped[bool] = mapped_column(Boolean, default=False)
    has_phone: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    search: Mapped[SocialSearch] = relationship(back_populates="leads")


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    industry: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    keywords: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sources: Mapped[dict] = mapped_column(JSON, default=list)
    filters: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
