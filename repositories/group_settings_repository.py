import logging

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.group_models import GroupSettings
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class GroupSettingsRepository(BaseRepository[GroupSettings]):
    def __init__(self, db_manager=None):
        super().__init__(db_manager or pg_manager, "group_settings")

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
