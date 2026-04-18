"""add job intake metadata

Revision ID: 20260417_0005
Revises: 20260415_0004
Create Date: 2026-04-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260417_0005"
down_revision: str | None = "20260415_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("intake_source", sa.String(length=100), nullable=False, server_default="manual"),
    )
    op.add_column(
        "jobs",
        sa.Column("intake_confidence", sa.String(length=50), nullable=False, server_default="high"),
    )
    op.add_column(
        "jobs",
        sa.Column("intake_state", sa.String(length=50), nullable=False, server_default="accepted"),
    )
    op.create_index(op.f("ix_jobs_intake_source"), "jobs", ["intake_source"])
    op.create_index(op.f("ix_jobs_intake_confidence"), "jobs", ["intake_confidence"])
    op.create_index(op.f("ix_jobs_intake_state"), "jobs", ["intake_state"])


def downgrade() -> None:
    op.drop_index(op.f("ix_jobs_intake_state"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_intake_confidence"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_intake_source"), table_name="jobs")
    op.drop_column("jobs", "intake_state")
    op.drop_column("jobs", "intake_confidence")
    op.drop_column("jobs", "intake_source")
