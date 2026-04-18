"""add email intakes

Revision ID: 20260418_0006
Revises: 20260417_0005
Create Date: 2026-04-18
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260418_0006"
down_revision: str | None = "20260417_0005"
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
        "email_intakes",
        *base_columns(),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=True),
        sa.Column("sender", sa.String(length=500), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column(
            "source_provider",
            sa.String(length=100),
            nullable=False,
            server_default="manual_paste",
        ),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_email_intakes_uuid"), "email_intakes", ["uuid"], unique=True)
    op.create_index(op.f("ix_email_intakes_owner_user_id"), "email_intakes", ["owner_user_id"])
    op.create_index(op.f("ix_email_intakes_source_provider"), "email_intakes", ["source_provider"])
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(
            sa.Column("email_intake_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_jobs_email_intake_id_email_intakes",
            "email_intakes",
            ["email_intake_id"],
            ["id"],
        )
        batch_op.create_index(op.f("ix_jobs_email_intake_id"), ["email_intake_id"])


def downgrade() -> None:
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_index(op.f("ix_jobs_email_intake_id"))
        batch_op.drop_constraint("fk_jobs_email_intake_id_email_intakes", type_="foreignkey")
        batch_op.drop_column("email_intake_id")
    op.drop_index(op.f("ix_email_intakes_source_provider"), table_name="email_intakes")
    op.drop_index(op.f("ix_email_intakes_owner_user_id"), table_name="email_intakes")
    op.drop_index(op.f("ix_email_intakes_uuid"), table_name="email_intakes")
    op.drop_table("email_intakes")
