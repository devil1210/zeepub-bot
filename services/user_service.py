import logging
from typing import Any

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
            # Solo asignamos level_id=1 si estamos seguros de que existe o si el repo lo permite
            # UserRepository.create manejará la integridad o usará el default del modelo (6) si falla
            defaults["level_id"] = 1

        if not user:
            # Verificación proactiva: ¿Existe el level_id en la DB?
            from sqlalchemy import text

            lvl_exists = (
                await self.session.execute(
                    text("SELECT EXISTS(SELECT 1 FROM user_levels WHERE id = :lid)"),
                    {"lid": defaults.get("level_id", 6)},
                )
            ).scalar()

            if not lvl_exists:
                logger.warning(
                    f"Level ID {defaults.get('level_id', 6)} not found in DB. Using fallback level 0 (Temporary) or skipping assignment."
                )
                # Si es el primer arranque, tratamos de forzar el nivel default o dejar que el modelo decida
                if "level_id" in defaults:
                    del defaults["level_id"]  # Dejar que el modelo use su default (6) si no existe el 1

            user = await self.user_repo.create(telegram_id=telegram_id, **defaults)
            # Crear configuración de UI por defecto
            ui_settings = UserUISettings(user_id=telegram_id, primary_color="#3b82f6")
            self.session.add(ui_settings)
            await self.session.flush()
            # Refrescar para asegurar que level y ui_settings estén cargados
            await self.session.refresh(user, ["level", "ui_settings"])
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
            username = None
            name = f"User_{telegram_id}"
            if tg_user:
                if isinstance(tg_user, dict):
                    username = tg_user.get("username")
                    name = tg_user.get("first_name") or name
                else:
                    username = getattr(tg_user, "username", None)
                    name = getattr(tg_user, "first_name", None) or getattr(tg_user, "full_name", name)
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
            "is_real_admin": data.get("is_real_admin"),
            "isStaff": data.get("level") in ("admin", "staff"),
        }

    async def get_user_by_email(self, email: str) -> dict | None:
        """Helper for Cloudflare / Supabase auth fallback."""
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload

        query = select(User).where(User.email == email.lower()).options(joinedload(User.level))
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if user:
            return {
                "telegram_id": user.telegram_id,
                "email": user.email,
                "name": user.name,
                "username": user.username,
                "role": user.role,
                "level_id": user.level_id,
            }
        return None

    async def get_or_create_user_by_email(self, email: str) -> int:
        """Obtiene o crea un usuario registrado mediante correo (Cloudflare Access)."""
        import zlib
        clean_email = email.strip().lower()
        is_admin = bool(config.ADMIN_EMAILS and clean_email in config.ADMIN_EMAILS)

        existing = await self.get_user_by_email(clean_email)
        if existing and existing.get("telegram_id"):
            if is_admin and existing.get("role") != "admin":
                from sqlalchemy import select
                query = select(User).where(User.email == clean_email)
                res = await self.session.execute(query)
                u_obj = res.scalar_one_or_none()
                if u_obj:
                    u_obj.role = "admin"
                    u_obj.level_id = 1
                    await self.session.commit()
            return existing["telegram_id"]

        synthetic_id = abs(zlib.crc32(clean_email.encode("utf-8")))

        from sqlalchemy import select
        query = select(User).where(User.telegram_id == synthetic_id)
        res = await self.session.execute(query)
        u = res.scalar_one_or_none()

        if not u:
            name_part = clean_email.split("@")[0]
            u = User(
                telegram_id=synthetic_id,
                email=clean_email,
                name=name_part,
                username=name_part,
                role="admin" if is_admin else "user",
                level_id=1 if is_admin else 6,
                is_beta=False,
                can_upload=False,
                can_upload_epub=False,
            )
            self.session.add(u)
            await self.session.commit()
        else:
            if is_admin and u.role != "admin":
                u.role = "admin"
                u.level_id = 1
                await self.session.commit()

        return synthetic_id

    async def _reassign_user_references(self, old_id: int, new_id: int):
        """Reasigna referencias de tablas secundarias de old_id a new_id."""
        from sqlalchemy import text
        tables_and_cols = [
            ("user_downloads", "user_id"),
            ("user_activity_logs", "user_id"),
            ("user_activity_logs", "changed_by_id"),
            ("user_history", "user_id"),
            ("user_books", "user_id"),
            ("operations", "user_id"),
        ]
        for tbl, col in tables_and_cols:
            try:
                async with self.session.begin_nested():
                    await self.session.execute(
                        text(f"UPDATE {tbl} SET {col} = :new_id WHERE {col} = :old_id"),
                        {"new_id": new_id, "old_id": old_id},
                    )
            except Exception as e:
                logger.debug(f"Could not update {tbl}.{col} from {old_id} to {new_id}: {e}")

    async def link_telegram_to_user(self, current_user_id: int, telegram_identifier: str, bot=None) -> dict:
        """Vincular la cuenta de correo actual con un ID o Username de Telegram."""
        from sqlalchemy import select

        ident = telegram_identifier.strip().lstrip("@")
        if not ident:
            raise ValueError("El identificador de Telegram no puede estar vacío.")

        resolved_tg_id: int | None = None
        target_user = None

        if ident.isdigit():
            resolved_tg_id = int(ident)
            query = select(User).where(User.telegram_id == resolved_tg_id)
            res = await self.session.execute(query)
            target_user = res.scalar_one_or_none()
        else:
            query = select(User).where(User.username.ilike(ident))
            res = await self.session.execute(query)
            target_user = res.scalar_one_or_none()

            # Si no está en DB por username y tenemos la instancia del bot, intentar resolver el username con get_chat
            if not target_user and bot:
                try:
                    chat = await bot.get_chat(f"@{ident}")
                    if chat and chat.id:
                        resolved_tg_id = chat.id
                        query_by_id = select(User).where(User.telegram_id == resolved_tg_id)
                        res_by_id = await self.session.execute(query_by_id)
                        target_user = res_by_id.scalar_one_or_none()
                except Exception as e:
                    logger.warning(f"No se pudo resolver @{ident} mediante Telegram Bot API: {e}")

        # Obtener el usuario actual (sesión web)
        query_curr = select(User).where(User.telegram_id == current_user_id)
        res_curr = await self.session.execute(query_curr)
        curr_user = res_curr.scalar_one_or_none()

        if not curr_user:
            raise ValueError("Usuario web actual no encontrado.")

        email_to_link = curr_user.email
        is_admin = curr_user.role == "admin"

        if target_user:
            # Si el usuario de Telegram ya existe en la DB
            if curr_user.telegram_id != target_user.telegram_id:
                if email_to_link:
                    try:
                        async with self.session.begin_nested():
                            curr_user.email = None
                            await self.session.flush()
                    except Exception:
                        pass
                target_user.email = email_to_link

                if is_admin:
                    target_user.role = "admin"
                    target_user.level_id = 1

                await self._reassign_user_references(curr_user.telegram_id, target_user.telegram_id)
                try:
                    async with self.session.begin_nested():
                        await self.session.delete(curr_user)
                except Exception as e:
                    logger.warning(f"No se pudo eliminar el usuario sintético anterior {curr_user.telegram_id}: {e}")
            else:
                if email_to_link and target_user.email != email_to_link:
                    target_user.email = email_to_link

            final_user = target_user
        else:
            # Si el usuario destino no existía en la DB
            if resolved_tg_id and curr_user.telegram_id != resolved_tg_id:
                if email_to_link:
                    try:
                        async with self.session.begin_nested():
                            curr_user.email = None
                            await self.session.flush()
                    except Exception:
                        pass

                target_user = User(
                    telegram_id=resolved_tg_id,
                    email=email_to_link,
                    name=curr_user.name,
                    username=ident,
                    role=curr_user.role,
                    level_id=curr_user.level_id,
                    is_beta=curr_user.is_beta,
                    can_upload=curr_user.can_upload,
                    can_upload_epub=curr_user.can_upload_epub,
                )
                self.session.add(target_user)
                await self.session.flush()
                await self._reassign_user_references(curr_user.telegram_id, resolved_tg_id)
                try:
                    async with self.session.begin_nested():
                        await self.session.delete(curr_user)
                except Exception as e:
                    logger.warning(f"No se pudo eliminar el usuario sintético {curr_user.telegram_id}: {e}")
                final_user = target_user
            elif ident.isdigit():
                new_tg_id = int(ident)
                if curr_user.telegram_id != new_tg_id:
                    if email_to_link:
                        try:
                            async with self.session.begin_nested():
                                curr_user.email = None
                                await self.session.flush()
                        except Exception:
                            pass
                    target_user = User(
                        telegram_id=new_tg_id,
                        email=email_to_link,
                        name=curr_user.name,
                        username=curr_user.username or f"User_{new_tg_id}",
                        role=curr_user.role,
                        level_id=curr_user.level_id,
                        is_beta=curr_user.is_beta,
                        can_upload=curr_user.can_upload,
                        can_upload_epub=curr_user.can_upload_epub,
                    )
                    self.session.add(target_user)
                    await self.session.flush()
                    await self._reassign_user_references(curr_user.telegram_id, new_tg_id)
                    try:
                        async with self.session.begin_nested():
                            await self.session.delete(curr_user)
                    except Exception as e:
                        logger.warning(f"No se pudo eliminar el usuario sintético {curr_user.telegram_id}: {e}")
                    final_user = target_user
                else:
                    final_user = curr_user
            else:
                raise ValueError(
                    f"No se pudo encontrar a @{ident} en Telegram. Para vincular por alias, abre primero el bot en Telegram (@spcore_bot) y presiona /start o utiliza el botón 'Abrir Bot en Telegram'."
                )

        # Intentar obtener foto de perfil si bot está disponible
        if bot and final_user.telegram_id:
            try:
                photos = await bot.get_user_profile_photos(final_user.telegram_id, limit=1)
                if photos and photos.photos:
                    file_id = photos.photos[0][0].file_id
                    final_user.photo_url = f"/api/bot/avatar?file_id={file_id}"
            except Exception as e:
                logger.debug(f"Error obteniendo foto de perfil de Telegram: {e}")

        await self.session.commit()
        return {
            "success": True,
            "telegram_id": final_user.telegram_id,
            "username": final_user.username,
            "email": final_user.email,
            "name": final_user.name,
            "photo_url": final_user.photo_url,
        }

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
        level_map = {"admin": 1, "staff": 2, "premium": 3, "vip": 4, "user": 6, "free": 6, "white": 5}

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


