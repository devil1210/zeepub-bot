import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select

from api.handlers.helpers import check_staff
from config.config_settings import config
from core.db_manager_pg import pg_manager
from core.supabase_manager import supabase_manager
from repositories.user_repository import user_repo

logger = logging.getLogger(__name__)


async def handle_admin_get_users(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene la lista paginada de usuarios para el panel admin."""
    check_staff(user_data)
    limit = data.get("limit", 20)
    offset = data.get("offset", 0)
    search = data.get("search")
    users = await user_repo.list_users(limit=limit, offset=offset, search=search)
    return {"users": users}


async def handle_admin_set_user_level(data: dict[str, Any], user_data: dict[str, Any]):
    """Cambia el nivel de un usuario específico."""
    check_staff(user_data)
    target_id = data.get("userId")
    level_id = data.get("levelId")
    if not target_id or not level_id:
        raise HTTPException(status_code=400, detail="Faltan parámetros userId o levelId")
    await user_repo.update_user_level(int(target_id), int(level_id))
    return {"success": True}


async def handle_admin_scan_user(data: dict[str, Any], user_data: dict[str, Any], request=None):
    """Sincroniza la foto de perfil de un usuario desde Telegram."""
    check_staff(user_data)
    target_id = data.get("userId")
    if not target_id:
        raise HTTPException(status_code=400, detail="Falta parámetro userId")

    bot = None
    if request and hasattr(request.app.state, "bot_instance"):
        bot = request.app.state.bot_instance.app.bot

    if not bot:
        try:
            from api.main import bot as global_bot

            bot = global_bot
        except ImportError:
            return {"success": False, "message": "Bot instance no disponible"}

    from services.user_service import sync_user_profile_photo

    result = await sync_user_profile_photo(int(target_id), bot)
    if result:
        return {
            "success": True,
            "photo_url": result.get("photo_url"),
            "username": result.get("username"),
            "name": result.get("name"),
        }
    else:
        return {
            "success": False,
            "message": "No se pudo sincronizar la foto o identidad de perfil.",
        }


async def handle_admin_sync_users_cloud(data: dict[str, Any], user_data: dict[str, Any]):
    """Sincroniza usuarios y niveles locales (Postgres) a Supabase."""
    check_staff(user_data)

    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}

    try:
        from models.user_models import User, UserLevel

        client = supabase_manager.get_client()

        async with pg_manager.get_session() as session:
            # 1. Sync User Levels
            res_levels = await session.execute(select(UserLevel))
            levels = res_levels.scalars().all()

            for lvl in levels:
                lvl_data = {
                    "id": lvl.id,
                    "name": lvl.name,
                    "priority": lvl.priority,
                    "color": lvl.color,
                    "ui_theme": lvl.ui_theme,
                    "ui_primary_color": lvl.ui_primary_color,
                    "ui_font_size": lvl.ui_font_size,
                    "ui_nav_opacity": lvl.ui_nav_opacity,
                    "ui_glass_blur": lvl.ui_glass_blur,
                    "ui_cover_width": lvl.ui_cover_width,
                    "ui_accent_opacity": lvl.ui_accent_opacity,
                    "panel_transparency": lvl.panel_transparency,
                    "background_color": lvl.background_color,
                    "card_color": lvl.card_color,
                    "banner_content_offset": lvl.banner_content_offset,
                    "force_settings": lvl.force_settings,
                    "price": lvl.price,
                    "can_download": lvl.can_download,
                    "can_read": lvl.can_read,
                    "daily_downloads": lvl.daily_downloads,
                    "has_mini_app_access": lvl.has_mini_app_access,
                    "has_library_access": lvl.has_library_access,
                    "can_request_books": lvl.can_request_books,
                    "can_upload_epub": lvl.can_upload_epub,
                    "early_access": lvl.early_access,
                    "custom_themes": lvl.custom_themes,
                    "allow_theme_templates": lvl.allow_theme_templates,
                    "show_recommendations": lvl.show_recommendations,
                    "default_theme_id": lvl.default_theme_id,
                }
                try:
                    client.table("user_levels").upsert(lvl_data).execute()
                except Exception as upsert_e:
                    logger.warning(f"Supabase upsert error for user_level {lvl.id}: {upsert_e}")

            # 2. Sync Users
            res_users = await session.execute(select(User))
            users = res_users.scalars().all()

            user_batch = []
            for u in users:
                u_data = {
                    "telegram_id": u.telegram_id,
                    "username": u.username,
                    "name": u.name,
                    "nickname": u.nickname,
                    "photo_url": u.photo_url,
                    "level_id": u.level_id,
                    "role": u.role,
                    "beta_tester": u.beta_tester,
                    "has_library_access": u.has_library_access,
                    "can_request_books": u.can_request_books,
                    "can_upload_epub": u.can_upload_epub,
                    "total_downloads": u.total_downloads,
                    "insignias": u.insignias,
                    "settings": u.settings,
                    "expires_at": u.expires_at.isoformat() if u.expires_at else None,
                }
                user_batch.append(u_data)

            if user_batch:
                for i in range(0, len(user_batch), 50):
                    batch = user_batch[i : i + 50]
                    try:
                        client.table("users").upsert(batch).execute()
                    except Exception as upsert_e:
                        logger.error(
                            f"Supabase PUSH error for user batch (indices {i}-{i + len(batch) - 1}): {upsert_e}"
                        )

            # 3. Pull from Supabase
            logger.info("ADMIN: Triggering immediate PULL from Supabase to Local")
            from core.optimized_sync_engine import optimized_sync_engine

            await optimized_sync_engine.force_sync_all()
            try:
                await optimized_sync_engine._sync_users_optimized()
                await optimized_sync_engine._sync_user_levels_optimized()
                await optimized_sync_engine._sync_admins_optimized()
            except Exception as pull_e:
                logger.error(f"Error during bidirectional PULL: {pull_e}")
                return {
                    "success": True,
                    "message": f"Push completado ({len(users)} users), pero el Pull falló: {pull_e}",
                }

            return {
                "success": True,
                "message": f"Sincronización bidireccional completada. Pushed {len(users)} users.",
                "stats": {"users_pushed": len(users), "levels_pushed": len(levels)},
            }
    except Exception as e:
        return {"success": False, "message": str(e)}


async def handle_admin_save_user_permissions(data: dict[str, Any], user_data: dict[str, Any]):
    """Guarda los permisos de un usuario específico."""
    check_staff(user_data)
    from models.user_models import User

    target_id = data.get("userId")
    if not target_id:
        raise HTTPException(status_code=400, detail="Falta userId")

    async with pg_manager.get_session() as session:
        user = await session.get(User, int(target_id))
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if "levelId" in data:
            user.level_id = int(data["levelId"])

        user.has_library_access = data.get("hasLibraryAccess", user.has_library_access)
        user.can_request_books = data.get("canRequestBooks", user.can_request_books)
        user.can_upload_epub = data.get("canUploadEpub", user.can_upload_epub)
        user.beta_tester = data.get("betaTester", user.beta_tester)
        user.allow_theme_templates = data.get("allowThemeTemplates", user.allow_theme_templates)
        user.role = data.get("role", user.role)

        expires_str = data.get("expiresAt") or data.get("expires_at")
        if expires_str:
            from datetime import datetime

            try:
                user.expires_at = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
            except Exception:
                pass

        await session.commit()
    return {"success": True}


async def handle_admin_get_user_permissions(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene los permisos de un usuario específico."""
    check_staff(user_data)
    from models.user_models import User

    target_id = data.get("userId")
    if not target_id:
        raise HTTPException(status_code=400, detail="Falta userId")

    async with pg_manager.get_session() as session:
        from sqlalchemy.orm import selectinload

        stmt = select(User).options(selectinload(User.level_info)).where(User.telegram_id == int(target_id))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {
            "success": True,
            "user": {
                "id": str(user.telegram_id),
                "telegramId": user.telegram_id,
                "username": user.username,
                "name": user.name,
                "nickname": user.nickname,
                "levelId": user.level_id,
                "levelName": user.level_info.name if user.level_info else "Básico",
                "levelColor": user.level_info.color if user.level_info else "#3b82f6",
                "hasLibraryAccess": user.has_library_access,
                "canRequestBooks": user.can_request_books,
                "canUploadEpub": user.can_upload_epub,
                "betaTester": user.beta_tester,
                "role": user.role,
                "expiresAt": user.expires_at.isoformat() if user.expires_at else None,
                "photo_url": user.photo_url,
                "insignias": user.insignias,
                "settings": user.settings,
                "allowThemeTemplates": user.allow_theme_templates,
                "canReport": True,  # Fallback as not in schema yet
                "bypassLimits": user.bypass_limits,
            },
        }


async def handle_admin_get_recent_audit_logs(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene los logs de auditoría recientes de todo el sistema."""
    check_staff(user_data)
    limit = data.get("limit", 100)
    offset = data.get("offset", 0)

    from services.user_audit_service import UserAuditService

    logs = UserAuditService.get_recent_changes(limit=limit, offset=offset)
    return {"logs": logs}


async def handle_get_user_audit_history(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene el historial de auditoría de un usuario específico."""
    check_staff(user_data)
    target_id = data.get("userId")
    if not target_id:
        raise HTTPException(status_code=400, detail="Falta userId")

    from services.user_audit_service import UserAuditService

    logs = UserAuditService.get_user_history(str(target_id))
    return {"success": True, "history": logs, "logs": logs}
