"""Add file_category to transfer_files

Revision ID: 003
Revises: 002
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transfer_files",
        sa.Column("file_category", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transfer_files", "file_category")
