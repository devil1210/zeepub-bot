import asyncio
import logging
from sqlalchemy import text
from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Script proporcionado por el usuario (sin COMMIT interno para evitar errores de SQLAlchemy)
SQL_BLOCKS = [
    """
    -- 1. Corregir tipo de dato de source_id
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'books' AND column_name = 'source_id' AND data_type = 'bigint') THEN
            ALTER TABLE books 
            ALTER COLUMN source_id TYPE UUID 
            USING source_id::TEXT::UUID;
            RAISE NOTICE 'Columna source_id actualizada de bigint a UUID.';
        END IF;
    END $$;
    """,
    """
    -- 2. Añadir rating_count si no existe
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name = 'books' AND column_name = 'rating_count') THEN
            ALTER TABLE books ADD COLUMN rating_count INTEGER DEFAULT 0;
        END IF;
    END $$;
    """,
    """
    -- 3. Añadir rating_average si no existe
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name = 'books' AND column_name = 'rating_average') THEN
            ALTER TABLE books ADD COLUMN rating_average NUMERIC(5,2) DEFAULT 0.00;
        END IF;
    END $$;
    """
]

async def run_fix():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        try:
            for block in SQL_BLOCKS:
                logger.info(f"Executing SQL block...")
                await session.execute(text(block))
            
            await session.commit()
            logger.info("✅ Todos los bloques ejecutados y confirmados (Local VPS/Docker).")
            
            # Verificación final
            result = await session.execute(text(
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='books' AND column_name IN ('source_id', 'rating_count', 'rating_average')"
            ))
            for row in result.all():
                logger.info(f"VERIFIED: Column '{row[0]}' is now type '{row[1]}'")
                
        except Exception as e:
            logger.error(f"❌ Error durante la ejecución: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(run_fix())
