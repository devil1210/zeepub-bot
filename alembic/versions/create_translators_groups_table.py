"""create translators_groups table and populate

Revision ID: create_translators_groups_table
Revises: create_upload_books_table
Create Date: 2026-01-25 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "create_translators_groups_table"
down_revision = "create_upload_books_table"
branch_labels = None
depends_on = None


def upgrade():
    # Create table
    op.create_table(
        "translators_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("siglas", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "siglas", name="uq_translators_groups_name_siglas"),
    )

    # Populate data from local_books
    # Extract acronyms from brackets in filename
    # Postgres substring format: substring(string from pattern)
    op.execute(r"""
        INSERT INTO translators_groups (name, siglas)
        SELECT DISTINCT 
            publisher, 
            substring(filename from '\[(.*?)\]')
        FROM local_books
        WHERE 
            publisher IS NOT NULL 
            AND filename ~ '\[.*?\]'
        ON CONFLICT (name, siglas) DO NOTHING
    """)


def downgrade():
    op.drop_table("translators_groups")
