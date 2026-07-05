"""increase address length

Revision ID: 0002_increase_address_length
Revises: 0001_initial_schema
Create Date: 2026-07-06 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_increase_address_length"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "businesses",
        "address",
        existing_type=sa.String(length=512),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "businesses",
        "address",
        existing_type=sa.Text(),
        type_=sa.String(length=512),
        existing_nullable=True,
    )
