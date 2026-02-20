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
    user_id = user_data.get("user_id")
    level_key = user_data.get("level", "free")
    st = state_manager.get_user_state(user_id)

    roles_display = {
        "admin": "Admin 🛠️",
        "staff": "Staff 🛡️",
        "premium": "Premium ✨",
        "vip": "VIP ⭐️",
        "white": "Patrocinador 🤍",
        "free": "Lector 📚",
        "banned": "🚫 Baneado",
    }

    # Prioritize label from user_data (which comes from get_effective_user)
    system_role_text = user_data.get("status_label") or roles_display.get(level_key, "Lector")

    # Determine max downloads
    if level_key in ("admin", "staff", "premium", "banned"):
        max_dl = None
    elif level_key == "vip":
        max_dl = config.VIP_DOWNLOADS_PER_DAY
    elif level_key == "white":
        max_dl = config.WHITELIST_DOWNLOADS_PER_DAY
    else:
        max_dl = config.MAX_DOWNLOADS_PER_DAY

    used = st.get("downloads_used", 0)

    # Calculate time until next reset (midnight)
    now = datetime.now()
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_left = next_midnight - now
    hours, remainder = divmod(int(time_left.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)

    level_info = user_data.get("level_info") or {}

    return {
        "user": {
            "id": user_id,
            "username": user_data.get("nickname") or user_data.get("name") or f"User_{user_id}",
            "level": level_key or "free",
            "role": user_data.get("role") or "",
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
            "can_upload_epub": bool(user_data.get("can_upload_epub", False) or level_info.get("canUploadEpub", False)),
            "is_real_admin": user_data.get("is_real_admin", False),
            "downloads": {
                "used": int(used or 0),
                "limit": max_dl if max_dl is not None else 999,
            },
        },
        "timeUntilReset": f"{hours}h {minutes}m",
        "hasUnlimitedDownloads": max_dl is None and level_key != "banned",
        "isBanned": level_key == "banned",
        "isAdmin": level_key == "admin",
    }


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
