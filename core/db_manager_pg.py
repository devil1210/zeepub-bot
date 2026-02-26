import asyncio
import logging
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

            db_url = config.DATABASE_URL
            if not db_url:
                logger.warning("No DATABASE_URL found. PostgresManager will not work.")
                return

            # Handle 'postgres://' vs 'postgresql://' for SQLAlchemy
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            try:
                # Optimized async connection pool settings for production
                engine_args = {
                    "echo": False,
                    "pool_pre_ping": True,  # Verify connections before using
                    "pool_size": config.DB_POOL_SIZE or 10,  # Base pool size
                    "max_overflow": config.DB_MAX_OVERFLOW or 20,  # Additional connections
                    "pool_recycle": 3600,  # Recycle connections after 1 hour
                    "pool_timeout": 30,  # Wait up to 30s for available connection
                    "connect_args": {
                        "server_settings": {"jit": "off"},  # Disable JIT for faster simple queries
                        "timeout": 10,  # Connection timeout (10s)
                        "command_timeout": 30,  # Query timeout (30s)
                    },
                }

                self.engine = create_async_engine(db_url, **engine_args)

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
