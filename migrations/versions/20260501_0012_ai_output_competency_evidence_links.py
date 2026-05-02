"""add ai output competency evidence links

Revision ID: 20260501_0012
Revises: 20260428_0011
Create Date: 2026-05-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260501_0012"
down_revision: str | None = "20260428_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_output_competency_evidence_links",
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("ai_output_id", sa.Integer(), nullable=False),
        sa.Column("competency_evidence_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("artefact_id", sa.Integer(), nullable=True),
        sa.Column("output_type", sa.String(length=100), nullable=False),
        sa.Column("draft_kind", sa.String(length=100), nullable=True),
        sa.Column("use_intent", sa.String(length=100), nullable=False),
        sa.Column("user_selected", sa.Boolean(), nullable=False),
        sa.Column("evidence_uuid", sa.String(length=36), nullable=False),
        sa.Column("evidence_title", sa.String(length=200), nullable=False),
        sa.Column("evidence_competency", sa.String(length=200), nullable=True),
        sa.Column("evidence_strength", sa.String(length=32), nullable=True),
        sa.Column("evidence_result_action_snippet", sa.Text(), nullable=True),
        sa.Column("latest_star_shaping_output_id", sa.Integer(), nullable=True),
        sa.Column("evidence_snapshot", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ai_output_id"], ["ai_outputs.id"]),
        sa.ForeignKeyConstraint(["artefact_id"], ["artefacts.id"]),
        sa.ForeignKeyConstraint(["competency_evidence_id"], ["competency_evidence.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["latest_star_shaping_output_id"], ["ai_outputs.id"]),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_output_competency_evidence_links_ai_output_id"),
        "ai_output_competency_evidence_links",
        ["ai_output_id"],
    )
    op.create_index(
        op.f("ix_ai_output_competency_evidence_links_artefact_id"),
        "ai_output_competency_evidence_links",
        ["artefact_id"],
    )
    op.create_index(
        op.f("ix_ai_output_competency_evidence_links_competency_evidence_id"),
        "ai_output_competency_evidence_links",
        ["competency_evidence_id"],
    )
    op.create_index(
        op.f("ix_ai_output_competency_evidence_links_draft_kind"),
        "ai_output_competency_evidence_links",
        ["draft_kind"],
    )
    op.create_index(
        op.f("ix_ai_output_competency_evidence_links_evidence_uuid"),
        "ai_output_competency_evidence_links",
        ["evidence_uuid"],
    )
    op.create_index(
        op.f("ix_ai_output_competency_evidence_links_job_id"),
        "ai_output_competency_evidence_links",
        ["job_id"],
    )
    op.create_index(
        op.f("ix_ai_output_competency_evidence_links_latest_star_shaping_output_id"),
        "ai_output_competency_evidence_links",
        ["latest_star_shaping_output_id"],
    )
    op.create_index(
        op.f("ix_ai_output_competency_evidence_links_output_type"),
        "ai_output_competency_evidence_links",
        ["output_type"],
    )
    op.create_index(
        op.f("ix_ai_output_competency_evidence_links_owner_user_id"),
        "ai_output_competency_evidence_links",
        ["owner_user_id"],
    )
    op.create_index(
        op.f("ix_ai_output_competency_evidence_links_use_intent"),
        "ai_output_competency_evidence_links",
        ["use_intent"],
    )
    op.create_index(
        op.f("ix_ai_output_competency_evidence_links_uuid"),
        "ai_output_competency_evidence_links",
        ["uuid"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_output_competency_evidence_links_uuid"), table_name="ai_output_competency_evidence_links")
    op.drop_index(op.f("ix_ai_output_competency_evidence_links_use_intent"), table_name="ai_output_competency_evidence_links")
    op.drop_index(op.f("ix_ai_output_competency_evidence_links_owner_user_id"), table_name="ai_output_competency_evidence_links")
    op.drop_index(op.f("ix_ai_output_competency_evidence_links_output_type"), table_name="ai_output_competency_evidence_links")
    op.drop_index(op.f("ix_ai_output_competency_evidence_links_latest_star_shaping_output_id"), table_name="ai_output_competency_evidence_links")
    op.drop_index(op.f("ix_ai_output_competency_evidence_links_job_id"), table_name="ai_output_competency_evidence_links")
    op.drop_index(op.f("ix_ai_output_competency_evidence_links_evidence_uuid"), table_name="ai_output_competency_evidence_links")
    op.drop_index(op.f("ix_ai_output_competency_evidence_links_draft_kind"), table_name="ai_output_competency_evidence_links")
    op.drop_index(op.f("ix_ai_output_competency_evidence_links_competency_evidence_id"), table_name="ai_output_competency_evidence_links")
    op.drop_index(op.f("ix_ai_output_competency_evidence_links_artefact_id"), table_name="ai_output_competency_evidence_links")
    op.drop_index(op.f("ix_ai_output_competency_evidence_links_ai_output_id"), table_name="ai_output_competency_evidence_links")
    op.drop_table("ai_output_competency_evidence_links")
