import asyncio
import logging
from sqlalchemy import text
from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def deep_inspect():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        # 1. Search Path
        res = await session.execute(text("SHOW search_path;"))
        logger.info(f"Search Path: {res.scalar()}")

        # 2. Localizar 'books' en TODO el catálogo de PostgreSQL
        q = text("""
            SELECT n.nspname as schema, c.relname as name, 
                   CASE c.relkind 
                     WHEN 'r' THEN 'table' 
                     WHEN 'v' THEN 'view' 
                     WHEN 'm' THEN 'materialized view' 
                     WHEN 'i' THEN 'index' 
                     WHEN 'S' THEN 'sequence' 
                     WHEN 'f' THEN 'foreign table' 
                     WHEN 'p' THEN 'partitioned table' 
                     ELSE 'other' 
                   END as type
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = 'books';
        """)
        res = await session.execute(q)
        for r in res.all():
            logger.info(f"OBJETO ENCONTRADO: Schema: {r[0]} | Name: {r[1]} | Type: {r[2]}")

        # 3. Ver columnas de TODOS los objetos llamados 'books'
        q_cols = text("""
            SELECT n.nspname as schema, c.relname as table_name, a.attname as column_name, 
                   pg_catalog.format_type(a.atttypid, a.atttypmod) as type
            FROM pg_catalog.pg_attribute a
            JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = 'books' AND a.attnum > 0 AND NOT a.attisdropped
            AND a.attname = 'source_id';
        """)
        res = await session.execute(q_cols)
        for r in res.all():
            logger.info(f"COLUMNA: Schema: {r[0]} | Table: {r[1]} | Col: {r[2]} | Type: {r[3]}")

        # 4. Si hay discrepancia, intentar forzar el tipo en el esquema que sea bigint
        res = await session.execute(q_cols)
        for r in res.all():
            if 'bigint' in r[3].lower():
                schema = r[0]
                logger.info(f"🔨 Corrigiendo {schema}.books.source_id...")
                try:
                    await session.execute(text(f"ALTER TABLE {schema}.books ALTER COLUMN source_id TYPE UUID USING source_id::TEXT::UUID;"))
                    logger.info("✅ Hecho.")
                except Exception as e:
                    logger.error(f"❌ Falló corrección en {schema}: {e}")

        await session.commit()

if __name__ == "__main__":
    asyncio.run(deep_inspect())
