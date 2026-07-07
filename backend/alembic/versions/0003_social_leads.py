"""add social_searches and social_leads tables

Revision ID: 0003
Revises: 0002_increase_address_length
Create Date: 2026-07-07
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002_increase_address_length"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "social_searches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", postgresql.ENUM("queued", "running", "completed", "failed", name="jobstatus", create_type=False), nullable=False, server_default="queued"),
        sa.Column("industry", sa.String(255), nullable=False, index=True),
        sa.Column("location", sa.String(255), nullable=False, index=True),
        sa.Column("keywords", sa.String(512), nullable=True),
        sa.Column("sources", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("filters", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("query_summary", sa.String(512), nullable=True),
        sa.Column("target_limit", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_social_searches_status", "social_searches", ["status"])

    op.create_table(
        "social_leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("search_id", sa.Integer(), sa.ForeignKey("social_searches.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("source_platform", sa.String(64), nullable=False, index=True),
        sa.Column("profile_url", sa.String(2048), nullable=True),
        sa.Column("website", sa.String(1024), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("linkedin", sa.String(1024), nullable=True),
        sa.Column("facebook", sa.String(1024), nullable=True),
        sa.Column("instagram", sa.String(1024), nullable=True),
        sa.Column("twitter", sa.String(1024), nullable=True),
        sa.Column("github", sa.String(1024), nullable=True),
        sa.Column("youtube", sa.String(1024), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(255), nullable=True),
        sa.Column("state", sa.String(255), nullable=True),
        sa.Column("country", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("services", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("employee_estimate", sa.String(128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("technologies", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("google_rating", sa.Float(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("last_activity", sa.String(128), nullable=True),
        sa.Column("confidence_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lead_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("digital_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("has_website", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_ssl", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_email", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_phone", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("social_leads")
    op.drop_table("social_searches")
