"""add nickname to users

Revision ID: 58670adf5f59
Revises: 0002
Create Date: 2024-12-16 13:12:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "58670adf5f59"
down_revision = "0002_published_books"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("telegram_id", sa.BigInteger(), primary_key=True),
            sa.Column("role", sa.Text(), nullable=True),
            sa.Column("added_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("custom_status", sa.Text(), nullable=True),
            sa.Column("created_by", sa.BigInteger(), nullable=True),
            sa.Column("nickname", sa.Text(), nullable=True),
        )
    else:
        columns = [c["name"] for c in inspector.get_columns("users")]
        if "nickname" not in columns:
            op.add_column("users", sa.Column("nickname", sa.Text(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if inspector.has_table("users"):
        columns = [c["name"] for c in inspector.get_columns("users")]
        if "nickname" in columns:
            op.drop_column("users", "nickname")
