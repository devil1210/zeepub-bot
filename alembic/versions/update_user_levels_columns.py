"""update user levels columns

Revision ID: update_user_levels_columns
Revises: add_user_levels
Create Date: 2026-01-16 22:50:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "update_user_levels_columns"
down_revision = "add_user_levels"
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns to user_levels
    try:
        op.add_column("user_levels", sa.Column("daily_downloads", sa.Integer(), nullable=False, server_default="1"))
    except Exception: pass
    
    try:
        op.add_column("user_levels", sa.Column("early_access", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    except Exception: pass
    
    try:
        op.add_column("user_levels", sa.Column("custom_themes", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    except Exception: pass
    
    try:
        op.add_column("user_levels", sa.Column("price", sa.Float(), nullable=False, server_default="0.0"))
    except Exception: pass

    # Update default values for existing levels
    op.execute("UPDATE user_levels SET daily_downloads = -1, early_access = TRUE, custom_themes = TRUE, price = 0.0 WHERE id = 1") # Admin
    op.execute("UPDATE user_levels SET daily_downloads = -1, early_access = TRUE, custom_themes = TRUE, price = 0.0 WHERE id = 2") # Staff
    op.execute("UPDATE user_levels SET daily_downloads = 100, early_access = TRUE, custom_themes = TRUE, price = 5.0 WHERE id = 3") # Premium
    op.execute("UPDATE user_levels SET daily_downloads = 50, early_access = TRUE, custom_themes = FALSE, price = 2.0 WHERE id = 4") # VIP
    op.execute("UPDATE user_levels SET daily_downloads = 25, early_access = FALSE, custom_themes = FALSE, price = 1.0 WHERE id = 5") # Patrocinador
    op.execute("UPDATE user_levels SET daily_downloads = 1, early_access = FALSE, custom_themes = FALSE, price = 0.0 WHERE id = 6") # Lector


def downgrade():
    op.drop_column("user_levels", "price")
    op.drop_column("user_levels", "custom_themes")
    op.drop_column("user_levels", "early_access")
    op.drop_column("user_levels", "daily_downloads")
