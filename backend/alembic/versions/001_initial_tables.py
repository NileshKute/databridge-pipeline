"""Initial tables

Revision ID: 001
Revises:
Create Date: 2026-02-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

userrole_enum = sa.Enum(
    "artist", "team_lead", "supervisor", "line_producer",
    "data_team", "it_team", "admin",
    name="userrole",
)
transferstatus_enum = sa.Enum(
    "uploaded", "pending_team_lead", "pending_supervisor", "pending_line_producer",
    "approved", "scanning", "scan_passed", "scan_failed", "copying",
    "ready_for_transfer", "transferring", "verifying", "transferred",
    "rejected", "cancelled",
    name="transferstatus",
)
transferpriority_enum = sa.Enum(
    "low", "normal", "high", "urgent",
    name="transferpriority",
)
transfercategory_enum = sa.Enum(
    "vfx_assets", "animation", "textures", "lighting", "compositing",
    "audio", "editorial", "matchmove", "fx", "other",
    name="transfercategory",
)
approvalstatus_enum = sa.Enum(
    "pending", "approved", "rejected", "skipped",
    name="approvalstatus",
)
notificationtype_enum = sa.Enum(
    "upload", "approval_required", "approved", "rejected",
    "scan_started", "scan_complete", "scan_failed",
    "transfer_started", "transfer_complete", "transfer_failed",
    "system",
    name="notificationtype",
)


def upgrade() -> None:
    # Create enums first (PostgreSQL-specific)
    userrole_enum.create(op.get_bind(), checkfirst=True)
    transferstatus_enum.create(op.get_bind(), checkfirst=True)
    transferpriority_enum.create(op.get_bind(), checkfirst=True)
    transfercategory_enum.create(op.get_bind(), checkfirst=True)
    approvalstatus_enum.create(op.get_bind(), checkfirst=True)
    notificationtype_enum.create(op.get_bind(), checkfirst=True)

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", userrole_enum, nullable=False, server_default="artist"),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("ldap_dn", sa.String(500), nullable=True),
        sa.Column("ldap_groups", sa.Text(), nullable=True),
        sa.Column("shotgrid_user_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # --- transfers ---
    op.create_table(
        "transfers",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("reference", sa.String(20), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", transfercategory_enum, nullable=True),
        sa.Column("status", transferstatus_enum, nullable=False, server_default="uploaded"),
        sa.Column("priority", transferpriority_enum, nullable=False, server_default="normal"),
        sa.Column("artist_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("total_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("staging_path", sa.String(1000), nullable=True),
        sa.Column("production_path", sa.String(1000), nullable=True),
        sa.Column("shotgrid_project_id", sa.Integer(), nullable=True),
        sa.Column("shotgrid_entity_type", sa.String(50), nullable=True),
        sa.Column("shotgrid_entity_id", sa.Integer(), nullable=True),
        sa.Column("shotgrid_entity_name", sa.String(200), nullable=True),
        sa.Column("shotgrid_task_id", sa.Integer(), nullable=True),
        sa.Column("shotgrid_version_id", sa.Integer(), nullable=True),
        sa.Column("scan_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scan_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scan_result", JSON(), nullable=True),
        sa.Column("scan_passed", sa.Boolean(), nullable=True),
        sa.Column("transfer_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("transfer_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("transfer_verified", sa.Boolean(), nullable=True),
        sa.Column("transfer_method", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("tags", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_transfers_reference", "transfers", ["reference"], unique=True)
    op.create_index("ix_transfers_status", "transfers", ["status"])
    op.create_index("ix_transfers_artist_id", "transfers", ["artist_id"])

    # --- transfer_files ---
    op.create_table(
        "transfer_files",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("transfer_id", sa.Integer(), sa.ForeignKey("transfers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("original_path", sa.String(1000), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("checksum_verified", sa.Boolean(), nullable=True),
        sa.Column("virus_scan_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("virus_scan_detail", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_transfer_files_transfer_id", "transfer_files", ["transfer_id"])

    # --- approvals ---
    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("transfer_id", sa.Integer(), sa.ForeignKey("transfers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approver_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("required_role", userrole_enum, nullable=False),
        sa.Column("status", approvalstatus_enum, nullable=False, server_default="pending"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_approvals_transfer_id", "approvals", ["transfer_id"])

    # --- transfer_history ---
    op.create_table(
        "transfer_history",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("transfer_id", sa.Integer(), sa.ForeignKey("transfers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_transfer_history_transfer_id", "transfer_history", ["transfer_id"])

    # --- notifications ---
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("transfer_id", sa.Integer(), sa.ForeignKey("transfers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", notificationtype_enum, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("email_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("transfer_history")
    op.drop_table("approvals")
    op.drop_table("transfer_files")
    op.drop_table("transfers")
    op.drop_table("users")

    notificationtype_enum.drop(op.get_bind(), checkfirst=True)
    approvalstatus_enum.drop(op.get_bind(), checkfirst=True)
    transfercategory_enum.drop(op.get_bind(), checkfirst=True)
    transferpriority_enum.drop(op.get_bind(), checkfirst=True)
    transferstatus_enum.drop(op.get_bind(), checkfirst=True)
    userrole_enum.drop(op.get_bind(), checkfirst=True)
