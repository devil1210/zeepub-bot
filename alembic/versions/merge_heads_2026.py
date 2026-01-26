"""merge heads

Revision ID: merge_heads_2026
Revises: add_created_at_to_users, create_ai_learning_feedback, update_user_levels_columns
Create Date: 2026-01-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_heads_2026'
down_revision = ('add_created_at_to_users', 'create_ai_learning_feedback', 'update_user_levels_columns')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
