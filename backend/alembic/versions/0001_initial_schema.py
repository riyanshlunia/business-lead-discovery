"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-03 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'jobstatus') THEN CREATE TYPE jobstatus AS ENUM ('queued', 'running', 'completed', 'failed'); END IF; END $$;")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("email"),
    )

    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_projects_user_id"), "projects", ["user_id"], unique=False)
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)
    op.create_index(op.f("ix_projects_industry"), "projects", ["industry"], unique=False)
    op.create_index(op.f("ix_projects_location"), "projects", ["location"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", postgresql.ENUM("queued", "running", "completed", "failed", name="jobstatus", create_type=False), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("query", sa.String(length=512), nullable=False),
        sa.Column("target_limit", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_jobs_project_id"), "jobs", ["project_id"], unique=False)
    op.create_index(op.f("ix_jobs_status"), "jobs", ["status"], unique=False)
    op.create_index(op.f("ix_jobs_industry"), "jobs", ["industry"], unique=False)
    op.create_index(op.f("ix_jobs_location"), "jobs", ["location"], unique=False)

    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=1024), nullable=True),
        sa.Column("phone_number", sa.String(length=64), nullable=True),
        sa.Column("address", sa.String(length=512), nullable=True),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("google_maps_url", sa.String(length=2048), nullable=False),
        sa.Column("business_status", sa.String(length=128), nullable=True),
        sa.Column("opening_hours", sa.Text(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("google_maps_url", name="uq_business_google_maps_url"),
    )
    op.create_index(op.f("ix_businesses_job_id"), "businesses", ["job_id"], unique=False)
    op.create_index(op.f("ix_businesses_name"), "businesses", ["name"], unique=False)
    op.create_index(op.f("ix_businesses_google_maps_url"), "businesses", ["google_maps_url"], unique=False)

    op.create_table(
        "websites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("final_url", sa.String(length=1024), nullable=True),
        sa.Column("ssl_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("https_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("meta_title", sa.String(length=512), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("image_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("contact_page_found", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("form_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("load_speed_ms", sa.Integer(), nullable=True),
        sa.Column("mobile_viewport", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("google_analytics", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("facebook_pixel", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("robots_txt", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sitemap_xml", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("analysis_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("business_id"),
    )

    op.create_table(
        "social_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=True),
    )
    op.create_index(op.f("ix_social_accounts_business_id"), "social_accounts", ["business_id"], unique=False)
    op.create_index(op.f("ix_social_accounts_platform"), "social_accounts", ["platform"], unique=False)

    op.create_table(
        "emails",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("address", sa.String(length=320), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="website"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(op.f("ix_emails_business_id"), "emails", ["business_id"], unique=False)
    op.create_index(op.f("ix_emails_address"), "emails", ["address"], unique=False)

    op.create_table(
        "lead_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("digital_presence_score", sa.Integer(), nullable=False),
        sa.Column("lead_opportunity_score", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("business_id"),
    )
    op.create_index(op.f("ix_lead_scores_business_id"), "lead_scores", ["business_id"], unique=False)

    op.create_table(
        "exports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_exports_job_id"), "exports", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_exports_job_id"), table_name="exports")
    op.drop_table("exports")
    op.drop_index(op.f("ix_lead_scores_business_id"), table_name="lead_scores")
    op.drop_table("lead_scores")
    op.drop_index(op.f("ix_emails_address"), table_name="emails")
    op.drop_index(op.f("ix_emails_business_id"), table_name="emails")
    op.drop_table("emails")
    op.drop_index(op.f("ix_social_accounts_platform"), table_name="social_accounts")
    op.drop_index(op.f("ix_social_accounts_business_id"), table_name="social_accounts")
    op.drop_table("social_accounts")
    op.drop_table("websites")
    op.drop_index(op.f("ix_businesses_google_maps_url"), table_name="businesses")
    op.drop_index(op.f("ix_businesses_name"), table_name="businesses")
    op.drop_index(op.f("ix_businesses_job_id"), table_name="businesses")
    op.drop_table("businesses")
    op.drop_index(op.f("ix_jobs_location"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_industry"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_status"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_project_id"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_projects_location"), table_name="projects")
    op.drop_index(op.f("ix_projects_industry"), table_name="projects")
    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.drop_index(op.f("ix_projects_user_id"), table_name="projects")
    op.drop_table("projects")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
