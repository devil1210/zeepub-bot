import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException

from config.config_settings import config
from core.state_manager import state_manager
from services.notion_service import notion_service
from services.recommendation_service import RecommendationService
from services.settings_service import get_setting

logger = logging.getLogger(__name__)


async def handle_bot_info(data: dict[str, Any], user_data: dict[str, Any], request=None):
    """Devuelve información básica del bot y configuración de UI global."""

    bot = None
    if request and hasattr(request.app.state, "bot_instance"):
        bot = request.app.state.bot_instance.app.bot

    if not bot:
        try:
            from api.main import bot as global_bot

            bot = global_bot.app.bot
        except ImportError:
            pass  # bot might be None if not running

    avatar_url = "/robot-librarian.jpg"

    if bot:
        try:
            bot_user = await bot.get_me()
            photos = await bot.get_user_profile_photos(bot_user.id, limit=1)
            if photos.photos:
                file_id = photos.photos[0][-1].file_id
                avatar_url = f"/api/bot/avatar?file_id={file_id}"

            name = bot_user.first_name or "ZeePubBot"
            username = f"@{bot_user.username}" if bot_user.username else "@ZeePubBot"
        except Exception as e:
            logger.error(f"Could not fetch bot profile photo: {e}")
            name = "ZeePubBot"
            username = "@ZeePubBot"
    else:
        name = "ZeePubBot"
        username = "@ZeePubBot"

    ui_defaults = {}
    try:
        ui_defaults_raw = get_setting("ui_defaults_global", "{}")
        ui_defaults = json.loads(ui_defaults_raw)
    except Exception:
        ui_defaults = {}

    # Robust Defaults if DB is empty
    if not ui_defaults:
        ui_defaults = {
            "theme": "dark",
            "primaryColor": "#3b82f6",
            "fontSize": 14,
            "navOpacity": 0.8,
            "accentOpacity": 0.2,
            "glassBlur": 12,
            "backgroundColor": "#0f172a",
            "cardColor": "#1e293b",
            "glassOpacity": 0.6,
        }

    return {
        "name": name,
        "username": username,
        "description": "Asistente de EPUB del grupo. Preciso, limpio y siempre listo para ayudarte. 📚",
        "avatar": avatar_url,
        "version": config.VERSION,
        "ui_defaults": ui_defaults,
    }


