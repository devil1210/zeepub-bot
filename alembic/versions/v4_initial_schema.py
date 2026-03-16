"""v4 initial schema

Revision ID: v4_initial_schema
Revises: merge_heads_2026
Create Date: 2026-03-16 03:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "v4_initial_schema"
down_revision = "merge_heads_2026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. library_sources
    op.create_table(
        "library_sources",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("last_scanned", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 2. series
    op.create_table(
        "series",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.Column("title_raw", sa.String(length=512), nullable=False),
        sa.Column("title_spanish", sa.String(length=512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="reading", nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["library_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_series_hash", "series", ["hash"])

    # 3. books
    op.create_table(
        "books",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.Column("series_id", sa.UUID(), nullable=False),
        sa.Column("volume_number", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("extension", sa.String(length=10), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["series_id"], ["series.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_books_hash", "books", ["hash"])

    # 4. users migration (adapt existing)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if inspector.has_table("users"):
        columns = [c["name"] for c in inspector.get_columns("users")]

        # Rename telegram_id to id if it exists
        if "telegram_id" in columns and "id" not in columns:
            op.alter_column("users", "telegram_id", new_column_name="id")

        # Add new V4 columns
        if "username" not in columns:
            op.add_column("users", sa.Column("username", sa.String(length=255), nullable=True))
        if "level_id" not in columns:
            op.add_column("users", sa.Column("level_id", sa.UUID(), nullable=True))
        if "ui_config" not in columns:
            op.add_column("users", sa.Column("ui_config", sa.JSON(), nullable=True))
    else:
        op.create_table(
            "users",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column("username", sa.String(length=255), nullable=True),
            sa.Column("role", sa.String(length=50), server_default="member", nullable=False),
            sa.Column("level_id", sa.UUID(), nullable=True),
            sa.Column("ui_config", sa.JSON(), nullable=True),
            sa.Column("added_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )


def downgrade() -> None:
    op.drop_table("books")
    op.drop_table("series")
    op.drop_table("library_sources")
    # For users, we don't drop since it might have existed before V4
    # But we can undo the V4 specific changes if needed.
    op.drop_column("users", "ui_config")
    op.drop_column("users", "level_id")
    op.drop_column("users", "username")
    # Note: telegram_id rename is risky to undo without context, omitting.
