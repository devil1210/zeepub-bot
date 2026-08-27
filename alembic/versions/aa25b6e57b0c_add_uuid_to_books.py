"""add uuid to books

Revision ID: aa25b6e57b0c
Revises: merge_heads_2026
Create Date: 2026-06-01 13:15:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "aa25b6e57b0c"
down_revision = "fix_series_metadata_vps"
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columna uuid a la tabla books si la tabla existe
    conn = op.get_bind()
    tables_res = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'books'"
        )
    ).fetchone()

    if tables_res:
        columns_res = conn.execute(
            sa.text(
                "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'books'"
            )
        )
        existing_cols = [row[0] for row in columns_res]
        if "uuid" not in existing_cols:
            op.add_column(
                "books", sa.Column("uuid", sa.String(length=255), nullable=True)
            )
            op.create_index("ix_books_uuid", "books", ["uuid"])


def downgrade():
    conn = op.get_bind()
    tables_res = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'books'"
        )
    ).fetchone()
    if tables_res:
        try:
            op.drop_index("ix_books_uuid", table_name="books")
        except Exception:
            pass
        try:
            op.drop_column("books", "uuid")
        except Exception:
            pass
