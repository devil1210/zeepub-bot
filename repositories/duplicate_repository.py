import logging

from sqlalchemy import delete, desc, select

from core.db_manager_pg import pg_manager
from models.library_models import DuplicateBook
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DuplicateRepository(BaseRepository[DuplicateBook]):
    """
    Repositorio para la gestión de libros duplicados (DuplicateBook).
    """

    def __init__(self, db_manager=None):
        super().__init__(db_manager or pg_manager, "duplicate_books")

    async def get_all_duplicates(self) -> list[DuplicateBook]:
        """Obtiene todos los registros de duplicados detectados."""
        async with pg_manager.get_session() as session:
            try:
                stmt = select(DuplicateBook).order_by(desc(DuplicateBook.detected_at))
                result = await session.execute(stmt)
                return result.scalars().all()
            except Exception as e:
                logger.error(f"Error getting duplicates: {e}")
                return []

    async def clear_all(self) -> bool:
        """Limpia todos los registros de la tabla de duplicados."""
        async with pg_manager.get_session() as session:
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
