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
    # Use batch_alter_table or check for existence for safety
    t_name = "series_metadata"

    # We use raw execution with check to avoid errors if some already exist in some environment
    conn = op.get_bind()
    columns_res = conn.execute(
        sa.text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t_name}'")
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
                op.create_index(op.f("ix_series_metadata_slug"), t_name, ["slug"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_series_metadata_slug"), table_name="series_metadata")
    op.drop_column("series_metadata", "demographics")
    op.drop_column("series_metadata", "tags")
    op.drop_column("series_metadata", "illustrator_jap")
    op.drop_column("series_metadata", "illustrator")
    op.drop_column("series_metadata", "author_jap")
    op.drop_column("series_metadata", "slug")
    op.drop_column("series_metadata", "series_english")
    op.drop_column("series_metadata", "series_spanish")
