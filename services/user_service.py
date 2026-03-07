from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.users import UserRepository
from models.users import User, UserUISettings
import logging

logger = logging.getLogger(__name__)

class UserService:
    """
    Servicio para gestionar usuarios, niveles y configuraciones de UI.
    """
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.session = session

    async def get_or_create_user(self, telegram_id: int, **defaults) -> User:
        """Obtiene un usuario existente o crea uno nuevo."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            user = await self.user_repo.create(telegram_id=telegram_id, **defaults)
            # Crear configuración de UI por defecto
            ui_settings = UserUISettings(user_id=telegram_id, primary_color="#3b82f6")
            self.session.add(ui_settings)
            await self.session.flush()
        return user

    async def update_ui_settings(self, telegram_id: int, **settings) -> Optional[UserUISettings]:
        """Actualiza las preferencias estéticas del usuario."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user or not user.ui_settings:
            return None
        
        for key, value in settings.items():
            if hasattr(user.ui_settings, key):
                setattr(user.ui_settings, key, value)
        
        return user.ui_settings

    async def commit_changes(self):
        await self.session.commit()
