"""Add shotgrid_sequence_id and shotgrid_sequence_name to transfers

Revision ID: 004
Revises: 003
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transfers",
        sa.Column("shotgrid_sequence_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "transfers",
        sa.Column("shotgrid_sequence_name", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transfers", "shotgrid_sequence_name")
    op.drop_column("transfers", "shotgrid_sequence_id")
