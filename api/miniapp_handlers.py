import json
import logging
import urllib.parse
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import HTTPException

from config.config_settings import config
from core.state_manager import state_manager
from repositories.download_repository import download_repo
from repositories.user_repository import user_repo
from services.library_service import LibraryService
from services.opds_service import get_cached_feed
from services.rating_service import RatingService
from services.settings_service import get_setting, set_setting
from services.telegram_service import enviar_libro_directo
from utils.helpers import (
    build_search_url,
    abs_url,
    extract_author,
    extract_creators_by_role,
    parse_metadata_from_title,
)

logger = logging.getLogger(__name__)

# --- Handlers ---


async def handle_search(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Busca libros en la base de datos local o en el servidor OPDS."""
    user_id = user_data.get("user_id", 0)
    user_role = user_data.get("role", "free")
    query = data.get("query")
    page_url = data.get("pageUrl")
    page = data.get("page", 1)

    is_local_search = True # Always enforced for web interface
    
    if is_local_search:
        logger.info(f"[search] Using LibraryService for grouped series search. Query: '{query or ''}'")
        return await LibraryService.search_series(
            query or "", page=page
        )

    # REMOVED: OPDS Fallback Logic
    return {"results": []}


async def handle_book_detail(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Devuelve el detalle de un libro desde la base de datos local o OPDS."""
    user_id = user_data.get("user_id", 0)
    book_id_raw = data.get("bookId")
    logger.info(f"[book-detail] Request received - bookId: {book_id_raw}")

    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    # 1. Series/Group Handling
    if isinstance(book_id_raw, str) and book_id_raw.startswith("series_"):
        s_hash = book_id_raw.replace("series_", "")
        volumes = await LibraryService.get_series_volumes(s_hash)
        if not volumes:
            raise HTTPException(status_code=404, detail="Serie no encontrada")
        
        # Usar el primero como representante para la info general
        rep = volumes[0]
        return {
            "id": book_id_raw,
            "title": rep.get("series_clean") or rep.get("series") or rep.get("title"),
            "author": rep.get("author"),
            "summary": rep.get("description"),
            "cover": rep.get("cover"),
            "rating_average": rep.get("rating_average", 0),
            "rating_count": rep.get("rating_count", 0),
            "numBooks": len(volumes),
            "is_series": True,
            "volumes": volumes # Retornamos los volúmenes reales
        }

    # 2. Local Book ONLY (Individual)
    if isinstance(book_id_raw, str) and (
        book_id_raw.isdigit() or (book_id_raw.startswith("local_") and not book_id_raw.startswith("series_"))
    ):
        clean_id = int(str(book_id_raw).replace("local_", ""))
        local_book = await LibraryService.get_book_by_id(clean_id)
        if local_book:
            logger.info(
                f"[book-detail] Found local book via LibraryService: {local_book['title']}"
            )
            local_book["is_downloaded"] = await download_repo.has_user_downloaded(
                user_id,
                local_book["title"],
                local_book.get("cleanTitle"),
                local_book.get("content_hash"),
            )
            local_book["download_count"] = await download_repo.get_total_download_count(
                local_book["title"],
                local_book.get("cleanTitle"),
                local_book.get("content_hash"),
            )
            return local_book
    
    # OPDS fallback removed
    raise HTTPException(status_code=404, detail="Book not found in local library")

    # Get metrics from centralized DB
    from repositories.metrics_repository import metrics_repo

    content_hash = entry.get("content_hash") or entry.get("hash")
    if content_hash:
        result["is_downloaded"] = await metrics_repo.has_downloaded(
            user_id, content_hash
        )
        result["download_count"] = await metrics_repo.get_total_downloads(content_hash)
        rating_stats = await metrics_repo.get_rating_stats(content_hash)
        result["rating_average"] = rating_stats["average"]
        result["rating_count"] = rating_stats["count"]

    return result


async def handle_bot_info(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Devuelve información básica del bot y configuración de UI global."""
    from api.main import bot

    bot_user = await bot.app.bot.get_me()
    avatar_url = "/robot-librarian.jpg"

    try:
        photos = await bot.app.bot.get_user_profile_photos(bot_user.id, limit=1)
        if photos.photos:
            file_id = photos.photos[0][-1].file_id
            avatar_url = f"/api/bot/avatar?file_id={file_id}"
    except Exception as e:
        logger.error(f"Could not fetch bot profile photo: {e}")

    return {
        "name": bot_user.first_name or "ZeePubBot",
        "username": f"@{bot_user.username}" if bot_user.username else "@ZeePubBot",
        "description": "Asistente de EPUB del grupo. Preciso, limpio y siempre listo para ayudarte. 📚",
        "avatar": avatar_url,
        "ui_defaults": json.loads(get_setting("ui_defaults_global", "{}")),
    }


async def handle_user_status(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Devuelve el nivel del usuario e información de descargas (límites, etc)."""
    user_id = user_data.get("user_id")
    role_key = user_data.get("role", "free")
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

    system_role_text = roles_display.get(role_key, "Lector")

    # Determine max downloads
    if role_key in ("admin", "staff", "premium", "banned"):
        max_dl = None
    elif role_key == "vip":
        max_dl = config.VIP_DOWNLOADS_PER_DAY
    elif role_key == "white":
        max_dl = config.WHITELIST_DOWNLOADS_PER_DAY
    else:
        max_dl = config.MAX_DOWNLOADS_PER_DAY

    used = st.get("downloads_used", 0)

    # Calculate time until next reset (midnight)
    now = datetime.now()
    next_midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    time_left = next_midnight - now
    hours, remainder = divmod(int(time_left.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)

    return {
        "level": system_role_text,
        "downloadsUsed": used,
        "downloadsLimit": max_dl,
        "timeUntilReset": f"{hours}h {minutes}m",
        "hasUnlimitedDownloads": max_dl is None and role_key != "banned",
        "isBanned": role_key == "banned",
        "isAdmin": role_key == "admin",
        "role": role_key,
    }


async def handle_user_downloads_history(
    data: Dict[str, Any], user_data: Dict[str, Any]
):
    """Devuelve el historial reciente de descargas del usuario."""
    user_id = user_data.get("user_id")
    try:
        downloads = await download_repo.get_user_downloads(user_id, limit=20)
        return {"downloads": downloads}
    except Exception as e:
        logger.error(f"Error fetching download history for user {user_id}: {e}")
        return {"downloads": []}


async def handle_recommendations(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Devuelve recomendaciones personalizadas (Beta exclusiva Staff)."""
    from services.recommendation_service import RecommendationService

    user_id = user_data.get("user_id")
    user_role = user_data.get("role", "free")

    if user_role not in ("admin", "staff"):
        raise HTTPException(status_code=403, detail="Beta exclusiva para Staff")

    limit = data.get("limit", 10)
    recs = await RecommendationService.get_recommendations(user_id, limit=limit)

    results = []
    for r in recs:
        is_dict = isinstance(r, dict)
        r_id = r.get("id") if is_dict else r.id
        results.append(
            {
                "id": f"local_{r_id}",
                "title": r.get("title") if is_dict else r.title,
                "author": r.get("author") if is_dict else r.author,
                "cover": (
                    f"/api/library/covers/{r_id}"
                    if (r.get("cover_path") if is_dict else r.cover_path)
                    else None
                ),
                "downloadUrl": f"local_{r_id}",
                "is_folder": False,
                "series": r.get("series") if is_dict else r.series,
                "seriesIndex": r.get("series_index") if is_dict else r.series_index,
                "cleanTitle": r.get("title") if is_dict else r.title,
                "rating_average": (
                    r.get("rating_average") if is_dict else r.rating_average
                )
                or 0,
            }
        )
    return {"results": results}


async def handle_rate_book(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Permite al usuario calificar un libro."""
    user_id = user_data.get("user_id")
    book_id_raw = data.get("bookId")
    rating = data.get("rating")

    if not book_id_raw or rating is None:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId o rating")

    try:
        book_id = int(str(book_id_raw).replace("local_", ""))
    except ValueError:
        raise HTTPException(
            status_code=400, detail="ID de libro inválido para votación"
        )

    return RatingService.rate_book(user_id, book_id, rating)


async def handle_remove_rating(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Elimina la calificación previa del usuario sobre un libro."""
    user_id = user_data.get("user_id")
    book_id_raw = data.get("bookId")
    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    try:
        book_id = int(str(book_id_raw).replace("local_", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de libro inválido")

    return RatingService.remove_rating(user_id, book_id)


async def handle_save_badge_config(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Guarda la configuración global de los badges (solo Admin)."""
    user_role = user_data.get("role", "free")
    if user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden guardar configuración global",
        )

    set_setting("badge_pos_top", str(data.get("badgeTop", 8)))
    set_setting("badge_pos_right", str(data.get("badgeRight", 8)))
    set_setting("show_pos_tool", str(data.get("showPosTool", False)))
    set_setting("badge_pos_mode", data.get("badgePosMode", "relative"))

    return {"success": True, "message": "Configuración de badge guardada correctamente"}


async def handle_download(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Envía el archivo del libro directamente a través del bot."""
    user_id = user_data.get("user_id")
    book_id = data.get("bookId")
    title = data.get("title", "Libro")
    target = data.get("target", "private")
    target_id_override = data.get("targetId")
    thread_id_override = data.get("threadId")

    if not book_id:
        raise HTTPException(status_code=400, detail="Missing bookId")

    from api.main import bot

    target_chat_id = user_id
    message_thread_id = None
    is_admin = user_id in config.ADMIN_USERS

    if is_admin:
        if target == "channel":
            target_chat_id = target_id_override or get_setting(
                "mini_app_channel_id", "@ZeePubs"
            )
        elif target == "group":
            target_chat_id = target_id_override or get_setting(
                "mini_app_group_id", "@ZeePubBotTest"
            )
            message_thread_id = thread_id_override

    metadata_override = None
    actual_download_url = book_id  # Default to book_id for remote books

    logger.debug(
        f"handle_download called with book_id: {book_id}, type: {type(book_id)}"
    )

    # Try to find book by content_hash first (most reliable)
    if book_id and not book_id.startswith("http"):
        try:
            from utils.library_db import get_session
            from models.library_models import LocalBook

            session = get_session()
            lb = None

            # Try by content_hash first
            lb = session.query(LocalBook).filter_by(content_hash=book_id).first()

            # Fallback: try by ID if it's numeric
            if not lb and (book_id.startswith("local_") or book_id.isdigit()):
                local_id = int(str(book_id).replace("local_", ""))
                lb = session.query(LocalBook).get(local_id)

            # Fallback: try by filepath
            if not lb and (
                book_id.startswith("/library/") or book_id.startswith("library/")
            ):
                lb = session.query(LocalBook).filter_by(filepath=book_id).first()

            if lb:
                metadata_override = lb.to_dict()
                actual_download_url = lb.filepath
                logger.debug(
                    f"Local book found: content_hash={metadata_override.get('content_hash')}, filepath={actual_download_url}"
                )
            else:
                logger.warning(f"Book not found in library: {book_id}")
        except Exception as e:
            logger.error(f"Error fetching metadata for handle_download: {e}")

    success = await enviar_libro_directo(
        bot=bot.app.bot,
        user_id=user_id,
        title=title,
        download_url=actual_download_url,
        target_chat_id=target_chat_id,
        message_thread_id=message_thread_id,
        metadata_override=metadata_override,
    )
    return {"success": success}


async def handle_ui_settings(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Gestiona configuraciones de UI (globales, por rol o personales)."""
    user_id = user_data.get("user_id")
    user_role = user_data.get("role", "free")
    sub_action = data.get("subAction", "get")

    if sub_action == "get":
        target_role = data.get("role", "global")
        if target_role == "auto":
            target_role = user_role

        final_settings = {
            "primaryColor": "#3b82f6",
            "uiScale": 1.0,
            "avatarScale": 1.0,
            "isDarkMode": True,
            "showSearchCard": True,
            "showSearchBar": False,
            "showDonateCard": True,
            "showHelpCard": True,
            "showSettingsInMenu": False,
            "dataSaver": False,
            "badgePosTop": 8,
            "badgePosRight": 8,
            "showPosTool": False,
            "badgePosMode": "relative",
        }

        # Load global and badge config
        try:
            final_settings.update(
                {
                    "badgePosTop": int(get_setting("badge_pos_top", "8")),
                    "badgePosRight": int(get_setting("badge_pos_right", "8")),
                    "showPosTool": get_setting("show_pos_tool", "false").lower()
                    == "true",
                    "badgePosMode": get_setting("badge_pos_mode", "relative"),
                }
            )
            global_raw = get_setting("ui_defaults_global", "{}")
            final_settings.update(json.loads(global_raw))
        except Exception:
            pass

        # Load role settings
        role_version = 0
        if target_role and target_role != "global":
            try:
                role_raw = get_setting(f"ui_defaults_{target_role}", "{}")
                role_data = json.loads(role_raw)
                role_version = role_data.get("ui_version", 0)
                final_settings.update(role_data)
            except Exception:
                pass

        # Personal overrides
        if data.get("role") == "auto":
            user_record = await user_repo.get_by_id(user_id)
            if user_record and user_record.get("settings"):
                user_settings = user_record.get("settings", {})
                last_seen_version = user_settings.get("last_seen_version", 0)
                if role_version > last_seen_version:
                    final_settings["update_notification"] = True
                final_settings.update(user_settings)

        return final_settings

    elif sub_action == "set":
        target_role = data.get("role", "global")
        settings_obj = data.get("settings", {})

        if target_role == "personal":
            try:
                role_raw = get_setting(f"ui_defaults_{user_role}", "{}")
                role_data = json.loads(role_raw)
                settings_obj["last_seen_version"] = role_data.get("ui_version", 0)
            except Exception:
                settings_obj["last_seen_version"] = 0

            await user_repo.update_user_settings(user_id, settings_obj)
            return {"success": True, "message": "Configuración personal guardada"}
        else:
            if user_role != "admin":
                raise HTTPException(
                    status_code=403,
                    detail="Solo administradores pueden cambiar la configuración global",
                )

            settings_obj["ui_version"] = int(time.time())
            set_setting(f"ui_defaults_{target_role}", json.dumps(settings_obj))

            if data.get("forceOverwrite"):
                role_to_level = {
                    "admin": 1,
                    "staff": 2,
                    "premium": 3,
                    "vip": 4,
                    "white": 5,
                    "free": 6,
                }
                l_id = role_to_level.get(target_role)
                if l_id:
                    await user_repo.reset_level_users_settings(l_id)

            return {
                "success": True,
                "message": f"Configuración para {target_role} guardada (v{settings_obj['ui_version']})",
            }


async def handle_create_stars_invoice(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Crea un link de factura de Telegram Stars."""
    tier = data.get("tier", "premium")
    amount = data.get("amount", 100)
    from api.main import bot

    stars_plugin = bot.plugin_manager.get_plugin("stars_payment")
    cms_plugin = bot.plugin_manager.get_plugin("custom_messages")
    if not stars_plugin:
        raise HTTPException(status_code=500, detail="Stars Payment Plugin not found")

    title = f"Nivel {tier.capitalize()}"
    desc = f"Suscripción al nivel {tier.capitalize()}"
    if cms_plugin:
        desc = await cms_plugin.get_text(
            "star_payment_invoice_desc", Nivel=tier.capitalize()
        )

    invoice_link = await stars_plugin.create_stars_invoice_link(
        title=title, description=desc, payload=f"upgrade_{tier}", amount=amount
    )
    return {"invoiceLink": invoice_link}


async def handle_status(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Alias para handle_user_status (compatible con acción 'status')."""
    return await handle_user_status(data, user_data)


async def handle_get_download_count(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Devuelve el conteo de descargas de un libro específico."""
    book_id_raw = data.get("bookId")
    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    book_id = str(book_id_raw)
    title_for_query = None
    clean_title_for_query = None
    book_hash_for_query = None

    if book_id.startswith("local_") or book_id.isdigit():
        clean_id_int = int(book_id.replace("local_", ""))
        local_book = await LibraryService.get_book_by_id(clean_id_int)
        if local_book:
            title_for_query = local_book["title"]
            clean_title_for_query = local_book.get("cleanTitle")
            book_hash_for_query = local_book.get("content_hash")
    else:
        # It's a URL (OPDS)
        try:
            feed = await get_cached_feed(book_id)
            if feed:
                entries = getattr(feed, "entries", [])
                entry = (
                    entries[0]
                    if entries
                    else (feed.feed if getattr(feed, "feed", None) else None)
                )
                if entry:
                    title_for_query = entry.get("title")
                    meta = parse_metadata_from_title(title_for_query)
                    clean_title_for_query = meta.get("clean_title")
                    # For OPDS books we don't have a stable binary hash,
                    # but we can simulate one if we want consistency across scanners.
                    # For now, title-based fallback in repository will handle it.
        except Exception as e:
            logger.error(
                f"[handle_get_download_count] Error resolving OPDS title for {book_id}: {e}"
            )

    if not title_for_query and not book_hash_for_query:
        return {"count": 0}

    from repositories.metrics_repository import metrics_repo

    count = (
        await metrics_repo.get_total_downloads(book_hash_for_query)
        if book_hash_for_query
        else 0
    )
    return {"count": count}


async def handle_rating_breakdown(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Devuelve el desglose de calificaciones para un libro."""
    book_id_raw = data.get("bookId")
    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    try:
        book_id = int(str(book_id_raw).replace("local_", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de libro inválido")

    return {"breakdown": RatingService.get_rating_breakdown(book_id)}
