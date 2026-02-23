"""Convert PostgreSQL native enums to VARCHAR(50)

Revision ID: 002
Revises: 001
Create Date: 2026-02-23

"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert enum columns to varchar (using ::text for existing enum values)
    op.execute("ALTER TABLE transfers ALTER COLUMN status TYPE VARCHAR(50) USING status::text")
    op.execute("ALTER TABLE transfers ALTER COLUMN priority TYPE VARCHAR(50) USING priority::text")
    op.execute("ALTER TABLE transfers ALTER COLUMN category TYPE VARCHAR(50) USING category::text")
    op.execute("ALTER TABLE approvals ALTER COLUMN status TYPE VARCHAR(50) USING status::text")
    op.execute("ALTER TABLE approvals ALTER COLUMN required_role TYPE VARCHAR(50) USING required_role::text")
    op.execute("ALTER TABLE notifications ALTER COLUMN type TYPE VARCHAR(50) USING type::text")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50) USING role::text")

    # Lowercase existing values to match Python enum values
    op.execute("UPDATE transfers SET status = LOWER(status)")
    op.execute("UPDATE transfers SET priority = LOWER(priority)")
    op.execute("UPDATE transfers SET category = LOWER(category) WHERE category IS NOT NULL")
    op.execute("UPDATE approvals SET status = LOWER(status)")
    op.execute("UPDATE approvals SET required_role = LOWER(required_role)")
    op.execute("UPDATE notifications SET type = LOWER(type)")
    op.execute("UPDATE users SET role = LOWER(role)")

    # Drop the old PostgreSQL enum types
    op.execute("DROP TYPE IF EXISTS transferstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS transferpriority CASCADE")
    op.execute("DROP TYPE IF EXISTS transfercategory CASCADE")
    op.execute("DROP TYPE IF EXISTS approvalstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS notificationtype CASCADE")
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")


def downgrade() -> None:
    # No downgrade — enum types are dropped; recreating them would require known values
    pass
