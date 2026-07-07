"""add saved_searches table

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-07
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=False),
        sa.Column("keywords", sa.String(512), nullable=True),
        sa.Column("sources", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("filters", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("saved_searches")