async def increment_download_count(telegram_id: int) -> int:
    """Incrementa el contador total de descargas de un usuario."""
    from repositories.user_repository import user_repo

    return await user_repo.increment_download_count(telegram_id)


async def sync_user_profile_photo(telegram_id: int, bot=None) -> dict | None:
    """Sincroniza la foto de perfil del usuario desde Telegram API."""
    from repositories.user_repository import user_repo

    photo_url = None
    if bot:
        try:
            photos = await bot.get_user_profile_photos(telegram_id, limit=1)
            if photos and photos.photos:
                file_id = photos.photos[0][0].file_id
                photo_url = f"/api/bot/avatar?file_id={file_id}"
        except Exception as e:
            logger.warning(f"No se pudo obtener foto de perfil para {telegram_id}: {e}")

    if photo_url:
        await user_repo.update_profile(telegram_id, photo_url=photo_url)

    return await user_repo.get_by_telegram_id(telegram_id)


async def check_milestones(telegram_id: int, context=None) -> str | None:
    """Comprueba si el usuario ha alcanzado un hito de descargas."""
    from repositories.user_repository import user_repo

    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        return None
    downloads = getattr(user, "total_downloads", 0) or 0
    if downloads in (10, 50, 100, 250, 500, 1000):
        return f"🎉 ¡Felicidades! Has alcanzado un hito de <b>{downloads} descargas</b> en ZeePub."
    return None


