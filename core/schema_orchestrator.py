import asyncio
import logging

from sqlalchemy import text

from core.db_manager_pg import pg_manager
from models.base import Base
from models.library_models import (
    LibrarySource,
)

# Import custom models so they are registered in Base.metadata
from models.user_models import UserLevel

logger = logging.getLogger(__name__)


class SchemaOrchestrator:
    """
    Responsibilities:
    1. Ensure Database Tables exist (Auto-Migration for initialization).
    2. Verify Schema integrity (check for missing columns).
    3. (Future) Sync with Supabase remote schema.
    """

    @staticmethod
    async def initialize_schema():
        """Creates tables if they don't exist in the Postgres DB."""
        logger.info("Initializing Database Schema...")

        # Ensure connection is ready
        await pg_manager.initialize()

        try:
            # Debug: Log tables in metadata
            table_names = list(Base.metadata.tables.keys())
            logger.info(f"Metadata contains {len(table_names)} tables: {', '.join(table_names)}")

            async with pg_manager.engine.begin() as conn:
                # Create all tables defined in SQLAlchemy models
                # This only creates tables that don't exist; it won't update existing frames
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Base tables creation/verification completed.")

                # Auto-Migration for UserLevel (Add missing columns to existing table)
                await SchemaOrchestrator._check_and_add_column("user_levels", "color", "VARCHAR(20) DEFAULT '#607D8B'")
                await SchemaOrchestrator._check_and_add_column("user_levels", "ui_font_size", "INTEGER DEFAULT 14")
                await SchemaOrchestrator._check_and_add_column("user_levels", "ui_glass_blur", "INTEGER DEFAULT 12")
                await SchemaOrchestrator._check_and_add_column("user_levels", "ui_cover_width", "INTEGER DEFAULT 120")
                await SchemaOrchestrator._check_and_add_column("user_levels", "ui_accent_opacity", "INTEGER DEFAULT 20")
                await SchemaOrchestrator._check_and_add_column(
                    "user_levels", "panel_transparency", "INTEGER DEFAULT 60"
                )
                await SchemaOrchestrator._check_and_add_column(
                    "user_levels", "background_color", "VARCHAR(20) DEFAULT '#0f172a'"
                )
                await SchemaOrchestrator._check_and_add_column(
                    "user_levels", "card_color", "VARCHAR(20) DEFAULT '#1e293b'"
                )
                await SchemaOrchestrator._check_and_add_column(
                    "user_levels", "banner_content_offset", "INTEGER DEFAULT 0"
                )
                await SchemaOrchestrator._check_and_add_column("user_levels", "force_settings", "BOOLEAN DEFAULT FALSE")
                await SchemaOrchestrator._check_and_add_column("user_levels", "can_read", "BOOLEAN DEFAULT TRUE")
                await SchemaOrchestrator._check_and_add_column(
                    "user_levels", "has_library_access", "BOOLEAN DEFAULT TRUE"
                )
                await SchemaOrchestrator._check_and_add_column(
                    "user_levels", "can_request_books", "BOOLEAN DEFAULT TRUE"
                )
                await SchemaOrchestrator._check_and_add_column("user_levels", "early_access", "BOOLEAN DEFAULT FALSE")
                await SchemaOrchestrator._check_and_add_column("user_levels", "custom_themes", "BOOLEAN DEFAULT FALSE")
                await SchemaOrchestrator._check_and_add_column(
                    "user_levels", "show_recommendations", "BOOLEAN DEFAULT TRUE"
                )
                await SchemaOrchestrator._check_and_add_column("user_levels", "price", "DOUBLE PRECISION DEFAULT 0.0")

                # Auto-Migration for UserUISettings
                await SchemaOrchestrator._check_and_add_column("user_ui_settings", "font_size", "INTEGER")
                await SchemaOrchestrator._check_and_add_column("user_ui_settings", "nav_opacity", "INTEGER")
                await SchemaOrchestrator._check_and_add_column("user_ui_settings", "accent_opacity", "INTEGER")
                await SchemaOrchestrator._check_and_add_column("user_ui_settings", "show_recommendations", "BOOLEAN")
                await SchemaOrchestrator._check_and_add_column(
                    "user_ui_settings", "title_language", "VARCHAR(20) DEFAULT 'romaji'"
                )

                await SchemaOrchestrator._check_and_add_column(
                    "user_levels", "allow_theme_templates", "BOOLEAN DEFAULT FALSE"
                )
                await SchemaOrchestrator._check_and_add_column(
                    "user_levels", "can_upload_epub", "BOOLEAN DEFAULT FALSE"
                )

                # Auto-Migration for Users (Ensure created_at and email exists)
                await SchemaOrchestrator._check_and_add_column("users", "email", "VARCHAR(255) UNIQUE")
                await SchemaOrchestrator._check_and_add_column("users", "can_upload_epub", "BOOLEAN DEFAULT FALSE")
                await SchemaOrchestrator._check_and_add_column(
                    "users",
                    "updated_at",
                    "TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())",
                )
                await SchemaOrchestrator._check_and_add_column("users", "created_at", "TIMESTAMP DEFAULT NOW()")

                # Auto-Migration for Books
                await SchemaOrchestrator._check_and_add_column("books", "series_hash", "VARCHAR(255)")

                # Auto-Migration for Series (author_jap, illustrator_jap)
                await SchemaOrchestrator._check_and_add_column("series", "author_jap", "VARCHAR(255)")
                await SchemaOrchestrator._check_and_add_column("series", "illustrator_jap", "VARCHAR(255)")

                # IMPORTANT: Wait a bit for Postgres to stabilize metadata
                await asyncio.sleep(1)

                # Seed Initial Data
                await SchemaOrchestrator._seed_initial_data()

        except Exception as e:
            logger.critical(f"Failed to initialize schema: {e}")
            raise

    @staticmethod
    async def _seed_initial_data():
        """Populates the database with required initial data like User Levels."""
        from sqlalchemy import select

        # Max retries for seeding if table not visible yet
        for attempt in range(3):
            async with pg_manager.get_session() as session:
                try:
                    # 0. Check if table exists (asyncpg level)
                    table_check = text(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_levels')"
                    )
                    exists = (await session.execute(table_check)).scalar()
                    if not exists:
                        logger.warning(f"Attempt {attempt + 1}: user_levels table not visible. Retrying...")
                        await asyncio.sleep(2)
                        continue

                    # 1. Upsert default User Levels
                    logger.info("Seeding/Merging User Levels...")

                    levels = [
                        UserLevel(
                            id=1,
                            name="Administrador",
                            priority=100,
                            color="#FF5252",
                            daily_downloads=999,
                            early_access=True,
                            custom_themes=True,
                            ui_theme="dark",
                            can_read=True,
                            has_library_access=True,
                            can_request_books=True,
                            show_recommendations=True,
                        ),
                        UserLevel(
                            id=2,
                            name="Staff",
                            priority=90,
                            color="#7C4DFF",
                            daily_downloads=999,
                            early_access=True,
                            custom_themes=True,
                            ui_theme="dark",
                            can_read=True,
                            has_library_access=True,
                            can_request_books=True,
                            show_recommendations=True,
                        ),
                        UserLevel(
                            id=3,
                            name="Premium",
                            priority=50,
                            color="#FFD740",
                            daily_downloads=50,
                            early_access=False,
                            custom_themes=True,
                            ui_theme="dark",
                            can_read=True,
                            has_library_access=True,
                            can_request_books=True,
                            show_recommendations=True,
                        ),
                        UserLevel(
                            id=4,
                            name="VIP",
                            priority=40,
                            color="#69F0AE",
                            daily_downloads=20,
                            early_access=False,
                            custom_themes=True,
                            ui_theme="dark",
                            can_read=True,
                            has_library_access=True,
                            can_request_books=True,
                            show_recommendations=True,
                        ),
                        UserLevel(
                            id=5,
                            name="Patrocinador",
                            priority=20,
                            color="#E0E0E0",
                            daily_downloads=10,
                            early_access=False,
                            custom_themes=True,
                            ui_theme="dark",
                            can_read=True,
                            has_library_access=True,
                            can_request_books=True,
                            show_recommendations=True,
                        ),
                        UserLevel(
                            id=6,
                            name="Lector",
                            priority=10,
                            color="#607D8B",
                            daily_downloads=5,
                            early_access=False,
                            custom_themes=True,
                            ui_theme="dark",
                            can_read=True,
                            has_library_access=True,
                            can_request_books=True,
                            show_recommendations=True,
                        ),
                    ]

                    for lvl in levels:
                        await session.merge(lvl)

                    await session.commit()
                    logger.info("User Levels seeded successfully.")

                    # 2. Seed Default Library Source
                    if not (
                        await session.execute(
                            text(
                                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'library_sources')"
                            )
                        )
                    ).scalar():
                        return  # Should exist if metadata worked

                    stmt_source = select(LibrarySource).limit(1)
                    existing_source = (await session.execute(stmt_source)).scalar_one_or_none()
                    if not existing_source:
                        logger.info("Seeding default Library Source (/library)...")
                        default_source = LibrarySource(name="Principal", path="/library")
                        session.add(default_source)
                        await session.commit()

                    return  # Success!

                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} - Error seeding initial data: {e}")
                    await asyncio.sleep(2)

    @staticmethod
    async def _check_and_add_column(table_name: str, column_name: str, column_type: str):
        """Helper to add missing columns safely."""
        async with pg_manager.get_session() as session:
            try:
                # 1. Check if table exists first
                table_check = text(
                    f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')"
                )
                table_exists = (await session.execute(table_check)).scalar()

                if not table_exists:
                    logger.debug(f"Table '{table_name}' does not exist yet. Skipping column check for '{column_name}'.")
                    return

                # 2. Check if column exists
                check_sql = text(
                    f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}' AND column_name='{column_name}'"
                )
                result = await session.execute(check_sql)
                if not result.scalar():
                    logger.warning(f"Column '{column_name}' missing in '{table_name}'. Adding it...")
                    await session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
                    await session.commit()
            except Exception as e:
                logger.error(f"Error checking column {column_name} in {table_name}: {e}")


# Global instance
schema_orchestrator = SchemaOrchestrator()
