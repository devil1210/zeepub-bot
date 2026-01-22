import logging
import asyncio
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from config.config_settings import config

logger = logging.getLogger(__name__)

class PostgresManager:
    """
    Manages connections to the PostgreSQL database (Supabase or Local).
    Uses SQLAlchemy AsyncIO.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PostgresManager, cls).__new__(cls)
            cls._instance._init_()
        return cls._instance

    def _init_(self):
        self.engine = None
        self.session_maker = None
        self._initialized = False

    async def initialize(self):
        """Initializes the database engine and session factory."""
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
            self.engine = create_async_engine(
                db_url,
                echo=False,  # Set to True for SQL query logging
                poolclass=NullPool,  # Better for serverless/Supabase direct connections
                connect_args={"server_settings": {"jit": "off"}},  # Optimization for simple queries
            )
            
            self.session_maker = async_sessionmaker(
                self.engine, 
                expire_on_commit=False, 
                class_=AsyncSession
            )
            
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
            except Exception as e:
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
