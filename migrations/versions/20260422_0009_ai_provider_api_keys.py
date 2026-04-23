"""add encrypted ai provider api keys

Revision ID: 20260422_0009
Revises: 20260418_0008
Create Date: 2026-04-22
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260422_0009"
down_revision: str | None = "20260418_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ai_provider_settings", sa.Column("api_key_encrypted", sa.Text(), nullable=True))
    op.add_column("ai_provider_settings", sa.Column("api_key_hint", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_provider_settings", "api_key_hint")
    op.drop_column("ai_provider_settings", "api_key_encrypted")
