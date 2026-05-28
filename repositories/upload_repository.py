import logging
from typing import Any

from sqlalchemy import delete, desc, select

from core.db_manager_pg import pg_manager
from models.library import UploadBook, UploadHistory
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UploadRepository(BaseRepository[UploadBook]):
    """
    Repositorio para la gestión de libros en proceso de carga (UploadBook)
    y el historial de cargas (UploadHistory).
    """

    def __init__(self, db_manager=None):
        super().__init__(model=UploadBook, db_manager=db_manager or pg_manager)

    # --- Implementación de métodos abstractos de BaseRepository ---

    async def get_by_id(self, id: Any) -> UploadBook | None:
        """Obtiene un UploadBook por su ID primario."""
        async with pg_manager.get_session() as session:
            return await session.get(UploadBook, id)

    async def create(self, entity: UploadBook) -> UploadBook:
        """Persiste un nuevo UploadBook en la base de datos."""
        async with pg_manager.get_session() as session:
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def update(self, entity: UploadBook) -> UploadBook:
        """Actualiza un UploadBook existente."""
        async with pg_manager.get_session() as session:
            merged = await session.merge(entity)
            await session.commit()
            await session.refresh(merged)
            return merged

    async def delete(self, id: Any) -> bool:
        """Elimina un UploadBook por ID."""
        return await self.delete_upload_record(id)

    async def create_upload_record(self, upload_data: dict[str, Any]) -> UploadBook:
        """Crea un registro de libro pendiente de aprobación."""
        async with pg_manager.get_session() as session:
            upload_record = UploadBook(**upload_data)
            session.add(upload_record)
            await session.commit()
            await session.refresh(upload_record)
            return upload_record

    async def get_upload_by_id(self, upload_id: int) -> UploadBook | None:
        """Obtiene un registro de upload por su ID primario."""
        async with pg_manager.get_session() as session:
            return await session.get(UploadBook, upload_id)

    async def delete_upload_record(self, upload_id: int) -> bool:
        """Elimina un registro de upload temporal."""
        async with pg_manager.get_session() as session:
            stmt = delete(UploadBook).where(UploadBook.id == upload_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def log_history(self, history_data: dict[str, Any]) -> UploadHistory:
        """Registra una entrada en el historial de cargas."""
        async with pg_manager.get_session() as session:
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
        async with pg_manager.get_session() as session:
            try:
                stmt = select(UploadHistory).order_by(desc(UploadHistory.created_at)).limit(limit).offset(offset)
                result = await session.execute(stmt)
                return result.scalars().all()
            except Exception as e:
                logger.error(f"Error getting upload history: {e}")
                return []

    async def get_pending_uploads(self) -> list[UploadBook]:
        """Obtiene todos los libros pendientes de aprobación."""
        async with pg_manager.get_session() as session:
            try:
                stmt = select(UploadBook).order_by(desc(UploadBook.created_at))
                result = await session.execute(stmt)
                return result.scalars().all()
            except Exception as e:
                logger.error(f"Error getting pending uploads: {e}")
                return []


upload_repo = UploadRepository()
