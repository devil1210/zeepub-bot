import logging
from typing import Annotated, Any, AsyncGenerator
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import async_session
from config.config_settings import config
from utils.security import validate_telegram_data
from services.user_service import UserService
from models.users import User

logger = logging.getLogger(__name__)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Generador de sesiones de base de datos asíncronas."""
    async with async_session() as session:
        yield session

async def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    """Inyecta el servicio de usuarios con la sesión actual."""
    return UserService(session)

async def get_current_user(
    x_telegram_init_data: Annotated[str | None, Header(alias="x-telegram-init-data")] = None,
    user_service: UserService = Depends(get_user_service)
) -> User:
    """
    Dependencia que valida la autenticación de Telegram y retorna el usuario de la BD.
    Soporta modo DEBUG si está configurado.
    """
    if not x_telegram_init_data:
        # Modo Debug para desarrollo local si se permite
        if config.DEBUG:
            admin_id = list(config.ADMIN_USERS)[0] if config.ADMIN_USERS else 123456
            logger.warning(f"⚠️ DEBUG: Autenticación omitida, usando UID {admin_id}")
            user = await user_service.get_or_create_user(admin_id)
            await user_service.commit_changes()
            return user
        raise HTTPException(status_code=401, detail="Header x-telegram-init-data missing")

    # Validar datos con Telegram
    res = validate_telegram_data(x_telegram_init_data, config.TELEGRAM_TOKEN)
    if not res:
        raise HTTPException(status_code=401, detail="Invalid Telegram Auth")

    tg_user = res.get("user", {})
    uid = tg_user.get("id")
    
    if not uid:
        raise HTTPException(status_code=401, detail="Telegram ID not found in initData")

    # Obtener o crear usuario en nuestro esquema v4.0
    user = await user_service.get_or_create_user(
        uid, 
        username=tg_user.get("username"),
        first_name=tg_user.get("first_name"),
        last_name=tg_user.get("last_name")
    )
    await user_service.commit_changes()
    
    return user
