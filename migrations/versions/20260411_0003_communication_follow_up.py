"""add communication follow up timestamp

Revision ID: 20260411_0003
Revises: 20260411_0002
Create Date: 2026-04-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260411_0003"
down_revision: str | None = "20260411_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("communications", sa.Column("follow_up_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_communications_follow_up_at"), "communications", ["follow_up_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_communications_follow_up_at"), table_name="communications")
    op.drop_column("communications", "follow_up_at")
