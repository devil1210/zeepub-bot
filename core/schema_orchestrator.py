import logging
from sqlalchemy import text
from core.db_manager_pg import pg_manager
from models.base import Base
# Import custom models so they are registered in Base.metadata
from models.user_models import User, UserLevel, UserUISettings
from models.library_models import LibrarySource, LocalBook, UserRating, UserDownload

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
            async with pg_manager.engine.begin() as conn:
                # Create all tables defined in SQLAlchemy models
                # This only creates tables that don't exist; it won't update existing frames
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Schema verification completed.")
                
                # Seed Initial Data
                await SchemaOrchestrator._seed_initial_data()
                
        except Exception as e:
            logger.critical(f"Failed to initialize schema: {e}")
            raise

    @staticmethod
    async def _seed_initial_data():
        """Populates the database with required initial data like User Levels."""
        from models.user_models import UserLevel
        from sqlalchemy import select
        
        async with pg_manager.get_session() as session:
            try:
                # Check if levels exist
                result = await session.execute(select(UserLevel).limit(1))
                if not result.scalar():
                    logger.info("Seeding default User Levels...")
                    
                    levels = [
                        UserLevel(id=1, name='admin', priority=100, color='#FF5252', price=0.0, daily_downloads=999, has_mini_app_access=True, early_access=True, custom_themes=True, ui_theme='dark'),
                        UserLevel(id=2, name='staff', priority=90, color='#7C4DFF', price=0.0, daily_downloads=999, has_mini_app_access=True, early_access=True, custom_themes=True, ui_theme='dark'),
                        UserLevel(id=3, name='premium', priority=50, color='#FFD740', price=4.99, daily_downloads=50, has_mini_app_access=True, early_access=False, custom_themes=True, ui_theme='dark'),
                        UserLevel(id=4, name='vip', priority=40, color='#69F0AE', price=9.99, daily_downloads=20, has_mini_app_access=True, early_access=False, custom_themes=True, ui_theme='dark'),
                        UserLevel(id=5, name='white', priority=20, color='#E0E0E0', price=0.0, daily_downloads=10, has_mini_app_access=True, early_access=False, custom_themes=False, ui_theme='dark'),
                        UserLevel(id=6, name='free', priority=10, color='#607D8B', price=0.0, daily_downloads=5, has_mini_app_access=True, early_access=False, custom_themes=False, ui_theme='dark'),
                    ]
                    
                    session.add_all(levels)
                    await session.commit()
                    logger.info("Default User Levels seeded successfully.")
                else:
                    # Optional: Verify Admin exists
                     pass
            except Exception as e:
                logger.error(f"Error seeding initial data: {e}")

    @staticmethod
    async def _check_and_add_column(table_name: str, column_name: str, column_type: str):
        """Helper to add missing columns safely."""
        async with pg_manager.get_session() as session:
            try:
                # Check if column exists
                check_sql = text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}' AND column_name='{column_name}'")
                result = await session.execute(check_sql)
                if not result.scalar():
                    logger.warning(f"Column '{column_name}' missing in '{table_name}'. Adding it...")
                    await session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
                    await session.commit()
            except Exception as e:
                logger.error(f"Error checking column {column_name} in {table_name}: {e}")

# Global instance
schema_orchestrator = SchemaOrchestrator()
