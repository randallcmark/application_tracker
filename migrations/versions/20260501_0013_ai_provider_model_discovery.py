"""add ai provider model discovery fields

Revision ID: 20260501_0013
Revises: 20260501_0012
Create Date: 2026-05-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260501_0013"
down_revision: str | None = "20260501_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ai_provider_settings", sa.Column("discovered_models", sa.JSON(), nullable=True))
    op.add_column("ai_provider_settings", sa.Column("model_discovery_status", sa.String(length=50), nullable=True))
    op.add_column("ai_provider_settings", sa.Column("model_discovery_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_provider_settings", "model_discovery_error")
    op.drop_column("ai_provider_settings", "model_discovery_status")
    op.drop_column("ai_provider_settings", "discovered_models")
