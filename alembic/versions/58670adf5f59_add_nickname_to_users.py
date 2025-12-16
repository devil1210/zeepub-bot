"""add nickname to users

Revision ID: 58670adf5f59
Revises: 0002
Create Date: 2024-12-16 13:12:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '58670adf5f59'
down_revision = '0002_published_books'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('nickname', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'nickname')
