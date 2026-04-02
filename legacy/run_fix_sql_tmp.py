import asyncio
import logging
from sqlalchemy import text
from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQL_SCRIPT = """
DO $$
BEGIN
    -- 1. Corregir tipo de dato de source_id
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'books' AND column_name = 'source_id' AND data_type = 'bigint') THEN
        ALTER TABLE books 
        ALTER COLUMN source_id TYPE UUID 
        USING source_id::TEXT::UUID;
        RAISE NOTICE 'Columna source_id actualizada de bigint a UUID.';
    END IF;
END $$;

DO $$
BEGIN
    -- 2. Añadir rating_count
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'books' AND column_name = 'rating_count') THEN
        ALTER TABLE books ADD COLUMN rating_count INTEGER DEFAULT 0;
    END IF;
END $$;

DO $$
BEGIN
    -- 3. Añadir rating_average
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'books' AND column_name = 'rating_average') THEN
        ALTER TABLE books ADD COLUMN rating_average NUMERIC(5,2) DEFAULT 0.00;
    END IF;
END $$;

COMMIT;
"""

async def run_sql_script():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        try:
            logger.info("Executing local SQL script on port 5432...")
            await session.execute(text(SQL_SCRIPT))
            await session.commit()
            logger.info("Script executed successfully.")
            
            # Verify
            logger.info("Verifying schema...")
            result = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='books' ORDER BY column_name"))
            for row in result.all():
                logger.info(f"  Column: {row[0]} ({row[1]})")
        except Exception as e:
            logger.error(f"Error executing script: {e}")

if __name__ == "__main__":
    asyncio.run(run_sql_script())
