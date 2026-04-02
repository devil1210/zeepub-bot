import asyncio
import logging
import os
from sqlalchemy import text
from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def diagnose():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        # 1. En qué esquema está 'books'?
        logger.info("--- Diagnóstico de Esquemas para la tabla 'books' ---")
        q_schemata = text("""
            SELECT table_schema, table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'books' AND column_name = 'source_id';
        """)
        res = await session.execute(q_schemata)
        rows = res.all()
        if not rows:
            logger.error("❌ No se encontró ninguna tabla 'books' con la columna 'source_id'!")
        else:
            for r in rows:
                logger.info(f"Tabla: {r[0]}.{r[1]} | Columna: {r[2]} | Tipo: {r[3]}")

        # 2. Qué esquema es el por defecto (current_schema)?
        res = await session.execute(text("SELECT current_schema();"))
        logger.info(f"Esquema actual (current_schema): {res.scalar()}")

        # 3. Listar todas las tablas en el esquema actual
        res = await session.execute(text("""
            SELECT tablename FROM pg_catalog.pg_tables 
            WHERE schemaname = current_schema();
        """))
        logger.info(f"Tablas en esquema actual: {[r[0] for r in res.all()]}")

        # 4. Forzar el cambio de tipo de forma explícita en todos los 'books' encontrados
        for r in rows:
            schema = r[0]
            if r[3] == 'bigint':
                logger.info(f"⚠️ Detectado bigint en {schema}.books. Intentando arreglar...")
                try:
                    await session.execute(text(f"ALTER TABLE {schema}.books ALTER COLUMN source_id TYPE UUID USING source_id::TEXT::UUID;"))
                    logger.info(f"✅ Arreglado {schema}.books")
                except Exception as e:
                    logger.error(f"❌ Error arreglando {schema}.books: {e}")
        
        await session.commit()

if __name__ == "__main__":
    asyncio.run(diagnose())
