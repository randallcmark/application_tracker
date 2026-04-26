"""add competency evidence

Revision ID: 20260426_0010
Revises: 20260422_0009
Create Date: 2026-04-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260426_0010"
down_revision: str | None = "20260422_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "competency_evidence",
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("competency", sa.String(length=200), nullable=True),
        sa.Column("situation", sa.Text(), nullable=True),
        sa.Column("task", sa.Text(), nullable=True),
        sa.Column("action", sa.Text(), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("evidence_notes", sa.Text(), nullable=True),
        sa.Column("strength", sa.String(length=32), nullable=False),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("source_kind", sa.String(length=50), nullable=True),
        sa.Column("source_job_id", sa.Integer(), nullable=True),
        sa.Column("source_artefact_id", sa.Integer(), nullable=True),
        sa.Column("source_ai_output_id", sa.Integer(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_ai_output_id"], ["ai_outputs.id"]),
        sa.ForeignKeyConstraint(["source_artefact_id"], ["artefacts.id"]),
        sa.ForeignKeyConstraint(["source_job_id"], ["jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_competency_evidence_owner_user_id"), "competency_evidence", ["owner_user_id"])
    op.create_index(op.f("ix_competency_evidence_source_ai_output_id"), "competency_evidence", ["source_ai_output_id"])
    op.create_index(op.f("ix_competency_evidence_source_artefact_id"), "competency_evidence", ["source_artefact_id"])
    op.create_index(op.f("ix_competency_evidence_source_job_id"), "competency_evidence", ["source_job_id"])
    op.create_index(op.f("ix_competency_evidence_uuid"), "competency_evidence", ["uuid"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_competency_evidence_uuid"), table_name="competency_evidence")
    op.drop_index(op.f("ix_competency_evidence_source_job_id"), table_name="competency_evidence")
    op.drop_index(op.f("ix_competency_evidence_source_artefact_id"), table_name="competency_evidence")
    op.drop_index(op.f("ix_competency_evidence_source_ai_output_id"), table_name="competency_evidence")
    op.drop_index(op.f("ix_competency_evidence_owner_user_id"), table_name="competency_evidence")
    op.drop_table("competency_evidence")
