"""
core/v4_db_manager.py
-----------------------
DBManagerV4: Gestor de base de datos para el stack V4.

Crear y verificar las tablas V4 de forma idempotente (CREATE IF NOT EXISTS)
usando SQLAlchemy async sobre la misma DATABASE_URL configurada en config.

Uso en main.py:
    from core.v4_db_manager import DBManagerV4
    db_v4 = DBManagerV4()
    await db_v4.create_all_tables()
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import create_async_engine

# Importar todos los modelos V4 para que los metadatos queden registrados
import models.agent_models  # noqa: F401
import models.library_models  # noqa: F401
import models.publication_models  # noqa: F401
import models.user_models  # noqa: F401
from config.config_settings import config
from models.base import Base

logger = logging.getLogger(__name__)


class DBManagerV4:
    """
    Crea/verifica el schema del stack V4 sobre la misma base de
    datos PostgreSQL del bot (DATABASE_URL).

    Llama a `create_all_tables()` una vez al arranque.
    """

    def __init__(self, database_url: str | None = None):
        url = database_url or config.DATABASE_URL
        if not url:
            raise RuntimeError("DATABASE_URL no configurada. El stack V4 requiere PostgreSQL.")
        self._engine = create_async_engine(url, echo=False)

    async def create_all_tables(self) -> None:
        """
        Ejecuta CREATE TABLE IF NOT EXISTS para todas las tablas V4
        definidas en los modelos SQLAlchemy.
        """
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        logger.info("[DBManagerV4] Schema V4 sincronizado correctamente.")

    async def dispose(self) -> None:
        await self._engine.dispose()
