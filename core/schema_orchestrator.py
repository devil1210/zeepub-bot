import asyncio
import logging
from uuid import UUID

from sqlalchemy import text

from core.db_manager_pg import pg_manager

# Import custom models so they are registered in Base.metadata
from models import (  # noqa: F401
    publication_models,
    rating_models,
    translators_models,
    user_models,
)
from models.base import Base
from models.library_models import LibrarySource
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
                # Enable postgres extensions
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("Extension 'vector' enabled.")

                try:
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgsentinel"))
                    logger.info("Extension 'pgsentinel' enabled.")
                except Exception as e:
                    logger.warning(f"Extension 'pgsentinel' not available (optional): {e}")

                # Create all tables defined in SQLAlchemy models
                # This only creates tables that don't exist; it won't update existing frames
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Base tables creation/verification completed.")

                # Auto-Migration for UserLevel (Add missing columns to existing table)
                await SchemaOrchestrator._check_and_add_column("user_levels", "daily_downloads", "INTEGER DEFAULT 5")
                await SchemaOrchestrator._check_and_add_column("user_levels", "can_download", "BOOLEAN DEFAULT TRUE")
                await SchemaOrchestrator._check_and_add_column("user_levels", "ui_theme", "VARCHAR(50) DEFAULT 'dark'")
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
                await SchemaOrchestrator._check_and_add_column("user_levels", "ui_primary_color", "VARCHAR(20)")
                await SchemaOrchestrator._check_and_add_column("user_levels", "ui_nav_opacity", "INTEGER")
                await SchemaOrchestrator._check_and_add_column("user_levels", "border_radius", "INTEGER DEFAULT 16")
                await SchemaOrchestrator._check_and_add_column("user_levels", "border_width", "INTEGER DEFAULT 1")
                await SchemaOrchestrator._check_and_add_column(
                    "user_levels", "banner_content_offset", "INTEGER DEFAULT 0"
                )

                # Auto-Migration for Users (Ensure created_at and email exists)
                await SchemaOrchestrator._check_and_add_column("users", "email", "VARCHAR(255) UNIQUE")
                await SchemaOrchestrator._check_and_add_column("users", "can_upload_epub", "BOOLEAN DEFAULT FALSE")
                await SchemaOrchestrator._check_and_add_column("users", "has_library_access", "BOOLEAN DEFAULT TRUE")
                await SchemaOrchestrator._check_and_add_column("users", "can_request_books", "BOOLEAN DEFAULT TRUE")
                await SchemaOrchestrator._check_and_add_column(
                    "users", "allow_theme_templates", "BOOLEAN DEFAULT FALSE"
                )
                await SchemaOrchestrator._check_and_add_column("users", "beta_tester", "BOOLEAN DEFAULT FALSE")
                await SchemaOrchestrator._check_and_add_column("users", "bypass_limits", "BOOLEAN DEFAULT FALSE")
                await SchemaOrchestrator._check_and_add_column("users", "total_downloads", "BIGINT DEFAULT 0")
                await SchemaOrchestrator._check_and_add_column("users", "photo_url", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("users", "nickname", "VARCHAR(255)")
                await SchemaOrchestrator._check_and_add_column("users", "roles", "JSONB DEFAULT '[]'::jsonb")
                await SchemaOrchestrator._check_and_add_column("users", "insignias", "JSONB DEFAULT '[]'::jsonb")
                await SchemaOrchestrator._check_and_add_column("users", "expires_at", "TIMESTAMP WITH TIME ZONE")
                await SchemaOrchestrator._check_and_add_column(
                    "users",
                    "updated_at",
                    "TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())",
                )
                await SchemaOrchestrator._check_and_add_column("users", "created_at", "TIMESTAMP DEFAULT NOW()")

                # Auto-Migration for Books (Full Scanner Support)
                await SchemaOrchestrator._check_and_add_column("books", "series_id", "UUID")
                await SchemaOrchestrator._check_and_add_column("books", "filename", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "file_modified_at", "NUMERIC")
                await SchemaOrchestrator._check_and_add_column("books", "file_created_at", "TIMESTAMP WITH TIME ZONE")
                await SchemaOrchestrator._check_and_add_column("books", "language", "VARCHAR(10) DEFAULT 'es'")
                await SchemaOrchestrator._check_and_add_column("books", "translator", "VARCHAR(255)")
                await SchemaOrchestrator._check_and_add_column("books", "layout_by", "VARCHAR(255)")
                await SchemaOrchestrator._check_and_add_column("books", "author", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "english_title", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "jap_title", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "romaji_title", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "book_type", "VARCHAR(50)")
                await SchemaOrchestrator._check_and_add_column("books", "edition", "VARCHAR(100)")
                await SchemaOrchestrator._check_and_add_column("books", "publisher", "VARCHAR(255)")
                await SchemaOrchestrator._check_and_add_column("books", "extracted_data", "JSONB DEFAULT '{}'::jsonb")
                await SchemaOrchestrator._check_and_add_column("books", "hash_md5", "VARCHAR(64)")
                await SchemaOrchestrator._check_and_add_column("books", "isbn", "VARCHAR(50)")
                await SchemaOrchestrator._check_and_add_column("books", "asin", "VARCHAR(50)")
                await SchemaOrchestrator._check_and_add_column("books", "uri_id", "VARCHAR(255)")
                await SchemaOrchestrator._check_and_add_column("books", "published_at", "VARCHAR(100)")
                await SchemaOrchestrator._check_and_add_column("books", "modified_at_opf", "VARCHAR(100)")
                await SchemaOrchestrator._check_and_add_column("books", "epub_version", "VARCHAR(20)")
                await SchemaOrchestrator._check_and_add_column("books", "word_count", "INTEGER")
                await SchemaOrchestrator._check_and_add_column("books", "page_count", "INTEGER")
                await SchemaOrchestrator._check_and_add_column("books", "reading_time", "INTEGER")
                await SchemaOrchestrator._check_and_add_column("books", "is_uncensored", "BOOLEAN DEFAULT FALSE")
                await SchemaOrchestrator._check_and_add_column("books", "color_mode", "VARCHAR(20) DEFAULT 'bw'")
                await SchemaOrchestrator._check_and_add_column("books", "series_hash", "VARCHAR(64)")
                await SchemaOrchestrator._check_and_add_column("books", "short_link", "VARCHAR(100)")
                await SchemaOrchestrator._check_and_add_column("books", "cover_original", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "cover_high", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "cover_medium", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "cover_low", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "author_jap", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "illustrator", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "illustrator_jap", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "spanish_title", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "english_title", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "romaji_title", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "jap_title", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("books", "series_spanish", "VARCHAR(255)")
                await SchemaOrchestrator._check_and_add_column("books", "series_english", "VARCHAR(255)")

                # Auto-Migration for PublicationChannels
                await SchemaOrchestrator._check_and_add_column(
                    "publication_channels", "is_favorite", "BOOLEAN DEFAULT FALSE"
                )

                # Auto-Migration for Series (author_jap, illustrator_jap, title_english)
                await SchemaOrchestrator._check_and_add_column("series", "author_jap", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("series", "illustrator_jap", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("series", "illustrator", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("series", "title_english", "VARCHAR(512)")
                await SchemaOrchestrator._check_and_add_column("series", "demographics", "JSONB")

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
                            id=UUID("00000000-0000-0000-0000-000000000001"),
                            name="Administrador",
                            priority=100,
                            color="#FF4B4B",
                            price=0.0,
                            daily_downloads=999,
                            can_read=True,
                            has_mini_app_access=True,
                            early_access=True,
                            custom_themes=True,
                            allow_theme_templates=True,
                            can_upload_epub=True,
                        ),
                        UserLevel(
                            id=UUID("00000000-0000-0000-0000-000000000002"),
                            name="Staff",
                            priority=90,
                            color="#4ECDC4",
                            price=0.0,
                            daily_downloads=999,
                            can_read=True,
                            has_mini_app_access=True,
                            early_access=True,
                            custom_themes=True,
                            allow_theme_templates=True,
                            can_upload_epub=False,
                        ),
                        UserLevel(
                            id=UUID("00000000-0000-0000-0000-000000000003"),
                            name="Premium",
                            priority=80,
                            color="#FFD93D",
                            price=1.99,
                            daily_downloads=50,
                            can_read=True,
                            has_mini_app_access=True,
                            early_access=False,
                            custom_themes=True,
                            allow_theme_templates=True,
                            can_upload_epub=False,
                        ),
                        UserLevel(
                            id=UUID("00000000-0000-0000-0000-000000000004"),
                            name="VIP",
                            priority=70,
                            color="#1A5F7A",
                            price=0.99,
                            daily_downloads=20,
                            can_read=True,
                            has_mini_app_access=True,
                            early_access=False,
                            custom_themes=True,
                            allow_theme_templates=True,
                            can_upload_epub=False,
                        ),
                        UserLevel(
                            id=UUID("00000000-0000-0000-0000-000000000005"),
                            name="Patrocinador",
                            priority=60,
                            color="#FFFFFF",
                            price=0.0,
                            daily_downloads=10,
                            can_read=True,
                            has_mini_app_access=True,
                            early_access=True,
                            custom_themes=True,
                            allow_theme_templates=True,
                            can_upload_epub=False,
                        ),
                        UserLevel(
                            id=UUID("00000000-0000-0000-0000-000000000006"),
                            name="Lector",
                            priority=0,
                            color="#888888",
                            price=0.0,
                            daily_downloads=5,
                            can_read=True,
                            has_mini_app_access=True,
                            early_access=False,
                            custom_themes=False,
                            allow_theme_templates=True,
                            can_upload_epub=False,
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
