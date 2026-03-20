import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.config_settings import config

logger = logging.getLogger(__name__)


class PostgresManager:
    """
    Manages connections to the PostgreSQL database (Supabase or Local).
    Uses SQLAlchemy AsyncIO.
    """

    _instance = None
    _lock = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_()
        return cls._instance

    def _init_(self):
        self.engine = None
        self.session_maker = None
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initializes the database engine and session factory."""
        if self._initialized:
            return

        async with self._lock:
            # Check again inside lock
            if self._initialized:
                return

            # Priority: use direct os.getenv to avoid any default SQLite falling from config
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                db_url = config.DATABASE_URL

            if not db_url or "sqlite" in db_url.lower():
                logger.error("❌ CRITICAL: No valid PostgreSQL DATABASE_URL found.")
                # We return here to avoid starting with SQLite if the user wants Postgres
                return

            # Force asyncpg
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif "postgresql" in db_url:
                db_url = db_url.replace("postgresql+psycopg2", "postgresql+asyncpg")
                if "+asyncpg" not in db_url:
                    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

            # Localhost for Windows
            if "@db:" in db_url or "db:5432" in db_url:
                if os.name == "nt":
                    db_url = db_url.replace("@db:", "@localhost:", 1).replace("db:5432", "localhost:5432")
                    logger.info("🔄 Windows detected: using localhost for Postgres.")

            try:
                self.engine = create_async_engine(db_url, pool_pre_ping=True, pool_recycle=3600)
                self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

                # Verify connection
                async with self.engine.begin() as conn:
                    await conn.run_sync(lambda _: logger.info("Postgres connection established successfully."))

                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize Postgres connection: {e}")
                raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependency for getting a DB session."""
        if not self.session_maker:
            await self.initialize()
            if not self.session_maker:
                raise RuntimeError("Database (PostgreSQL) is not initialized. Check DATABASE_URL.")

        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self):
        """Disposes the engine."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Postgres connection closed.")


# Global instance
pg_manager = PostgresManager()
