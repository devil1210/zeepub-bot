import logging
from typing import Any

from sqlalchemy import delete, select

from models.custom_messages_models import GlobalVariable, PluginSettings, StoredMessage
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CustomMessagesRepository(BaseRepository[StoredMessage]):
    """
    Repositorio asíncrono para gestionar las operaciones de base de datos de CustomMessagesPlugin.
    """

    def __init__(self, db_manager=None):
        super().__init__(StoredMessage, db_manager=db_manager)

    async def save_message(
        self, slug: str, chat_id: int, message_id: int, description: str = None, text_content: str = None
    ) -> bool:
        """Guarda o actualiza un mensaje personalizado en la base de datos."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(StoredMessage).where(StoredMessage.slug == slug)
                result = await session.execute(stmt)
                msg = result.scalar_one_or_none()

                if not msg:
                    msg = StoredMessage(slug=slug)
                    session.add(msg)

                msg.source_chat_id = chat_id
                msg.source_message_id = message_id
                if description:
                    msg.description = description
                if text_content:
                    msg.text_content = text_content

                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving message {slug}: {e}")
            return False

    async def get_message(self, slug: str) -> StoredMessage | None:
        """Recupera un mensaje por su slug."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(StoredMessage).where(StoredMessage.slug == slug)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting message {slug}: {e}")
            return None

    async def delete_message(self, slug: str) -> bool:
        """Elimina un mensaje por su slug."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = delete(StoredMessage).where(StoredMessage.slug == slug)
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting message {slug}: {e}")
            return False

    async def list_messages(self, limit: int = 100, offset: int = 0) -> list[StoredMessage]:
        """Lista todos los mensajes guardados de forma paginada."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(StoredMessage).order_by(StoredMessage.created_at.desc()).limit(limit).offset(offset)
                result = await session.execute(stmt)
                return result.scalars().all()
        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            return []

    async def set_setting(self, key: str, value: str) -> bool:
        """Guarda una configuración del plugin."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(PluginSettings).where(PluginSettings.key == key)
                result = await session.execute(stmt)
                setting = result.scalar_one_or_none()

                if not setting:
                    setting = PluginSettings(key=key)
                    session.add(setting)

                setting.value = value
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting '{key}': {e}")
            return False

    async def get_setting(self, key: str) -> str | None:
        """Recupera una configuración del plugin."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(PluginSettings).where(PluginSettings.key == key)
                result = await session.execute(stmt)
                setting = result.scalar_one_or_none()
                return setting.value if setting else None
        except Exception as e:
            logger.error(f"Error getting setting '{key}': {e}")
            return None

    async def get_all_global_vars(self) -> dict[str, str]:
        """Obtiene todas las variables globales y retorna un diccionario."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(GlobalVariable)
                result = await session.execute(stmt)
                vars_db = result.scalars().all()
                return {v.key: v.value for v in vars_db if v.value}
        except Exception as e:
            logger.error(f"Error refreshing global vars: {e}")
            return {}

    async def set_global_var(self, key: str, value: str) -> bool:
        """Define o actualiza una variable global."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(GlobalVariable).where(GlobalVariable.key == key)
                result = await session.execute(stmt)
                var = result.scalar_one_or_none()

                if not var:
                    var = GlobalVariable(key=key)
                    session.add(var)

                var.value = value
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting global var '{key}': {e}")
            return False

    async def del_global_var(self, key: str) -> bool:
        """Elimina una variable global."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = delete(GlobalVariable).where(GlobalVariable.key == key)
                await session.execute(stmt)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting global var '{key}': {e}")
            return False

    # Required by BaseRepository interface
    async def get_by_id(self, id: Any) -> StoredMessage | None:
        return await self.get_message(str(id))

    async def create(self, entity: StoredMessage) -> StoredMessage:
        async with self.db_manager.get_session() as session:
            session.add(entity)
            await session.commit()
            return entity

    async def update(self, entity: StoredMessage) -> StoredMessage:
        async with self.db_manager.get_session() as session:
            await session.merge(entity)
            await session.commit()
            return entity

    async def delete(self, id: Any) -> bool:
        return await self.delete_message(str(id))


custom_messages_repo = CustomMessagesRepository()
