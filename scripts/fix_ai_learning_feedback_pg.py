import asyncio
import logging
import os
import sys

# Añadir el directorio raíz al path para poder importar core y config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_ai_feedback_table():
    logger.info("Iniciando creación de tabla ai_learning_feedback en Postgres...")
    
    try:
        async with pg_manager.get_session() as session:
            # Crear la tabla si no existe
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_learning_feedback (
                    id SERIAL PRIMARY KEY,
                    series_hash VARCHAR(64) NOT NULL,
                    original_name TEXT NOT NULL,
                    proposed_name TEXT NOT NULL,
                    final_name TEXT,
                    status VARCHAR(20) NOT NULL,
                    ai_reason TEXT,
                    user_reason TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            logger.info("Tabla ai_learning_feedback verificada/creada.")

            # Crear el índice si no existe
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ai_learning_series_hash 
                ON ai_learning_feedback (series_hash);
            """))
            logger.info("Índice idx_ai_learning_series_hash verificado/creado.")
            
            await session.commit()
            logger.info("✅ Migración completada exitosamente.")
            
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        # En caso de error de conexión, mostrar el URL intentado (anonimizado)
        try:
            from config.config_settings import config
            url = config.DATABASE_URL
            if url:
                safe_url = url.split("@")[-1] if "@" in url else "N/A"
                logger.info(f"Host intentado: {safe_url}")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(fix_ai_feedback_table())
