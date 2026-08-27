"""fix series_metadata missing columns for vps
Revision ID: fix_series_metadata_vps
Revises: merge_heads_2026
Create Date: 2026-03-06 00:45:00.000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "fix_series_metadata_vps"
down_revision = "merge_heads_2026"
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to series_metadata if they don't exist
    t_name = "series_metadata"
    conn = op.get_bind()

    tables_res = conn.execute(
        sa.text(
            f"SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{t_name}'"
        )
    ).fetchone()

    if not tables_res:
        # Create table if it doesn't exist (e.g. in fresh CI test databases)
        op.create_table(
            t_name,
            sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
            sa.Column("series_hash", sa.String(64), unique=True, index=True),
            sa.Column("series_name", sa.String(512)),
            sa.Column("series_spanish", sa.String(255)),
            sa.Column("series_english", sa.String(255)),
            sa.Column("slug", sa.String(512), index=True),
            sa.Column("author_jap", sa.String(255)),
            sa.Column("illustrator", sa.String(255)),
            sa.Column("illustrator_jap", sa.String(255)),
            sa.Column("tags", postgresql.JSONB(astext_type=sa.Text())),
            sa.Column("demographics", postgresql.JSONB(astext_type=sa.Text())),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
        return

    columns_res = conn.execute(
        sa.text(
            f"SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '{t_name}'"
        )
    )
    existing_cols = [row[0] for row in columns_res]

    new_cols = [
        ("series_spanish", sa.String(255)),
        ("series_english", sa.String(255)),
        ("slug", sa.String(512)),
        ("author_jap", sa.String(255)),
        ("illustrator", sa.String(255)),
        ("illustrator_jap", sa.String(255)),
        ("tags", postgresql.JSONB(astext_type=sa.Text())),
        ("demographics", postgresql.JSONB(astext_type=sa.Text())),
    ]

    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            op.add_column(t_name, sa.Column(col_name, col_type))
            if col_name == "slug":
                op.create_index(
                    op.f("ix_series_metadata_slug"), t_name, ["slug"], unique=False
                )


def downgrade():
    conn = op.get_bind()
    tables_res = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'series_metadata'"
        )
    ).fetchone()
    if tables_res:
        try:
            op.drop_index(op.f("ix_series_metadata_slug"), table_name="series_metadata")
        except Exception:
            pass
        for c in [
            "demographics",
            "tags",
            "illustrator_jap",
            "illustrator",
            "author_jap",
            "slug",
            "series_english",
            "series_spanish",
        ]:
            try:
                op.drop_column("series_metadata", c)
            except Exception:
                pass
