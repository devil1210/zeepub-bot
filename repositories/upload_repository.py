import logging
from typing import Any

from sqlalchemy import desc, select

from models.library_models import UploadBook, UploadHistory
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UploadRepository(BaseRepository[UploadBook]):
    """
    Repositorio para la gestión de libros en proceso de carga (UploadBook)
    y el historial de cargas (UploadHistory).
    """

    def __init__(self, db_manager=None):
        super().__init__(UploadBook, db_manager)

    # --- Métodos adicionales para UploadBook y UploadHistory ---

    async def log_history(self, history_data: dict[str, Any]) -> UploadHistory:
        """Registra una entrada en el historial de cargas."""
        async with self.db_manager.get_session() as session:
            try:
                history_entry = UploadHistory(**history_data)
                session.add(history_entry)
                await session.commit()
                await session.refresh(history_entry)
                return history_entry
            except Exception as e:
                logger.error(f"Error logging upload history: {e}")
                await session.rollback()
                raise

    async def get_history(self, limit: int = 100, offset: int = 0) -> list[UploadHistory]:
        """Obtiene el historial de cargas paginado."""
        async with self.db_manager.get_session() as session:
            try:
                stmt = select(UploadHistory).order_by(desc(UploadHistory.created_at)).limit(limit).offset(offset)
                result = await session.execute(stmt)
                return list(result.scalars().all())
            except Exception as e:
                logger.error(f"Error getting upload history: {e}")
                return []

    async def get_pending_uploads(self) -> list[UploadBook]:
        """Obtiene todos los libros pendientes de aprobación."""
        async with self.db_manager.get_session() as session:
            try:
                stmt = select(UploadBook).order_by(desc(UploadBook.created_at))
                result = await session.execute(stmt)
                return list(result.scalars().all())
            except Exception as e:
                logger.error(f"Error getting pending uploads: {e}")
                return []

    # Alias para compatibilidad
    get_upload_by_id = BaseRepository.get_by_id
    create_upload_record = BaseRepository.create
    delete_upload_record = BaseRepository.delete


upload_repo = UploadRepository()
