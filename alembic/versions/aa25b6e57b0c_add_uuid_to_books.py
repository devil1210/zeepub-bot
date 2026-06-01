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
    # Agregar columna uuid a la tabla books
    op.add_column("books", sa.Column("uuid", sa.String(length=255), nullable=True))
    # Crear índice en books(uuid) para búsquedas ultrarrápidas
    op.create_index("ix_books_uuid", "books", ["uuid"])


def downgrade():
    # Eliminar índice y columna
    op.drop_index("ix_books_uuid", table_name="books")
    op.drop_column("books", "uuid")