async def get_or_create_user_by_email(email: str) -> int:
    from core.db_manager_pg import pg_manager

    async with pg_manager.get_session() as session:
        service = UserService(session)
        return await service.get_or_create_user_by_email(email)


async def link_telegram_to_user(current_user_id: int, telegram_identifier: str, bot=None) -> dict:
    from core.db_manager_pg import pg_manager

    async with pg_manager.get_session() as session:
        service = UserService(session)
        return await service.link_telegram_to_user(current_user_id, telegram_identifier, bot=bot)


import secrets
import time

_QR_AUTH_SESSIONS: dict[str, dict[str, Any]] = {}


def create_qr_auth_session(user_id: int) -> dict[str, Any]:
    """Crea una sesión de autenticación QR efímera (válida por 5 minutos)."""
    now = time.time()
    expired = [k for k, v in _QR_AUTH_SESSIONS.items() if now - v.get("created_at", 0) > 300]
    for k in expired:
        _QR_AUTH_SESSIONS.pop(k, None)

    token = f"auth_{secrets.token_hex(4)}"
    _QR_AUTH_SESSIONS[token] = {
        "token": token,
        "user_id": user_id,
        "status": "pending",
        "created_at": now,
        "telegram_user": None,
    }
    return {
        "token": token,
        "status": "pending",
        "expires_in": 300,
        "bot_username": "spcore_bot",
        "bot_link": f"https://t.me/spcore_bot?start={token}",
    }


def get_qr_auth_session(token: str) -> dict[str, Any]:
    """Obtiene el estado actual de una sesión QR."""
    sess = _QR_AUTH_SESSIONS.get(token)
    if not sess:
        return {"status": "expired"}
    if time.time() - sess.get("created_at", 0) > 300:
        _QR_AUTH_SESSIONS.pop(token, None)
        return {"status": "expired"}
    return {
        "status": sess.get("status", "pending"),
        "telegram_user": sess.get("telegram_user"),
        "user_id": sess.get("user_id"),
    }


async def confirm_qr_auth_session(token: str, telegram_id: int, telegram_username: str = None, first_name: str = None, bot=None) -> bool:
    """Confirma la vinculación de Telegram desde el bot usando el token del QR/Deep-link."""
    sess = _QR_AUTH_SESSIONS.get(token)
    if not sess or time.time() - sess.get("created_at", 0) > 300:
        return False

    web_user_id = sess["user_id"]
    res = await link_telegram_to_user(current_user_id=web_user_id, telegram_identifier=str(telegram_id), bot=bot)

    sess["status"] = "authenticated"
    sess["telegram_user"] = {
        "telegram_id": telegram_id,
        "username": telegram_username,
        "name": first_name,
        "photo_url": res.get("photo_url"),
    }
    return True

