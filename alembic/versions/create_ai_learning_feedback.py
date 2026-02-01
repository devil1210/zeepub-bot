"""create ai_learning_feedback table

Revision ID: create_ai_learning_feedback
Revises: create_translators_groups_table
Create Date: 2026-01-25 19:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "create_ai_learning_feedback"
down_revision = "create_translators_groups_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_learning_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("series_hash", sa.String(length=64), nullable=False),
        sa.Column("original_name", sa.Text(), nullable=False),
        sa.Column("proposed_name", sa.Text(), nullable=False),
        sa.Column("final_name", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False
        ),  # 'accepted', 'rejected', 'edited', 'manual'
        sa.Column("ai_reason", sa.Text(), nullable=True),
        sa.Column("user_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_ai_learning_series_hash", "ai_learning_feedback", ["series_hash"]
    )


def downgrade():
    op.drop_table("ai_learning_feedback")
