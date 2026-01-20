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
                
        except Exception as e:
            logger.critical(f"Failed to initialize schema: {e}")
            raise

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
