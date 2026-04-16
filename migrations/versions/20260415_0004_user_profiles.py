"""add user job search profiles

Revision ID: 20260415_0004
Revises: 20260411_0003
Create Date: 2026-04-15
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260415_0004"
down_revision: str | None = "20260411_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def base_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        *base_columns(),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("target_roles", sa.Text(), nullable=True),
        sa.Column("target_locations", sa.Text(), nullable=True),
        sa.Column("remote_preference", sa.String(length=100), nullable=True),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_currency", sa.String(length=3), nullable=True),
        sa.Column("preferred_industries", sa.Text(), nullable=True),
        sa.Column("excluded_industries", sa.Text(), nullable=True),
        sa.Column("constraints", sa.Text(), nullable=True),
        sa.Column("urgency", sa.String(length=100), nullable=True),
        sa.Column("positioning_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.UniqueConstraint("owner_user_id"),
    )
    op.create_index(op.f("ix_user_profiles_uuid"), "user_profiles", ["uuid"], unique=True)
    op.create_index(op.f("ix_user_profiles_owner_user_id"), "user_profiles", ["owner_user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_profiles_owner_user_id"), table_name="user_profiles")
    op.drop_index(op.f("ix_user_profiles_uuid"), table_name="user_profiles")
    op.drop_table("user_profiles")
