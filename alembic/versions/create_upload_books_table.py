"""create upload_books table

Revision ID: create_upload_books_table
Revises: add_user_levels
Create Date: 2026-01-23 06:20:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'create_upload_books_table'
down_revision = 'add_user_levels'
branch_labels = None
depends_on = None


def upgrade():
    # Create upload_books table
    op.create_table(
        'upload_books',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('original_filename', sa.String(512), nullable=False),
        sa.Column('temp_filepath', sa.String(1024), nullable=False),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('series', sa.String(255)),
        sa.Column('volume', sa.Float()),
        sa.Column('author', sa.String(255)),
        sa.Column('book_type', sa.String(100)),
        sa.Column('translator', sa.String(255)),
        sa.Column('layout_by', sa.String(255)),
        sa.Column('language', sa.String(10), server_default='es'),
        sa.Column('book_hash', sa.String(64), nullable=False),
        sa.Column('series_hash', sa.String(64)),
        sa.Column('identity_match', sa.String(10), server_default='False'),
        sa.Column('path_collision', sa.String(10), server_default='False'),
        sa.Column('processed', sa.String(10), server_default='False'),
        sa.Column('upload_metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for performance
    op.create_index('ix_upload_books_book_hash', 'upload_books', ['book_hash'])
    op.create_index('ix_upload_books_telegram_id', 'upload_books', ['telegram_id'])
    op.create_index('ix_upload_books_identity_match', 'upload_books', ['identity_match'])


def downgrade():
    op.drop_table('upload_books')
