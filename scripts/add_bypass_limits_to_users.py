import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration():
    db_url = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            logger.info("Adding bypass_limits column to users table...")
            # Check if column exists first
            check_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='bypass_limits';
            """)
            res = await session.execute(check_sql)
            if not res.fetchone():
                await session.execute(
                    text("ALTER TABLE users ADD COLUMN bypass_limits BOOLEAN DEFAULT FALSE;")
                )
                logger.info("Column bypass_limits added successfully.")
            else:
                logger.info("Column bypass_limits already exists.")

            await session.commit()
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            await session.rollback()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())
