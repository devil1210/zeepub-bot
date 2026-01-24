"""add user levels system

Revision ID: add_user_levels
Revises: 58670adf5f59
Create Date: 2026-01-08 20:10:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_user_levels'
down_revision = '58670adf5f59'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_levels table
    op.create_table(
        'user_levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('has_mini_app_access', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Insert default levels
    op.execute("""
        INSERT INTO user_levels (id, name, priority, color, has_mini_app_access) VALUES
        (1, 'Administrador', 100, '#FF6B6B', TRUE),
        (2, 'Staff', 90, '#4ECDC4', TRUE),
        (3, 'Premium', 80, '#FFD93D', TRUE),
        (4, 'VIP', 70, '#A8E6CF', TRUE),
        (5, 'Patrocinador', 60, '#C7CEEA', TRUE),
        (6, 'Lector', 50, '#B4B4B4', FALSE)
    """)

    # Add level_id column to users table
    op.add_column('users', sa.Column('level_id', sa.Integer(), nullable=True))

    # Create foreign key
    op.create_foreign_key('fk_users_level_id', 'users', 'user_levels', ['level_id'], ['id'])

    # Migrate existing users to new level system
    op.execute("""
        UPDATE users SET level_id = CASE
            WHEN role = 'admin' THEN 1
            WHEN role = 'staff' THEN 2
            WHEN role = 'premium' THEN 3
            WHEN role = 'vip' THEN 4
            WHEN role = 'white' THEN 5
            ELSE 6
        END
    """)

    # Create admins table if it doesn't exist
    op.create_table(
        'admins',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('granted_by', sa.BigInteger(), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('user_id')
    )

    # Add settings and total_downloads columns if they don't exist
    try:
        op.add_column("users", sa.Column("settings", sa.Text(), nullable=True))
    except Exception:
        pass  # Column might already exist

    try:
        op.add_column(
            "users",
            sa.Column(
                "total_downloads", sa.Integer(), nullable=False, server_default="0"
            ),
        )
    except Exception:
        pass  # Column might already exist


def downgrade():
    op.drop_constraint('fk_users_level_id', 'users', type_='foreignkey')
    op.drop_column('users', 'level_id')
    op.drop_table('user_levels')
    op.drop_table('admins')
    op.drop_column('users', 'settings')
    op.drop_column('users', 'total_downloads')
