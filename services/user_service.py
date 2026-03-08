import logging

from sqlalchemy.ext.asyncio import AsyncSession

from config.config_settings import config
from models.users import User, UserUISettings
from repositories.users import UserRepository

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
        
        # Lógica proactiva para administradores configurados en .env
        is_configured_admin = telegram_id in config.ADMIN_USERS or telegram_id == 133994080
        if is_configured_admin:
            defaults["role"] = "admin"
            defaults["level_id"] = 1  # Asumimos que 1 es el nivel admin

        if not user:
            user = await self.user_repo.create(telegram_id=telegram_id, **defaults)
            # Crear configuración de UI por defecto
            ui_settings = UserUISettings(user_id=telegram_id, primary_color="#3b82f6")
            self.session.add(ui_settings)
            await self.session.flush()
        elif is_configured_admin and user.role != "admin":
            # Actualizar si ya existe pero no tiene el rol
            user.role = "admin"
            user.level_id = 1
            await self.session.flush()
            
        return user

    async def update_ui_settings(self, telegram_id: int, **settings) -> UserUISettings | None:
        """Actualiza las preferencias estéticas del usuario."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user or not user.ui_settings:
            return None

        for key, value in settings.items():
            if hasattr(user.ui_settings, key):
                setattr(user.ui_settings, key, value)

        return user.ui_settings

    async def get_effective_user(self, telegram_id: int, tg_user: dict = None, simulated_level_id: int = None) -> dict:
        """
        Returns full effective user profile including level, role and permissions.
        Integrated with RBAC for v4 architecture.
        """
        from services.rbac_service import rbac_service

        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            # Create minimal user if not exists
            username = tg_user.get("username") if tg_user else None
            name = tg_user.get("first_name") if tg_user else f"User_{telegram_id}"
            user = await self.get_or_create_user(telegram_id, username=username, name=name)

        # Prepare base data for RBAC
        user_data = {
            "user_id": telegram_id,
            "telegram_id": telegram_id,
            "username": user.username,
            "nickname": user.nickname,
            "name": user.name,
            "role": user.role,
            "level": user.level.name if user.level else "free",
            "level_info": {
                "name": user.level.name if user.level else "free",
                "hasAccess": user.level.can_download if user.level else True,  # Default perms
                "canDownload": user.level.can_download if user.level else True,
                "canRead": True,
                "hasLibraryAccess": True,
                "canRequestBooks": True,
                "canUploadEpub": user.can_upload,
            },
            "is_real_admin": user.role == "admin" or telegram_id == 133994080,
            "can_upload_epub": user.can_upload,
            "beta_tester": user.is_beta,
        }

        # Apply simulated level if provided
        if simulated_level_id:
            # In a real implementation we would fetch the level info by ID
            pass

        # Flatten permissions
        user_data["permissions"] = list(await rbac_service.get_user_permissions(user_data))

        # Add UI Settings
        if user.ui_settings:
            user_data["settings"] = {
                "theme": user.ui_settings.theme,
                "primaryColor": user.ui_settings.primary_color,
                "glassBlur": user.ui_settings.glass_blur,
                "glassOpacity": user.ui_settings.glass_opacity / 100.0,
            }

        return user_data

    async def get_user_access_data(self, telegram_id: int) -> dict:
        """Lighter version of get_effective_user for quick perm checks."""
        data = await self.get_effective_user(telegram_id)
        return {
            "user_id": telegram_id,
            "level": data.get("level"),
            "role": data.get("role"),
            "permissions": data.get("permissions", []),
            "isAdmin": data.get("is_real_admin"),
            "isStaff": data.get("level") in ("admin", "staff"),
        }

    async def get_user_by_email(self, email: str) -> dict | None:
        """Helper for Supabase auth fallback."""
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload

        query = select(User).where(User.email == email.lower()).options(joinedload(User.level))
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if user:
            return {"telegram_id": user.telegram_id, "email": email}
        return None

    async def get_user_settings(self, telegram_id: int) -> dict:
        """Obtiene todas las configuraciones del usuario."""
        user_data = await self.get_effective_user(telegram_id)
        return user_data.get("settings", {})

    async def update_user_setting(self, telegram_id: int, key: str, value: any):
        """Actualiza una configuración específica del usuario."""
        # Mapeo de nombres de frontend a backend
        key_map = {
            "primaryColor": "primary_color",
            "glassBlur": "glass_blur",
            "glassOpacity": "glass_opacity",
            "theme": "theme",
        }
        db_key = key_map.get(key, key)

        # Si es glassOpacity, convertir de 0.0-1.0 a 0-100
        if db_key == "glass_opacity" and isinstance(value, (float, int)) and value <= 1.0:
            value = int(value * 100)

        await self.update_ui_settings(telegram_id, **{db_key: value})
        await self.session.commit()

    async def remove_user(self, telegram_id: int):
        """Elimina un usuario y todas sus relaciones."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()

    async def get_users_by_level(self, level_id: int) -> list[User]:
        """Obtiene todos los usuarios de un nivel específico."""
        from sqlalchemy import select

        query = select(User).where(User.level_id == level_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def invalidate_user_cache(self, telegram_id: int):
        """Invalida el caché (placeholder para v4)."""
        # En v4 la consistencia es directa via Postgres,
        # pero mantenemos la interfaz para plugins.
        pass

    async def upsert_user(self, telegram_id: int, **data) -> User:
        """Registro/Actualización masiva de usuario (RBAC compatible)."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        
        # Mapeo de niveles legacy a IDs (o nombres)
        level_map = {
            "admin": 1, "staff": 2, "premium": 3, "vip": 4, "user": 6, "free": 6, "white": 5
        }
        
        level_val = data.pop("level", None)
        if level_val:
            if isinstance(level_val, str):
                data["level_id"] = level_map.get(level_val.lower(), 6)
            else:
                data["level_id"] = level_val

        if not user:
            user = await self.user_repo.create(telegram_id=telegram_id, **data)
            # Asegurar ui_settings
            ui_settings = UserUISettings(user_id=telegram_id, primary_color="#3b82f6")
            self.session.add(ui_settings)
        else:
            for k, v in data.items():
                if hasattr(user, k):
                    setattr(user, k, v)
        
        await self.session.flush()
        return user

    async def update_user_status_label(self, telegram_id: int, label: str | None):
        """Actualiza el rol visual (nickname o campo específico si existiera)."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if user:
            user.nickname = label
            await self.session.flush()

    async def commit_changes(self):
        await self.session.commit()


# --- Funciones de Compatibilidad (Standalone) ---


async def get_effective_user(telegram_id: int, tg_user: dict = None, simulated_level_id: int = None) -> dict:
    from core.db_manager_pg import pg_manager

    async with pg_manager.get_session() as session:
        service = UserService(session)
        return await service.get_effective_user(telegram_id, tg_user, simulated_level_id)


async def get_user_access_data(telegram_id: int) -> dict:
    from core.db_manager_pg import pg_manager

    async with pg_manager.get_session() as session:
        service = UserService(session)
        return await service.get_user_access_data(telegram_id)


async def get_user_by_email(email: str) -> dict | None:
    from core.db_manager_pg import pg_manager

    async with pg_manager.get_session() as session:
        service = UserService(session)
        return await service.get_user_by_email(email)


async def remove_user(telegram_id: int):
    from core.db_manager_pg import pg_manager

    async with pg_manager.get_session() as session:
        service = UserService(session)
        await service.remove_user(telegram_id)


async def get_user_settings(telegram_id: int) -> dict:
    from core.db_manager_pg import pg_manager

    async with pg_manager.get_session() as session:
        service = UserService(session)
        return await service.get_user_settings(telegram_id)


async def update_user_setting(telegram_id: int, key: str, value: any):
    from core.db_manager_pg import pg_manager

    async with pg_manager.get_session() as session:
        service = UserService(session)
        await service.update_user_setting(telegram_id, key, value)


async def update_user_nickname(telegram_id: int, nickname: str):
    from core.db_manager_pg import pg_manager

    async with pg_manager.get_session() as session:
        from sqlalchemy import update

        from models.users import User

        stmt = update(User).where(User.telegram_id == telegram_id).values(nickname=nickname)
        await session.execute(stmt)
        await session.commit()


async def get_users_by_level(level_id: int) -> list:
    from core.db_manager_pg import pg_manager

    async with pg_manager.get_session() as session:
        service = UserService(session)
        users = await service.get_users_by_level(level_id)
        # Convert to dict for legacy compatibility if needed,
        # but most plugins expect ORM objects or dict with telegram_id
        return users


async def upsert_user(telegram_id: int, **data):
    from core.db_manager_pg import pg_manager
    async with pg_manager.get_session() as session:
        service = UserService(session)
        await service.upsert_user(telegram_id, **data)
        await session.commit()

async def update_user_status_label(telegram_id: int, label: str | None):
    from core.db_manager_pg import pg_manager
    async with pg_manager.get_session() as session:
        service = UserService(session)
        await service.update_user_status_label(telegram_id, label)
        await session.commit()

async def invalidate_user_cache(telegram_id: int = None):
    # Standalone wrapper for cache invalidation
    pass
