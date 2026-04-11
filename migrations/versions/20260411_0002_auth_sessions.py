"""add auth sessions

Revision ID: 20260411_0002
Revises: 20260411_0001
Create Date: 2026-04-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260411_0002"
down_revision: str | None = "20260411_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_hash", sa.String(length=64), nullable=False),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=100), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("session_hash"),
    )
    op.create_index(op.f("ix_auth_sessions_session_hash"), "auth_sessions", ["session_hash"], unique=True)
    op.create_index(op.f("ix_auth_sessions_user_id"), "auth_sessions", ["user_id"])
    op.create_index(op.f("ix_auth_sessions_uuid"), "auth_sessions", ["uuid"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_auth_sessions_uuid"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_user_id"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_session_hash"), table_name="auth_sessions")
    op.drop_table("auth_sessions")
