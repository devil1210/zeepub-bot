import logging
from typing import Any

from sqlalchemy import delete, select

from models.library_models import DuplicateBook
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DuplicateRepository(BaseRepository[DuplicateBook]):
    """
    Repositorio para la gestión de libros duplicados (DuplicateBook).
    """

    def __init__(self, db_manager=None):
        super().__init__(DuplicateBook, db_manager=db_manager)

    # --- Métodos abstractos de BaseRepository ---

    async def get_by_id(self, id: Any) -> DuplicateBook | None:
        """Obtiene un registro de duplicado por ID."""
        async with self.db_manager.get_session() as session:
            return await session.get(DuplicateBook, id)

    async def create(self, entity: DuplicateBook) -> DuplicateBook:
        """Crea un nuevo registro de duplicado."""
        async with self.db_manager.get_session() as session:
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def update(self, entity: DuplicateBook) -> DuplicateBook:
        """Actualiza un registro de duplicado."""
        async with self.db_manager.get_session() as session:
            merged = await session.merge(entity)
            await session.commit()
            await session.refresh(merged)
            return merged

    async def delete(self, id: Any) -> bool:
        """Elimina un registro de duplicado por ID."""
        async with self.db_manager.get_session() as session:
            try:
                stmt = delete(DuplicateBook).where(DuplicateBook.id == id)
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount > 0
            except Exception as e:
                logger.error(f"Error deleting duplicate {id}: {e}")
                await session.rollback()
                return False

    async def get_all_duplicates(self) -> list[DuplicateBook]:
        """Obtiene todos los registros de duplicados detectados."""
        async with self.db_manager.get_session() as session:
            try:
                stmt = select(DuplicateBook).order_by(DuplicateBook.detected_at.desc())
                result = await session.execute(stmt)
                return result.scalars().all()
            except Exception as e:
                logger.error(f"Error getting duplicates: {e}")
                return []

    async def clear_all(self) -> bool:
        """Limpia todos los registros de la tabla de duplicados."""
        async with self.db_manager.get_session() as session:
            try:
                await session.execute(delete(DuplicateBook))
                await session.commit()
                return True
            except Exception as e:
                logger.error(f"Error clearing duplicates: {e}")
                await session.rollback()
                return False


# Instancia global
duplicate_repo = DuplicateRepository()
