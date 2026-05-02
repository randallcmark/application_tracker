"""add artefact follow up timestamp

Revision ID: 20260428_0011
Revises: 20260426_0010
Create Date: 2026-04-28
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260428_0011"
down_revision: str | None = "20260426_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("artefacts", sa.Column("follow_up_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_artefacts_follow_up_at"), "artefacts", ["follow_up_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_artefacts_follow_up_at"), table_name="artefacts")
    op.drop_column("artefacts", "follow_up_at")
