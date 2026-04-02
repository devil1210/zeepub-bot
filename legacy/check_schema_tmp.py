import asyncio
import logging
import os
from sqlalchemy import text
from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_schema():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        try:
            for table in ["books", "series", "user_levels"]:
                logger.info(f"--- Checking table: {table} ---")
                
                # Check table exists
                table_check = text(
                    f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
                )
                exists = (await session.execute(table_check)).scalar()
                logger.info(f"Table '{table}' exists: {exists}")
                
                if exists:
                    # List columns
                    columns_sql = text(
                        f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}' ORDER BY column_name"
                    )
                    results = await session.execute(columns_sql)
                    cols = results.all()
                    for col in cols:
                        logger.info(f"  Column: {col[0]} ({col[1]})")
                logger.info("")
        except Exception as e:
            logger.error(f"Error checking schema: {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())
