# src/core/db.py
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.core.config import settings

logger = logging.getLogger(__name__)

class NexusDatabase:
    """
    Gestor de base de datos asíncrono para Zeepub-Nexus.
    Mantiene el pool de conexiones optimizado para el VPS.
    """
    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self):
        """Inicializa el engine y la fábrica de sesiones."""
        if self._engine:
            return

        db_url = settings.DATABASE_URL
        # Corrección automática de protocolo para asyncpg
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        try:
            self._engine = create_async_engine(
                db_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=10,
                max_overflow=20,
            )
            self._session_factory = async_sessionmaker(
                self._engine, 
                expire_on_commit=False, 
                class_=AsyncSession
            )
            logger.info("🛢 NexusDatabase: Engine inicializado correctamente.")
        except Exception as e:
            logger.error(f"❌ Error inicializando NexusDatabase: {e}")
            raise

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager para sesiones asíncronas manuales."""
        if not self._session_factory:
            await self.initialize()
        
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def get_session(self) -> AsyncSession:
        """Obtiene una sesión (útil para FastAPI Depends)."""
        if not self._session_factory:
            await self.initialize()
        return self._session_factory()

    async def close(self):
        """Cierra el engine y libera recursos."""
        if self._engine:
            await self._engine.dispose()
            logger.info("🛢 NexusDatabase: Engine cerrado.")

# Singleton exportable
db_manager = NexusDatabase()
