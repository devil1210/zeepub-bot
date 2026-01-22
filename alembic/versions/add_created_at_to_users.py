"""add created_at column to users table

Revision ID: add_created_at_to_users
Revises: 58670adf5f59
Create Date: 2026-01-22 18:42:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_created_at_to_users'
down_revision = '58670adf5f59'
branch_labels = None
depends_on = None


def upgrade():
    # Add created_at column to users table if it doesn't exist
    # For PostgreSQL
    try:
        op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))
        # Update existing records with current timestamp
        op.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
        # Make column not nullable after updating existing records
        op.alter_column('users', 'created_at', nullable=False)
    except Exception as e:
        # Column might already exist, log and continue
        print(f"Column created_at might already exist: {e}")


def downgrade():
    # Remove created_at column from users table
    try:
        op.drop_column('users', 'created_at')
    except Exception as e:
        # Column might not exist, log and continue
        print(f"Could not drop created_at column: {e}")
