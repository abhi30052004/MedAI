"""Add case insurance and reviewer assignment fields.

Revision ID: 8c4f1d2a9e71
Revises: b2ccc23b78e0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c4f1d2a9e71"
down_revision: Union[str, Sequence[str], None] = "b2ccc23b78e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("insurance_available", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("cases", sa.Column("insurance_provider", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("insurance_number", sa.String(), nullable=True))
    op.add_column("cases", sa.Column("assigned_insurance_reviewer", sa.Integer(), nullable=True))
    op.add_column("cases", sa.Column("doctor_review_reason", sa.Text(), nullable=True))
    op.add_column("cases", sa.Column("insurance_review_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_cases_assigned_insurance_reviewer_users",
        "cases", "users", ["assigned_insurance_reviewer"], ["id"],
    )
    op.alter_column("cases", "insurance_available", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_cases_assigned_insurance_reviewer_users", "cases", type_="foreignkey")
    op.drop_column("cases", "assigned_insurance_reviewer")
    op.drop_column("cases", "insurance_review_reason")
    op.drop_column("cases", "doctor_review_reason")
    op.drop_column("cases", "insurance_number")
    op.drop_column("cases", "insurance_provider")
    op.drop_column("cases", "insurance_available")
