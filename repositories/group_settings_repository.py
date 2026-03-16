import logging
from typing import Any

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.group_models import GroupSettings
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class GroupSettingsRepository(BaseRepository[GroupSettings]):
    def __init__(self, db_manager=None):
        super().__init__(GroupSettings, db_manager=db_manager)

    # --- Métodos abstractos de BaseRepository ---

    async def get_by_id(self, id: Any) -> GroupSettings | None:
        """Obtiene una configuración de grupo por su ID primario."""
        async with pg_manager.get_session() as session:
            return await session.get(GroupSettings, id)

    async def create(self, entity: GroupSettings) -> GroupSettings:
        """Crea una nueva configuración de grupo."""
        async with pg_manager.get_session() as session:
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def update(self, entity: GroupSettings) -> GroupSettings:
        """Actualiza una configuración de grupo."""
        async with pg_manager.get_session() as session:
            merged = await session.merge(entity)
            await session.commit()
            await session.refresh(merged)
            return merged

    async def delete(self, id: Any) -> bool:
        """Elimina una configuración de grupo por ID."""
        from sqlalchemy import delete

        async with pg_manager.get_session() as session:
            try:
                stmt = delete(GroupSettings).where(GroupSettings.id == id)
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount > 0
            except Exception as e:
                logger.error(f"Error deleting group settings {id}: {e}")
                await session.rollback()
                return False

    async def get_by_chat_id(self, chat_id: int) -> GroupSettings | None:
        """Obtiene la configuración de un grupo por su chat_id."""
        async with self.db_manager.get_session() as session:
            stmt = select(GroupSettings).where(GroupSettings.chat_id == chat_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def set_authorized(self, chat_id: int, authorized: bool = True) -> bool:
        """Establece el estado de autorización de un grupo."""
        async with self.db_manager.get_session() as session:
            try:
                stmt = select(GroupSettings).where(GroupSettings.chat_id == chat_id)
                result = await session.execute(stmt)
                group = result.scalar_one_or_none()

                if not group:
                    group = GroupSettings(chat_id=chat_id, is_authorized=authorized)
                    session.add(group)
                else:
                    group.is_authorized = authorized

                await session.commit()
                return True
            except Exception as e:
                logger.error(f"Error setting group authorization for {chat_id}: {e}")
                return False

    async def set_welcome_slug(self, chat_id: int, slug: str) -> bool:
        """Establece el slug del mensaje de bienvenida para un grupo."""
        async with self.db_manager.get_session() as session:
            try:
                stmt = select(GroupSettings).where(GroupSettings.chat_id == chat_id)
                result = await session.execute(stmt)
                group = result.scalar_one_or_none()

                if not group:
                    group = GroupSettings(chat_id=chat_id, welcome_msg_slug=slug)
                    session.add(group)
                else:
                    group.welcome_msg_slug = slug

                await session.commit()
                return True
            except Exception as e:
                logger.error(f"Error setting group welcome slug for {chat_id}: {e}")
                return False


group_settings_repo = GroupSettingsRepository()