async def handle_user_status(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve el nivel del usuario e información de descargas (límites, etc)."""
    from utils.download_limiter import downloads_left

    user_id = user_data.get("user_id")
    level_key = user_data.get("level", "free")
    st = state_manager.get_user_state(user_id)

    is_admin = (
        user_data.get("role") == "admin"
        or user_data.get("is_real_admin")
        or level_key in ["admin", "Administrador"]
        or user_id in config.ADMIN_USERS
    )

    roles_display = {
        "admin": "Admin 🛠️",
        "Administrador": "Admin 🛠️",
        "staff": "Staff 🛡️",
        "premium": "Premium ✨",
        "vip": "VIP ⭐️",
        "white": "Patrocinador 🤍",
        "free": "Lector 📚",
        "banned": "🚫 Baneado",
    }

    # Prioritize label from user_data (which comes from get_effective_user)
    system_role_text = (
        user_data.get("status_label")
        or ("Admin 🛠️" if is_admin else roles_display.get(level_key, level_key))
    )

    # 1. Use Unified Download Limiter
    left = await downloads_left(user_id)
    used = st.get("downloads_used", 0)

    # Calculate max based on what's left + what's used, but only if not unlimited
    if isinstance(left, int) and not is_admin:
        max_dl = left + used
        has_unlimited = False
    else:
        max_dl = 999
        has_unlimited = True

    # Calculate time until next reset (midnight)
    now = datetime.now()
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_left = next_midnight - now
    hours, remainder = divmod(int(time_left.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)

    level_info = user_data.get("level_info") or {}

    # Obtener foto del usuario desde el bot de Telegram
    photo_url = None
    bot = None

    # Intentamos obtener la instancia del bot a partir de request_state o global
    try:
        from api.main import bot as global_bot

        bot = global_bot.app.bot
    except Exception:
        pass

    if bot and user_id:
        try:
            photos = await bot.get_user_profile_photos(user_id, limit=1)
            if photos.photos:
                # Usamos la primera foto en el tamaño de resolución más bajo para carga ultra rápida
                file_id = photos.photos[0][0].file_id
                photo_url = f"/api/bot/avatar?file_id={file_id}"
        except Exception as e:
            logger.warning(f"Could not fetch profile photo for user {user_id}: {e}")

    user_email = user_data.get("email")
    # username real de Telegram (filtrar valores debug/sinteticos)
    raw_tg_username = user_data.get("username")
    _debug_usernames = {"admin_debug", "admin.debug", "unknown", "none", ""}
    tg_username = None
    if raw_tg_username and str(raw_tg_username).lower() not in _debug_usernames and not str(raw_tg_username).startswith("User_"):
        tg_username = str(raw_tg_username)

    is_linked = bool(
        is_admin
        or (user_id and user_id > 0 and tg_username)
        or user_data.get("photo_url")
    )

    return {
        "user": {
            "id": user_id,
            "username": user_data.get("nickname") or user_data.get("name") or f"User_{user_id}",
            "tg_username": tg_username,  # @username real de Telegram (sin @)
            "telegram_id": user_id,
            "email": user_email,
            "is_telegram_linked": is_linked,
            "needs_telegram_link": not is_linked and not is_admin,
            "level": level_key or "free",
            "role": user_data.get("role") or ("admin" if is_admin else "free"),
            "status_label": system_role_text or "Lector",
            "has_library_access": bool(
                (user_data.get("has_library_access", True) is not False)
                and (level_info.get("hasLibraryAccess", True) is not False)
            ),
            "can_request_books": bool(
                (user_data.get("can_request_books", True) is not False)
                and (level_info.get("canRequestBooks", True) is not False)
            ),
            "can_download": bool(level_info.get("canDownload", True) is not False),
            "can_read": bool(level_info.get("canRead", True) is not False),
            "can_upload_epub": bool(
                is_admin
                or user_data.get("can_upload_epub", False)
                or level_info.get("canUploadEpub", False)
            ),
            "is_real_admin": is_admin,
            "downloads": {
                "used": int(used or 0),
                "limit": max_dl,
            },
            "photo_url": photo_url or user_data.get("photo_url"),
        },
        "timeUntilReset": f"{hours}h {minutes}m",
        "hasUnlimitedDownloads": has_unlimited or is_admin,
        "isBanned": level_key == "banned",
        "isAdmin": is_admin,
    }


async def handle_link_telegram(data: dict[str, Any], user_data: dict[str, Any], request=None):
    """Vincular cuenta de correo actual con ID o @username de Telegram."""
    user_id = user_data.get("user_id")
    telegram_identifier = data.get("telegram_id") or data.get("telegram_identifier") or data.get("username")
    if not telegram_identifier:
        raise HTTPException(status_code=400, detail="Debes proporcionar un ID de Telegram o tu @usuario.")

    bot = None
    if request and hasattr(request.app.state, "bot_instance"):
        bot = request.app.state.bot_instance.app.bot

    if not bot:
        try:
            from api.main import bot as global_bot

            bot = global_bot.app.bot
        except Exception:
            pass

    from services.user_service import link_telegram_to_user

    result = await link_telegram_to_user(user_id, str(telegram_identifier), bot=bot)
    return result


async def handle_telegram_widget_auth(data: dict[str, Any], user_data: dict[str, Any], request=None):
    """Procesa y valida la autenticación nativa desde el Telegram Login Widget."""
    auth_data = data.get("auth_data") or data
    bot_token = config.TELEGRAM_TOKEN

    from utils.security import validate_telegram_widget_data

    validated = validate_telegram_widget_data(auth_data, bot_token)

    if not validated:
        raise HTTPException(status_code=401, detail="Firma de autenticación de Telegram inválida o expirada.")

    tg_id = int(validated["id"])
    first_name = validated.get("first_name", "")
    last_name = validated.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()
    username = validated.get("username", "")
    photo_url = validated.get("photo_url")

    from services.user_service import upsert_user

    await upsert_user(
        telegram_id=tg_id,
        name=full_name or username or f"User_{tg_id}",
        username=username,
        photo_url=photo_url,
    )

    return {
        "success": True,
        "user_id": tg_id,
        "username": username or full_name,
        "photo_url": photo_url,
        "message": "¡Autenticación con Telegram exitosa!",
    }


async def handle_unlink_telegram(data: dict[str, Any], user_data: dict[str, Any], request=None):
    """Desvincula la cuenta de Telegram del usuario activo."""
    user_id = user_data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Usuario no autenticado.")

    from core.db_manager_pg import pg_manager
    from sqlalchemy import update
    from models.users import User

    async with pg_manager.get_session() as session:
        stmt = update(User).where(User.telegram_id == user_id).values(
            telegram_id=None,
            username=None
        )
        await session.execute(stmt)
        await session.commit()

    return {"success": True, "message": "Cuenta de Telegram desvinculada exitosamente."}


async def handle_recommendations(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve recomendaciones personalizadas (Beta exclusiva Staff)."""
    user_id = user_data.get("user_id")
    settings = user_data.get("settings", {})

    # Check both camelCase and snake_case for backward compatibility
    show_recs = settings.get("showRecommendations")
    if show_recs is None:
        show_recs = settings.get("show_recommendations", True)

    if not show_recs:
        logger.info(f"Recommendations skipped for user {user_id} (disabled in settings)")
        return {"results": []}

    limit = data.get("limit", 10)
    recs = await RecommendationService.get_recommendations(user_id, limit=limit)

    results = []
    for r in recs:
        is_dict = isinstance(r, dict)
        if is_dict:
            # Local book from search/service usually has cover and cover_thumb via to_dict
            book_data = r
        else:
            # LocalBook object from SQLAlchemy
            book_data = r.to_dict()

        # Ensure we use the correct cover paths from DB
        numeric_id = str(book_data.get("id", "")).replace("local_", "")

        results.append(
            {
                "id": f"local_{numeric_id}",
                "title": book_data.get("title"),
                "author": book_data.get("author"),
                "cover": book_data.get("cover"),
                "cover_thumb": book_data.get("cover_thumb"),
                "downloadUrl": f"local_{numeric_id}",
                "is_folder": False,
                "series": book_data.get("series"),
                "seriesIndex": book_data.get("seriesIndex"),
                "cleanTitle": book_data.get("clean_title") or book_data.get("series") or book_data.get("title"),
                "rating_average": book_data.get("rating_average", 0),
                "book_type": book_data.get("book_type"),
            }
        )
    return {"results": results}


async def handle_status(data: dict[str, Any], user_data: dict[str, Any]):
    """Alias para handle_user_status (compatible con acción 'status')."""
    return await handle_user_status(data, user_data)


async def handle_feedback(data: dict[str, Any], user_data: dict[str, Any]):
    """Recibe feedback, reporte de bugs o sugerencias."""
    user_id = user_data.get("user_id")
    message = data.get("message")
    category = data.get("category", "Sugerencia")  # Sugerencia, Bug, Otro

    if not message:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")

    username = user_data.get("nickname") or user_data.get("name") or f"User_{user_id}"

    # Log to Notion
    asyncio.create_task(notion_service.log_feedback(username, message, category))

    return {"success": True, "message": "Feedback recibido. ¡Gracias!"}
