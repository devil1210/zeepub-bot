import json
import logging
from sqlalchemy import func, or_
import urllib.parse
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import HTTPException

from config.config_settings import config
import os
import shutil
from core.db_manager import db_manager
from core.supabase_manager import supabase_manager
from utils.library_db import get_session
from models.library_models import LocalBook, LibrarySource, DuplicateBook
from core.state_manager import state_manager
from repositories.download_repository import download_repo
from repositories.user_repository import user_repo
from services.library_service import LibraryService
from services.opds_service import get_cached_feed
from services.rating_service import RatingService
from services.settings_service import get_setting, set_setting
from sqlalchemy import desc
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
    user_level = user_data.get("level", "free")
    query = data.get("query")
    page = data.get("page", 1)
    search_type = data.get("type", "todos")
    sort = data.get("sort", "a-z")

    is_local_search = True # Always enforced for web interface
    
    if is_local_search:
        logger.info(f"[search] Using LibraryService for grouped series search. Query: '{query or ''}' Type: '{search_type}' Sort: '{sort}'")
        return await LibraryService.search_series(
            query or "", page=page, search_type=search_type, sort_by=sort
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
        "version": config.VERSION,
        "ui_defaults": json.loads(get_setting("ui_defaults_global", "{}")),
    }


async def handle_user_status(data: Dict[str, Any], user_data: Dict[str, Any]):
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
    next_midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    time_left = next_midnight - now
    hours, remainder = divmod(int(time_left.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)

    return {
        "user": {
            "id": user_id,
            "username": user_data.get("nickname") or f"User_{user_id}",
            "level": level_key,
            "role": user_data.get("role"), # Now returns the functional role label
            "status_label": system_role_text,
            "has_library_access": (user_data.get("has_library_access", True) is not False) and (user_data.get("level_info", {}).get("hasLibraryAccess", True) is not False),
            "can_request_books": (user_data.get("can_request_books", True) is not False) and (user_data.get("level_info", {}).get("canRequestBooks", True) is not False),
            "can_download": user_data.get("level_info", {}).get("canDownload", True),
            "can_read": user_data.get("level_info", {}).get("canRead", True),
            "downloads": {
                "used": used,
                "limit": max_dl
            }
        },
        "timeUntilReset": f"{hours}h {minutes}m",
        "hasUnlimitedDownloads": max_dl is None and level_key != "banned",
        "isBanned": level_key == "banned",
        "isAdmin": level_key == "admin",
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
        numeric_id = book_data.get("id", "").replace("local_", "")
        
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
    user_level = user_data.get("level", "free")
    if user_level != "admin":
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
    """Gestiona configuraciones de UI (globales, por nivel o personales)."""
    user_id = user_data.get("user_id")
    user_level = user_data.get("level", "free")
    sub_action = data.get("subAction", "get")

    if sub_action == "get":
        # We can mostly rely on user_data["settings"] which is pre-calculated by get_effective_user
        # but we also add the badge settings which are not in the main settings blob yet.
        
        final_settings = user_data.get("settings", {}).copy()
        
        # Add badge config (stored as separate settings)
        try:
            final_settings.update(
                {
                    "badgePosTop": int(get_setting("badge_pos_top", "8")),
                    "badgePosRight": int(get_setting("badge_pos_right", "8")),
                    "showPosTool": get_setting("show_pos_tool", "false").lower() == "true",
                    "badgePosMode": get_setting("badge_pos_mode", "relative"),
                    "uiScale": 1.0,
                    "avatarScale": 1.0,
                    "isDarkMode": True,
                    "showSearchCard": True,
                    "showSearchBar": False,
                    "showDonateCard": True,
                    "showHelpCard": True,
                    "dataSaver": False,
                }
            )
        except Exception as e:
            logger.error(f"Error loading UI base defaults: {e}")

        return final_settings

    elif sub_action == "set":
        target_role = data.get("role", "global")
        settings_obj = data.get("settings", {})

        if target_role == "personal":
            try:
                role_raw = get_setting(f"ui_defaults_{user_level}", "{}")
                role_data = json.loads(role_raw)
                settings_obj["last_seen_version"] = role_data.get("ui_version", 0)
            except Exception:
                settings_obj["last_seen_version"] = 0

            await user_repo.update_user_settings(user_id, settings_obj)
            return {"success": True, "message": "Configuración personal guardada"}
        else:
            if user_level != "admin":
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


async def handle_admin_stats(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Calcula y devuelve estadísticas globales para el Panel Admin."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    # 1. Dynamic System Metrics
    total_users = 0
    total_books = 0
    dls_24h = 0
    dls_prev_24h = 0
    users_7d = 0
    
    if user_repo.supabase.is_active:
        try:
            # Users
            res_u = user_repo.supabase.get_client().table('users').select("telegram_id", count='exact').execute()
            total_users = res_u.count or 0
            
            # Books
            res_b = user_repo.supabase.get_client().table('local_books').select("id", count='exact').execute()
            total_books = res_b.count or 0
            
            # Downloads 24h
            day_ago = (datetime.now() - timedelta(hours=24)).isoformat()
            res_d = user_repo.supabase.get_client().table('download_history').select("id", count='exact').gte('downloaded_at', day_ago).execute()
            dls_24h = res_d.count or 0

            # Downloads prev 24h (comparison)
            two_days_ago = (datetime.now() - timedelta(hours=48)).isoformat()
            res_dp = user_repo.supabase.get_client().table('download_history').select("id", count='exact').gte('downloaded_at', two_days_ago).lt('downloaded_at', day_ago).execute()
            dls_prev_24h = res_dp.count or 0

            # Users 7d
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            # Note: We assume 'created_at' exists in Supabase. If not, this might fail or return 0.
            try:
                res_u7 = user_repo.supabase.get_client().table('users').select("telegram_id", count='exact').gte('created_at', week_ago).execute()
                users_7d = res_u7.count or 0
            except:
                users_7d = int(total_users * 0.05) # Fallback heuristic if no created_at
        except Exception as e:
            logger.error(f"Supabase metrics error: {e}")
    else:
        async with user_repo.db.connection() as conn:
            # Users
            cur = await conn.execute("SELECT COUNT(*) FROM users")
            total_users = (await cur.fetchone())[0]
            
            # Downloads 24h
            cur = await conn.execute("SELECT COUNT(*) FROM download_history WHERE downloaded_at >= datetime('now', '-1 day')")
            dls_24h = (await cur.fetchone())[0]

            # Downloads prev 24h
            cur = await conn.execute("SELECT COUNT(*) FROM download_history WHERE downloaded_at >= datetime('now', '-2 days') AND downloaded_at < datetime('now', '-1 day')")
            dls_prev_24h = (await cur.fetchone())[0]

            # Users 7d (Check if created_at exists, fallback to total_users * 0.05)
            try:
                cur = await conn.execute("SELECT COUNT(*) FROM users WHERE created_at >= datetime('now', '-7 days')")
                users_7d = (await cur.fetchone())[0]
            except:
                 users_7d = int(total_users * 0.05)
        
        # Books (always from local session for now or repo)
        from utils.library_db import get_session
        from models.library_models import LocalBook
        s = get_session()
        total_books = s.query(LocalBook).count()
        s.close()

    # Calculate Uptime
    from api.main import app_state
    start_time = app_state.get("start_time", time.time())
    uptime_seconds = int(time.time() - start_time)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    
    uptime_text = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"

    # 2. Active Sessions (Users in memory as proxy)
    active_sessions = len(state_manager.user_state)

    # 3. Storage usage
    from utils.library_db import get_session
    from models.library_models import LocalBook
    session = get_session()
    storage_bytes = session.query(func.sum(LocalBook.file_size)).scalar() or 0
    storage_gb = round(storage_bytes / (1024**3), 2)
    session.close()

    # 3. Revenue Estimation
    total_revenue = 0.0
    if user_repo.supabase.is_active:
        try:
            # We can use RPC or join
            res = user_repo.supabase.get_client().table('users').select("level:user_levels(price)").execute()
            if res.data:
                total_revenue = sum(u.get('level', {}).get('price', 0) for u in res.data)
        except Exception as e:
            logger.error(f"Supabase revenue error: {e}")
    else:
        async with user_repo.db.connection() as conn:
            cursor = await conn.execute("""
                SELECT ul.price, COUNT(u.telegram_id) 
                FROM user_levels ul
                LEFT JOIN users u ON u.level_id = ul.id
                GROUP BY ul.id
            """)
            tier_revenue = await cursor.fetchall()
            total_revenue = sum(price * count for price, count in tier_revenue)

    # 4. Popular Book (Last 30 days)
    popular_book = None
    if download_repo.supabase.is_active:
        try:
            three_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            res = download_repo.supabase.get_client().table('download_history').select("title, clean_title, book_hash").gte('downloaded_at', three_days_ago).execute()
            if res.data:
                from collections import Counter
                counts = Counter((f"{r['book_hash']}|{r['title']}|{r['clean_title']}") for r in res.data)
                best = counts.most_common(1)
                if best:
                    key, count = best[0]
                    b_hash, b_title, b_clean = key.split('|')
                    popular_book = {
                        "title": b_clean if b_clean != 'None' else b_title,
                        "downloads": count,
                        "author": "N/A"
                    }
                    # Get author from library
                    session = get_session()
                    lb = session.query(LocalBook).filter(or_(LocalBook.content_hash == b_hash, LocalBook.title == b_title)).first()
                    if lb:
                        popular_book["author"] = lb.author
                        popular_book["cover"] = lb.cover_low
                    session.close()
        except Exception as e:
            logger.error(f"Supabase popular book error: {e}")
    else:
        async with user_repo.db.connection() as conn:
            cursor = await conn.execute("""
                SELECT title, clean_title, book_hash, COUNT(*) as dls
                FROM download_history 
                WHERE downloaded_at >= datetime('now', '-30 days')
                GROUP BY book_hash, clean_title
                ORDER BY dls DESC
                LIMIT 1
            """)
            row = await cursor.fetchone()
            if row:
                title, clean_title, book_hash, dls = row
                popular_book = {
                    "title": clean_title or title,
                    "downloads": dls,
                    "author": "N/A"
                }
                session = get_session()
                lb = session.query(LocalBook).filter(or_(LocalBook.content_hash == book_hash, LocalBook.title == title)).first()
                if lb:
                    popular_book["author"] = lb.author
                    popular_book["cover"] = lb.cover_low
                session.close()

    return {
        "revenue": round(total_revenue, 2),
        "activeSessions": active_sessions,
        "storageUsedGB": storage_gb,
        "storageTotalGB": 1000, # Hardcoded baseline or config
        "popularBook": popular_book,
        "growthTrend": [
            {"date": "15 Nov", "users": 1200, "downloads": 2400},
            {"date": "30 Nov", "users": 1350, "downloads": 2800},
            {"date": "15 Dic", "users": 1500, "downloads": 3100}
        ], # Placeholder for trend
        "totalUsers": total_users,
        "users7d": users_7d,
        "totalBooks": total_books,
        "downloads24h": dls_24h,
        "downloadsPrev24h": dls_prev_24h,
        "uptime": uptime_text
    }


async def handle_admin_get_tiers(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Obtiene todos los niveles y su configuración."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    levels = await user_repo.get_all_levels()
    logger.info(f"ADMIN: handle_admin_get_tiers found {len(levels)} levels")
    return {"success": True, "levels": levels, "tiers": levels}


async def handle_admin_save_tier(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Guarda cambios en un nivel."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    level_id = data.get("id")
    if not level_id:
        raise HTTPException(status_code=400, detail="Falta level_id")
    
    await user_repo.update_level(int(level_id), data)
    return {"success": True}


async def handle_admin_get_users(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Obtiene la lista paginada de usuarios para el panel admin."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    limit = data.get("limit", 20)
    offset = data.get("offset", 0)
    search = data.get("search")
    
    users = await user_repo.list_users(limit=limit, offset=offset, search=search)
    logger.info(f"ADMIN: handle_admin_get_users found {len(users)} users (limit={limit}, offset={offset}, search={search})")
    return {"users": users}


async def handle_admin_set_user_level(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Cambia el nivel de un usuario específico."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    target_id = data.get("userId")
    level_id = data.get("levelId")
    
    if not target_id or not level_id:
        raise HTTPException(status_code=400, detail="Faltan parámetros userId o levelId")
    
    await user_repo.update_user_level(int(target_id), int(level_id))
    return {"success": True}


async def handle_admin_scan_user(data: Dict[str, Any], user_data: Dict[str, Any], request=None):
    """Sincroniza la foto de perfil de un usuario desde Telegram."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    target_id = data.get("userId")
    if not target_id:
        raise HTTPException(status_code=400, detail="Falta parámetro userId")
    
    # Obtener bot del app state
    if not request or not hasattr(request.app.state, "bot_instance"):
        return {"success": False, "message": "Bot instance no disponible"}
    
    bot = request.app.state.bot_instance.app.bot
    
    from services.user_service import sync_user_profile_photo
    photo_url = await sync_user_profile_photo(int(target_id), bot)
    
    if photo_url:
        return {"success": True, "photo_url": photo_url}
    else:
        return {"success": False, "message": "No se pudo sincronizar la foto de perfil (el usuario puede no tener una o tenerla privada)."}


async def handle_admin_backup_library(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Syncs SQLite library data to Supabase."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}

    try:
        session = get_session()
        sources = session.query(LibrarySource).all()
        books = session.query(LocalBook).all()
        
        client = supabase_manager.get_client()
        
        # 1. Sync Sources
        for s in sources:
            source_data = {
                "id": s.id,
                "name": s.name,
                "path": s.path,
                "last_scanned": s.last_scanned.isoformat() if s.last_scanned else None
            }
            client.table('library_sources').upsert(source_data).execute()
            
        # 2. Sync Books in batches
        batch_size = 100
        for i in range(0, len(books), batch_size):
            batch = books[i:i+batch_size]
            books_data = []
            for b in batch:
                books_data.append({
                    "id": b.id,
                    "source_id": b.source_id,
                    "filepath": b.filepath,
                    "filename": b.filename,
                    "file_size": b.file_size,
                    "hash_md5": b.hash_md5,
                    "title": b.title,
                    "romaji_title": b.romaji_title,
                    "english_title": b.english_title,
                    "series": b.series,
                    "spanish_title": b.spanish_title,
                    "jap_title": b.jap_title,
                    "volume": float(b.volume) if b.volume is not None else None,
                    "author": b.author,
                    "illustrator": b.illustrator,
                    "translator": b.translator,
                    "layout_by": b.layout_by,
                    "publisher": b.publisher,
                    "isbn": b.isbn,
                    "asin": b.asin,
                    "uri_id": b.uri_id,
                    "published_at": b.published_at,
                    "modified_at_opf": b.modified_at_opf,
                    "book_type": b.book_type,
                    "epub_version": b.epub_version,
                    "word_count": b.word_count,
                    "page_count": b.page_count,
                    "reading_time": b.reading_time,
                    "rating_average": b.rating_average,
                    "rating_count": b.rating_count,
                    "description": b.description,
                    "demographics": b.demographics,
                    "tags": b.tags,
                    "language": b.language,
                    # Cover images - all quality levels
                    "cover_original": b.cover_original,
                    "cover_high": b.cover_high,
                    "cover_medium": b.cover_medium,
                    "cover_low": b.cover_low,
                    # Legacy cover paths for backward compatibility
                    "cover_path": b.cover_low or b.cover_medium,  # Fallback to low quality
                    "cover_thumb_path": b.cover_low,  # Thumbnail is now low quality
                    "file_created_at": b.file_created_at.isoformat() if b.file_created_at else None,
                    "file_modified_at": b.file_modified_at.isoformat() if b.file_modified_at else None,
                    "indexed_at": b.indexed_at.isoformat() if b.indexed_at else None,
                    "series_hash": b.series_hash,
                    "content_hash": b.content_hash,
                    "book_hash": b.book_hash or b.content_hash  # Use book_hash, fallback to content_hash
                })
            client.table('local_books').upsert(books_data).execute()
            
        session.close()
        return {"success": True, "message": f"Sincronizados {len(sources)} fuentes y {len(books)} libros."}
    except Exception as e:
        logger.error(f"Error backup library to Supabase: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_sync_users_cloud(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Sincroniza usuarios y niveles locales a Supabase."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}

    try:
        from core.db_manager import db_manager
        from core.supabase_manager import supabase_manager
        import json
        
        client = supabase_manager.get_client()
        
        async with db_manager.connection() as conn:
            # 1. Sync User Levels
            cursor = await conn.execute("SELECT * FROM user_levels")
            levels = await cursor.fetchall()
            
            # Get columns from user_levels
            cursor = await conn.execute("PRAGMA table_info(user_levels)")
            lvl_cols = [c[1] for c in await cursor.fetchall()]
            
            for lvl in levels:
                lvl_data = {}
                for idx, col in enumerate(lvl_cols):
                    val = lvl[idx]
                    # Map SQLite names to Supabase if needed, or keep same
                    lvl_data[col] = val
                
                # Special handling for Supabase bools if SQLite stored 0/1
                bool_cols = ["has_mini_app_access", "early_access", "custom_themes", "show_recommendations", "can_download", "can_read"]
                for bc in bool_cols:
                    if bc in lvl_data:
                        lvl_data[bc] = bool(lvl_data[bc])

                client.table('user_levels').upsert(lvl_data).execute()

            # 2. Sync Users
            cursor = await conn.execute("SELECT * FROM users")
            users = await cursor.fetchall()
            
            cursor = await conn.execute("PRAGMA table_info(users)")
            usr_cols = [c[1] for c in await cursor.fetchall()]
            
            user_batch = []
            for u in users:
                u_data = {}
                for idx, col in enumerate(usr_cols):
                    val = u[idx]
                    u_data[col] = val
                
                # Handle dates and JSON
                if u_data.get("added_at"):
                    if isinstance(u_data["added_at"], str):
                        pass # SQLite stores as string
                
                if u_data.get("expires_at") and not isinstance(u_data["expires_at"], str):
                    u_data["expires_at"] = u_data["expires_at"].isoformat()

                # Boolean fix
                for bc in ["has_library_access", "can_request_books"]:
                    if bc in u_data:
                        u_data[bc] = bool(u_data[bc])

                # JSON parse/re-encode to ensure validity
                for jc in ["insignias", "settings"]:
                    if u_data.get(jc):
                        try:
                            if isinstance(u_data[jc], str):
                                u_data[jc] = json.loads(u_data[jc])
                        except:
                            pass
                
                # Remove columns that don't exist in Supabase
                # custom_status was renamed to 'role'
                if "custom_status" in u_data:
                    if not u_data.get("role"):
                        u_data["role"] = u_data["custom_status"]
                    del u_data["custom_status"]
                
                # Remove 'roles' column (consolidated into 'insignias')
                if "roles" in u_data:
                    del u_data["roles"]
                
                user_batch.append(u_data)
                
                if len(user_batch) >= 50:
                    client.table('users').upsert(user_batch).execute()
                    user_batch = []
            
            if user_batch:
                client.table('users').upsert(user_batch).execute()

        return {"success": True, "message": f"Sincronizados {len(levels)} niveles y {len(users)} usuarios a la nube."}
    except Exception as e:
        logger.error(f"Error syncing users to Supabase: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_scan_library(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Activates forced library scan."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    force = data.get("force", False)
    
    async def run_scan_in_background(scanner_obj, force_val):
        try:
            logger.info(f"Background scan started (Force: {force_val})")
            await asyncio.to_thread(scanner_obj.sync_all, force_scan=force_val)
            logger.info("Background scan completed successfully.")
        except Exception as e:
            logger.error(f"Background scan error: {e}")

    try:
        from services.scanner_service import ScannerService
        
        if ScannerService._is_scanning:
            return {"success": False, "message": "⚠️ Ya hay un escaneo de librería en progreso."}

        libs_json = os.getenv("LOCAL_LIBRARIES")
        if not libs_json:
            return {"success": False, "message": "LOCAL_LIBRARIES no configurada."}
            
        scanner = ScannerService(libs_json)
        
        # Start the intensive task in background and return immediately
        # to avoid Cloudflare 524 (Timeout) errors
        asyncio.create_task(run_scan_in_background(scanner, force))
        
        return {
            "success": True, 
            "message": "Escaneo iniciado en segundo plano. Esto puede tardar varios minutos dependiendo del tamaño de la librería."
        }
    except Exception as e:
        logger.error(f"Error starting background scan: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_enrich_metadata(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Activates manual enrichment of metadata from online sources."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    async def run_enrichment_in_background(scanner_obj):
        try:
            logger.info("Background metadata enrichment started")
            await asyncio.to_thread(scanner_obj.enrich_all_metadata)
            logger.info("Background metadata enrichment completed.")
        except Exception as e:
            logger.error(f"Background enrichment error: {e}")

    try:
        from services.scanner_service import ScannerService
        libs_json = os.getenv("LOCAL_LIBRARIES")
        scanner = ScannerService(libs_json or "{}")
        
        asyncio.create_task(run_enrichment_in_background(scanner))
        
        return {
            "success": True, 
            "message": "Enriquecimiento de metadatos iniciado en segundo plano. Se procesarán libros con ISBN que no tengan título en español o descripción."
        }
    except Exception as e:
        logger.error(f"Error starting enrichment task: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_reset_library(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Reset complete library database (admin only, requires confirmation)."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Require explicit confirmation
    confirmed = data.get("confirmed", False)
    if not confirmed:
        return {
            "success": False, 
            "message": "Confirmación requerida para eliminar la base de datos.",
            "requireConfirmation": True
        }
    
    try:
        from utils.library_db import DB_PATH, COVERS_DIR, engine
        import sqlalchemy as sa
        
        items_deleted = []
        cover_count = 0
        
        # 0. If Postgres, clear tables instead of deleting file
        if engine.url.drivername != "sqlite":
            try:
                with engine.begin() as conn:
                    # Order of deletion matters due to FKs
                    conn.execute(sa.text("DELETE FROM user_ratings"))
                    conn.execute(sa.text("DELETE FROM user_downloads"))
                    conn.execute(sa.text("DELETE FROM local_books"))
                    conn.execute(sa.text("DELETE FROM library_sources"))
                items_deleted.append("Tablas de PostgreSQL limpiadas (local_books, sources, ratings, downloads)")
            except Exception as e:
                logger.error(f"Error clearing Postgres tables: {e}")
                return {"success": False, "message": f"Error limpiando tablas Postgres: {e}"}
        else:
            # 1. Delete SQLite database file
            if os.path.exists(DB_PATH):
                try:
                    os.remove(DB_PATH)
                    items_deleted.append("Archivo de base de datos SQLite eliminado")
                except Exception as e:
                    logger.error(f"Error deleting DB: {e}")
                    return {"success": False, "message": f"Error eliminando base de datos: {e}"}
            else:
                items_deleted.append("Base de datos SQLite no existía")
        
        # 2. Delete covers directory
        if os.path.exists(COVERS_DIR):
            try:
                cover_count = len([f for f in os.listdir(COVERS_DIR) if os.path.isfile(os.path.join(COVERS_DIR, f))])
                shutil.rmtree(COVERS_DIR)
                items_deleted.append(f"{cover_count} portadas eliminadas")
            except Exception as e:
                logger.error(f"Error deleting covers: {e}")
                items_deleted.append(f"Error eliminando portadas: {e}")
        else:
            items_deleted.append("Directorio de portadas no existía")
        
        # 3. Recreate covers directory
        try:
            os.makedirs(COVERS_DIR, exist_ok=True)
            items_deleted.append("Directorio de portadas recreado")
        except Exception as e:
            logger.error(f"Error recreating covers dir: {e}")
            items_deleted.append(f"Error recreando directorio: {e}")
        
        # 4. Recreate database with proper schema to avoid readonly issues
        try:
            from utils.library_db import init_library_db
            
            # Initialize database with all tables
            init_library_db()
            items_deleted.append("Base de datos recreada con esquema correcto")
        except Exception as e:
            logger.error(f"Error recreating database schema: {e}")
            items_deleted.append(f"Advertencia recreando esquema: {e}")
        
        logger.info(f"Admin {user_data.get('telegram_id')} reset library database. {cover_count} covers deleted.")
        
        return {
            "success": True, 
            "message": "Base de datos local reseteada exitosamente.",
            "details": items_deleted,
            "coversDeleted": cover_count
        }
    except Exception as e:
        logger.error(f"Error en handle_admin_reset_library: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_restart_docker(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Restart Docker container (admin only)."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        import subprocess
        
        # Get container name from environment
        container_name = os.getenv("CONTAINER_NAME", "zeepub-bot")
        
        logger.info(f"Admin {user_data.get('telegram_id')} requesting Docker restart for container: {container_name}")
        
        async def do_restart():
            try:
                # Execute docker restart command in thread
                await asyncio.to_thread(subprocess.run, ["docker", "restart", container_name], timeout=30)
            except Exception as e:
                logger.error(f"Error in background docker restart: {e}")

        # Start in background
        asyncio.create_task(do_restart())
        
        return {
            "success": True,
            "message": f"Contenedor {container_name} reiniciándose...",
            "restarting": True
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Timeout al ejecutar comando docker"}
    except FileNotFoundError:
        return {"success": False, "message": "Docker no está disponible en el sistema"}
    except Exception as e:
        logger.error(f"Error en handle_admin_restart_docker: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_update_system(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Trigger system update (git pull + restart) using existing bot infrastructure."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        from services.maintenance_service import trigger_watchtower_update
        
        logger.info(f"Admin {user_data.get('telegram_id')} requesting system update via Watchtower")
        
        # Ejecutar en segundo plano para evitar 502/504 de Nginx/Cloudflare
        asyncio.create_task(trigger_watchtower_update())
        
        return {
            "success": True,
            "message": "Actualización solicitada. El bot contactará con Watchtower para buscar nuevas versiones y se reiniciará si es necesario.",
            "restarting": True
        }
    except Exception as e:
        logger.error(f"Error en handle_admin_update_system: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_save_tier_config(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Guarda la configuración completa de un nivel/tier."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    tier_name = data.get("name")
    try:
        if tier_name == "Global" or (tier_name and "Global" in str(tier_name)) or data.get("id") == "global":
            # Global settings are stored in bot_settings table
            # Filter out non-UI fields for global UI defaults
            ui_settings = {}
            field_mapping = {
                "primaryColor": "primaryColor",
                "glassOpacity": "glassOpacity",
                "navOpacity": "navOpacity",
                "glassBlur": "glassBlur",
                "coverWidth": "coverWidth",
                "showRecommendations": "showRecommendations",
                "theme": "theme",
                "fontSize": "fontSize",
                "accentOpacity": "accentOpacity",
                "canDownload": "canDownload",
                "canRead": "canRead",
                "hasLibraryAccess": "hasLibraryAccess",
                "canRequestBooks": "canRequestBooks",
                "bannerContentOffset": "bannerContentOffset",
                "backgroundColor": "backgroundColor",
                "cardColor": "cardColor",
                "forceSettings": "forceSettings",
                "cardGlowIntensity": "cardGlowIntensity",
                "allowThemeTemplates": "allowThemeTemplates"
            }
            
            for frontend_key, setting_key in field_mapping.items():
                if frontend_key in data:
                    val = data[frontend_key]
                    if frontend_key == "glassOpacity" or frontend_key == "navOpacity" or frontend_key == "accentOpacity":
                        # If value is > 1, it's likely a percentage (0-100)
                        if isinstance(val, (int, float)) and val > 1:
                            val = val / 100.0
                    ui_settings[setting_key] = val
            
            # Additional fields that might be in data but not in mapping
            if "name" in data: ui_settings["name"] = data["name"]
            
            current_global = json.loads(get_setting("ui_defaults_global", "{}"))
            current_global.update(ui_settings)
            set_setting("ui_defaults_global", json.dumps(current_global))
            
            # Record change for audit if needed (can be added later)
            logger.info(f"ADMIN: Saved GLOBAL tier config locally and to Supabase (if active)")
            return {"success": True, "tierId": "global"}

        # from core.supabase_client import get_supabase_client
        client = supabase_manager.get_client()
        
        # Find tier by name
        result = client.table('user_levels').select('id').ilike('name', tier_name).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Tier '{tier_name}' no encontrado")
        
        tier_id = result.data[0]['id']
        
        # Build update data
        update_data = {
            "updated_at": "now()"
        }
        
        # Map frontend fields to database columns
        field_mapping = {
            "name": "name",
            "icon": "icon",
            "color": "color",
            "dailyDownloads": "daily_downloads",
            "maxConcurrent": "max_concurrent",
            "priorityRequests": "priority_requests",
            "earlyAccess": "early_access",
            "customThemes": "custom_themes",
            "primaryColor": "ui_primary_color",
            "glassOpacity": "panel_transparency",
            "theme": "ui_theme",
            "fontSize": "ui_font_size",
            "glassBlur": "ui_glass_blur",
            "coverWidth": "ui_cover_width",
            "navOpacity": "ui_nav_opacity",
            "accentOpacity": "ui_accent_opacity",
            "showRecommendations": "show_recommendations",
            "canDownload": "can_download",
            "canRead": "can_read",
            "hasLibraryAccess": "has_library_access",
            "canRequestBooks": "can_request_books",
            "bannerContentOffset": "banner_content_offset",
            "backgroundColor": "background_color",
            "cardColor": "card_color",
            "forceSettings": "force_settings",
            "cardGlowIntensity": "ui_glow_intensity",
            "ui_exported_settings": "ui_exported_settings",
            "allowThemeTemplates": "allow_theme_templates"
        }
        
        for frontend_key, db_key in field_mapping.items():
            if frontend_key in data and data[frontend_key] is not None:
                val = data[frontend_key]
                # Special handling for panel_transparency (expects int 0-100, frontend sends float 0-1)
                if db_key == "panel_transparency":
                    try:
                        val = int(float(val) * 100)
                    except (ValueError, TypeError):
                        val = 70 # Fallback default
                
                update_data[db_key] = val
        
        # Update tier in Supabase
        try:
            client.table('user_levels').update(update_data).eq('id', tier_id).execute()
        except Exception as e:
            msg = str(e)
            if "Could not find the" in msg and "column" in msg:
                logger.warning(f"Supabase schema missing columns. Retrying with basic fields only. Error: {msg}")
                # Retry with only core fields that surely exist
                core_fields = ["name", "icon", "color", "daily_downloads", "priority_requests"]
                safe_data = {k: v for k, v in update_data.items() if k in core_fields or k == "updated_at"}
                if safe_data:
                    client.table('user_levels').update(safe_data).eq('id', tier_id).execute()
                    return {"success": True, "tierId": tier_id, "warning": "Partial save: Schema update required"}
            raise e
        
        # Update tier locally (SQLite)
        try:
            from repositories.user_repository import user_repo
            await user_repo.update_level(tier_id, data)
        except Exception as e:
            logger.error(f"Error updating tier locally: {e}")
            # Non-fatal, we continue since Supabase was updated
        
        logger.info(f"ADMIN: Saved tier config for '{tier_name}' (ID: {tier_id}) in Cloud and Local")
        return {"success": True, "tierId": tier_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving tier config: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_tier_config(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Obtiene la configuración completa de un nivel/tier."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    tier_name = data.get("name")
    tier_id = data.get("id")
    
    try:
        # Check if it's the global tier (case-insensitive)
        is_global = False
        if tier_id and str(tier_id).lower() == "global":
            is_global = True
        elif tier_name and "global" in str(tier_name).lower():
            is_global = True

        if is_global:
            global_raw = get_setting("ui_defaults_global", "{}")
            g = json.loads(global_raw)
            global_config = {
                "id": "global",
                "name": "Global",
                "icon": "globe",
                "color": "#ffffff",
                "dailyDownloads": -1,
                "maxConcurrent": 10,
                "priorityRequests": True,
                "earlyAccess": True,
                "customThemes": True,
                "primaryColor": g.get("primaryColor", "#2b6cee"),
                "glassOpacity": g.get("glassOpacity", 0.6),
                "theme": g.get("theme", "dark"),
                "fontSize": g.get("fontSize", 14),
                "glassBlur": g.get("glassBlur", 12),
                "coverWidth": g.get("coverWidth", 120),
                "navOpacity": g.get("navOpacity", 0.8),
                "accentOpacity": g.get("accentOpacity", 0.2),
                "showRecommendations": g.get("showRecommendations", True),
                "canDownload": g.get("canDownload", True),
                "canRead": g.get("canRead", True),
                "forceSettings": g.get("forceSettings", False),
                "cardGlowIntensity": g.get("cardGlowIntensity", 0.5),
                "backgroundColor": g.get("backgroundColor", "#0f172a"),
                "cardColor": g.get("cardColor", "#1e293b"),
                "bannerContentOffset": g.get("bannerContentOffset", 0)
            }
            return {
                "success": True,
                "config": global_config,
                "tier": global_config
            }

        # Use cached repo method instead of direct Supabase call
        tier = None
        if tier_id:
            tier = await user_repo.get_level_by_id(int(tier_id))
        else:
            # Fallback to fetching all and finding by name if no ID
            all_lvls = await user_repo.get_all_levels()
            tier = next((l for l in all_lvls if l['name'].lower() == tier_name.lower()), None)
        
        if not tier:
            raise HTTPException(status_code=404, detail="Tier no encontrado")
        
        # Maps keys (note: user_repo.get_level_by_id already does most of this mapping)
        return {
            "success": True,
            "config": tier,
            "tier": tier
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tier config: {e}")
        raise HTTPException(status_code=500, detail=str(e))



async def handle_admin_get_themes(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Retorna la lista de plantillas de temas disponibles."""
    # Relaxed permission: Allow all authorized mini-app users to view themes (controlled by UI)
    # if user_data.get("level") != "admin":
    #    raise HTTPException(status_code=403, detail="No tienes permisos")
    
    from repositories.theme_repository import theme_repo
    try:
        themes = await theme_repo.get_all_themes()
        return {"success": True, "themes": themes}
    except Exception as e:
        logger.error(f"Error fetching themes: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_save_theme(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Guarda una configuración actual como una plantilla de tema."""
    if user_data.get("level") != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    theme_name = data.get("name")
    if not theme_name:
        return {"success": False, "message": "El tema necesita un nombre"}
    
    import re
    # Clean name: remove trailing numbers that look like " 2", " 3"
    theme_name = re.sub(r'\s+\d+$', '', theme_name).strip()
    
    from repositories.theme_repository import theme_repo
    
    # Ensure name uniqueness if it's a new theme request
    if data.get("is_new"):
        existing_themes = await theme_repo.get_all_themes()
        existing_names = [t['name'] for t in existing_themes]
        
        if theme_name in existing_names:
            # Avoid ending in " 2"
            suffixes = ["(Nuevo)", "(Alt)", "(Pro)", "(Custom)", "(Modern)", "(Premium)"]
            unique_found = False
            for s in suffixes:
                candidate = f"{theme_name} {s}"
                if candidate not in existing_names:
                    theme_name = candidate
                    unique_found = True
                    break
            
            if not unique_found:
                import time
                theme_name = f"{theme_name} ({int(time.time() % 1000)})"

    # Map frontend keys to DB columns
    insert_data = {
        "name": theme_name,
        "description": data.get("description", ""),
        "primaryColor": data.get("primaryColor"),
        "glassBlur": data.get("glassBlur"),
        "glassOpacity": data.get("glassOpacity"),
        "navOpacity": data.get("navOpacity"),
        "accentOpacity": data.get("accentOpacity"),
        "cardGlowIntensity": data.get("cardGlowIntensity"),
        "backgroundColor": data.get("backgroundColor"),
        "cardColor": data.get("cardColor"),
        "theme": data.get("theme"),
        "fontSize": data.get("fontSize"),
        "coverWidth": data.get("coverWidth"),
        "bannerContentOffset": data.get("bannerContentOffset")
    }
    
    # Remove None values
    insert_data = {k: v for k, v in insert_data.items() if v is not None}
    
    try:
        res = await theme_repo.upsert(insert_data)
        if not res:
             return {"success": False, "message": "No se pudo guardar el tema"}
        return {"success": True, "theme": res}
    except Exception as e:
        logger.error(f"Error saving theme: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_save_user_permissions(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Guarda los permisos de un usuario específico."""
    logger.info(f"ADMIN: Save permissions request for data: {data}")
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Falta userId")
    
    try:
        from repositories.user_repository import user_repo
        from services.user_service import invalidate_user_cache
        from services.user_audit_service import UserAuditService
        from datetime import datetime
        import asyncio
        
        # Get existing user to preserve values if not provided
        existing = await user_repo.get_by_id(int(user_id))
        if not existing:
             # Create minimal user if not exists
             await user_repo.create_minimal_user(int(user_id))
             existing = await user_repo.get_by_id(int(user_id))

        # Parse expires_at if provided
        expires_at = None
        if data.get("expiresAt"):
            try:
                from dateutil import parser
                expires_at = parser.parse(data["expiresAt"])
            except Exception:
                pass
        
        # Build upsert arguments
        # Map frontend 'role' and 'levelId'
        level_id = data.get("levelId", existing.get("level_id", 6))
        role = data.get("role", existing.get("role", "free"))
        
        # Admin safety
        if data.get("isAdmin"):
            role = "admin"
            level_id = 1
        
        # Track changes for audit log
        changes = {}
        
        # Check level change
        old_level_id = int(existing.get("level_id") or 6)
        if int(level_id) != old_level_id:
            changes["level"] = {
                "old": {"id": old_level_id, "name": existing.get("level")},
                "new": {"id": int(level_id), "name": data.get("levelName", "Unknown")}
            }
        
        # Check role change
        old_role = existing.get("role")
        if role != old_role:
            changes["role"] = {"old": old_role, "new": role}
        
        # Check other permission changes
        fields_to_track = {
            "role": "role",
            "nickname": "nickname",
            "name": "name",
            "username": "username",
            "betaTester": "beta_tester",
            "expiresAt": "expires_at",
            "canRequestBooks": "can_request_books",
            "hasLibraryAccess": "has_library_access"
        }
        
        for frontend_key, db_key in fields_to_track.items():
            if frontend_key in data:
                old_val = existing.get(db_key)
                new_val = data[frontend_key]
                if frontend_key == "expiresAt":
                    new_val = expires_at.isoformat() if expires_at else None
                    old_val = existing.get(db_key).isoformat() if existing.get(db_key) else None
                
                if old_val != new_val:
                    changes[db_key] = {"old": old_val, "new": new_val}
        
        # Check insignias changes
        old_insignias = existing.get("insignias", [])
        new_insignias = data.get("insignias", existing.get("insignias", []))
        if set(old_insignias or []) != set(new_insignias or []):
            changes["insignias"] = {"old": old_insignias, "new": new_insignias}
        
        # Save to database
        await user_repo.upsert(
            telegram_id=int(user_id),
            level=data.get("level", "free"), # Assuming level is passed or use role if it means tier
            expires_at=expires_at or existing.get("expires_at"),
            role=data.get("role", existing.get("role")),
            nickname=data.get("nickname", existing.get("nickname")),
            name=data.get("name", existing.get("name")),
            username=data.get("username", existing.get("username")),
            roles=data.get("roles", existing.get("roles", [])),
            insignias=new_insignias,
            created_by=int(user_data.get("telegram_id", 0)),
            has_library_access=data.get("hasLibraryAccess"),
            can_request_books=data.get("canRequestBooks"),
            level_id=level_id
        )
        
        # betaTester is handled separately if needed, or we could add it to upsert too
        if config.ENABLE_SUPABASE and "betaTester" in data:
            supabase_manager.get_client().table('users').update({"beta_tester": data["betaTester"]}).eq('telegram_id', int(user_id)).execute()

        # Log changes to audit log if there were any
        if changes:
            try:
                UserAuditService.log_permissions_change(
                    user_id=str(user_id),
                    username=data.get("username") or existing.get("username") or f"User_{user_id}",
                    changes=changes,
                    changed_by_id=str(user_data.get("telegram_id", 0)),
                    changed_by_username=user_data.get("username", "Admin")
                )
                logger.info(f"[Audit] Logged {len(changes)} changes for user {user_id}")
            except Exception as audit_error:
                logger.error(f"Error logging audit: {audit_error}")
                # Don't fail the whole operation if audit logging fails

        # Invalidate cache
        asyncio.create_task(invalidate_user_cache(int(user_id)))
        
        logger.info(f"ADMIN: Saved user permissions for user {user_id}")
        return {"success": True, "changes_logged": len(changes)}
    except Exception as e:
        logger.error(f"Error saving user permissions: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_user_permissions(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Obtiene los permisos de un usuario específico."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Falta userId")
    
    try:
        from repositories.user_repository import user_repo
        
        # Get extended info joining with levels
        access_info = await user_repo.get_access_info(int(user_id))
        # Get raw user info for fields not in access_info
        raw_user = await user_repo.get_by_id(int(user_id))
        
        if not access_info or not raw_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {
            "success": True,
            "user": {
                "id": str(user_id),
                "username": raw_user.get("username") or "",
                "name": raw_user.get("name") or raw_user.get("nickname") or "Usuario",
                "nickname": raw_user.get("nickname") or "",
                "level": raw_user.get("level", "free"),
                "roles": raw_user.get("roles") or [],
                "levelId": int(access_info["level"]["id"]),
                "levelName": access_info["level"]["name"],
                "levelColor": access_info["level"].get("color", "#3b82f6"),
                "role": raw_user.get("role"),
                "expiresAt": raw_user["expires_at"].isoformat() if raw_user.get("expires_at") and hasattr(raw_user["expires_at"], "isoformat") else None,
                "isAdmin": access_info["isAdmin"],
                "betaTester": raw_user.get("beta_tester", access_info["isBetaTester"]),
                "hasLibraryAccess": raw_user.get("has_library_access", True),
                "canRequestBooks": raw_user.get("can_request_books", True),
                "insignias": raw_user.get("insignias") or [],
                "photo_url": access_info.get("photo_url") or raw_user.get("photo_url")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_find_duplicates(data: Dict[str, Any], user_data: Dict[str, Any]):
    """
    Find all duplicate books grouped by content_hash.
    Returns duplicate groups with file info and statistics.
    """
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        from utils.library_db import get_session
        from models.library_models import LocalBook
        from sqlalchemy import func
        
        session = get_session()
        
        # Query to find duplicates
        duplicate_hashes = session.query(
            LocalBook.content_hash,
            func.count().label('count')
        ).filter(
            LocalBook.content_hash.isnot(None)
        ).group_by(
            LocalBook.content_hash
        ).having(
            func.count() > 1
        ).all()
        
        duplicate_groups = []
        total_wasted_space = 0
        total_duplicates = 0
        
        for hash_row in duplicate_hashes:
            content_hash = hash_row[0]
            
            # Get all books with this hash
            books = session.query(LocalBook).filter(
                LocalBook.content_hash == content_hash
            ).order_by(
                LocalBook.indexed_at.asc()
            ).all()
            
            if len(books) <= 1:
                continue
            
            # Calculate stats
            file_sizes = [book.file_size or 0 for book in books]
            total_size = sum(file_sizes)
            min_size = min(file_sizes) if file_sizes else 0
            wasted_space = total_size - min_size
            
            total_wasted_space += wasted_space
            total_duplicates += len(books) - 1
            
            group = {
                "content_hash": content_hash,
                "title": books[0].title,
                "author": books[0].author,
                "series": books[0].series,
                "volume": books[0].volume,
                "count": len(books),
                "total_size": total_size,
                "wasted_space": wasted_space,
                "books": [
                    {
                        "id": book.id,
                        "filepath": book.filepath,
                        "filename": book.filename,
                        "file_size": book.file_size or 0,
                        "indexed_at": book.indexed_at.isoformat() if book.indexed_at else None,
                        "is_oldest": book.id == books[0].id,
                        "is_newest": book.id == books[-1].id
                    }
                    for book in books
                ]
            }
            
            duplicate_groups.append(group)
        
        duplicate_groups.sort(key=lambda x: x['wasted_space'], reverse=True)
        session.close()
        
        return {
            "success": True,
            "duplicate_groups": duplicate_groups,
            "summary": {
                "total_duplicates": total_duplicates,
                "duplicate_groups_count": len(duplicate_groups),
                "wasted_space_bytes": total_wasted_space,
                "wasted_space_mb": round(total_wasted_space / (1024 * 1024), 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error finding duplicates: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_delete_duplicate(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Delete duplicate books safely, ensuring at least one copy remains."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    book_ids = data.get("book_ids", [])
    if not book_ids:
        return {"success": False, "message": "No se especificaron libros"}
    
    try:
        from utils.library_db import get_session, COVERS_DIR
        from models.library_models import LocalBook
        from sqlalchemy import func
        from collections import defaultdict
        import os
        
        session = get_session()
        
        books_to_delete = session.query(LocalBook).filter(
            LocalBook.id.in_(book_ids)
        ).all()
        
        if not books_to_delete:
            return {"success": False, "message": "No se encontraron libros"}
        
        # Group by content_hash
        by_hash = defaultdict(list)
        for book in books_to_delete:
            by_hash[book.content_hash].append(book)
        
        deleted_count = 0
        deleted_size = 0
        errors = []
        
        for content_hash, books in by_hash.items():
            # Count total books with this hash
            total_with_hash = session.query(func.count(LocalBook.id)).filter(
                LocalBook.content_hash == content_hash
            ).scalar()
            
            # Can't delete all copies
            if len(books) >= total_with_hash:
                errors.append(f"No se puede eliminar todas las copias de {books[0].title}")
                continue
            
            # Delete files
            for book in books:
                try:
                    if book.filepath and os.path.exists(book.filepath):
                        os.remove(book.filepath)
                    
                    if book.cover_path:
                        cover_file = book.cover_path.replace('/api/library/covers/', '')
                        cover_path = os.path.join(COVERS_DIR, cover_file)
                        if os.path.exists(cover_path):
                            os.remove(cover_path)
                        thumb_path = cover_path.replace('.jpg', '_thumb.jpg')
                        if os.path.exists(thumb_path):
                            os.remove(thumb_path)
                    
                    deleted_size += book.file_size or 0
                    session.delete(book)
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"Error deleting book {book.id}: {e}")
                    errors.append(f"Error: {book.filename}")
        
        session.commit()
        session.close()
        
        result = {
            "success": True,
            "deleted_count": deleted_count,
            "freed_space_mb": round(deleted_size / (1024 * 1024), 2)
        }
        
        if errors:
            result["errors"] = errors
        
        return result
        
    except Exception as e:
        logger.error(f"Error deleting duplicates: {e}")
        session.rollback()
        session.close()
        return {"success": False, "message": str(e)}


async def handle_update_user_setting(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Actualiza una o múltiples configuraciones del usuario."""
    from services.user_service import update_user_setting
    
    user_id = user_data.get("user_id")
    
    # Support two modes:
    # 1. Single setting: { "key": "show_recommendations", "value": true }
    # 2. Bulk settings: { "settings": { "primaryColor": "#xxx", "theme": "dark", ... } }
    
    settings_obj = data.get("settings")
    
    if settings_obj:
        # Bulk update mode
        try:
            logger.info(f"User {user_id} updating {len(settings_obj)} settings")
            await user_repo.update_user_settings(user_id, settings_obj)
            return {"success": True, "message": "Settings updated"}
        except Exception as e:
            logger.error(f"Error bulk updating user settings for {user_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Single setting mode (legacy)
        key = data.get("key")
        value = data.get("value")
        
        if not key:
            raise HTTPException(status_code=400, detail="Missing 'key' or 'settings' parameter")
        
        try:
            logger.info(f"User {user_id} updating setting: {key} = {value}")
            result = await update_user_setting(user_id, key, value)
            return {"success": True, "settings": result}
        except Exception as e:
            logger.error(f"Error updating user setting for {user_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))


async def handle_get_user_audit_history(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Obtiene el historial de cambios de un usuario."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Falta userId")
    
    try:
        from services.user_audit_service import UserAuditService
        
        limit = data.get("limit", 50)
        offset = data.get("offset", 0)
        
        history = UserAuditService.get_user_history(
            user_id=str(user_id),
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting user audit history: {e}")
        return {"success": False, "message": str(e)}
        
        
async def handle_admin_get_recent_audit_logs(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Obtiene los cambios recientes en el sistema."""
    user_level = user_data.get("level", "free")
    if user_level != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        from services.user_audit_service import UserAuditService
        
        limit = data.get("limit", 100)
        offset = data.get("offset", 0)
        
        recent = UserAuditService.get_recent_changes(
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "logs": recent,
            "count": len(recent)
        }
    except Exception as e:
        logger.error(f"Error getting recent audit logs: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_duplicates(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Retorna la lista de archivos duplicados detectados."""
    if user_data.get("level") != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    session = get_session()
    try:
        dups = session.query(DuplicateBook).order_by(desc(DuplicateBook.detected_at)).all()
        
        result = []
        for d in dups:
            result.append({
                "id": d.id,
                "title": d.title,
                "author": d.author,
                "hash": d.book_hash,
                "original": d.original_filepath,
                "duplicate": d.duplicate_filepath,
                "detectedAt": d.detected_at.isoformat() if d.detected_at else None
            })
            
        return {"success": True, "duplicates": result}
    except Exception as e:
        logger.error(f"Error fetching duplicates: {e}")
        return {"success": False, "message": str(e)}
    finally:
        session.close()

async def handle_admin_clear_duplicates(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Limpia la tabla de registros de duplicados."""
    if user_data.get("level") != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    session = get_session()
    try:
        session.query(DuplicateBook).delete()
        session.commit()
        return {"success": True, "message": "Registros de duplicados limpiados."}
    except Exception as e:
        logger.error(f"Error clearing duplicates: {e}")
        return {"success": False, "message": str(e)}
    finally:
        session.close()

async def handle_admin_get_system_logs(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Retorna los últimos logs capturados en memoria con opción de filtrado."""
    if user_data.get("level") != "admin" and not user_data.get("is_admin_db"):
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    try:
        from utils.log_manager import log_buffer_handler
        
        level = data.get("level", "INFO")
        hours = data.get("hours") # None for all in buffer
        
        logs = log_buffer_handler.get_logs(level=level, last_hours=hours)
        return {"success": True, "logs": logs}
    except Exception as e:
        logger.error(f"Error fetching system logs: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_send_logs_telegram(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Envía los logs capturados directamente al chat de Telegram del usuario."""
    if user_data.get("level") != "admin" and not user_data.get("is_admin_db"):
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    try:
        from utils.log_manager import log_buffer_handler
        from api.main import bot as bot_instance
        import io
        from datetime import datetime

        level = data.get("level", "DEBUG") 
        hours = data.get("hours")
        
        logs = log_buffer_handler.get_logs(level=level, last_hours=hours)
        if not logs:
            return {"success": False, "message": "No hay logs disponibles para enviar."}
            
        # Format logs
        log_text = "\n".join([f"[{l['time']}] {l['level']}: {l['msg']}" for l in logs])
        
        # Create file
        file_obj = io.BytesIO(log_text.encode('utf-8'))
        
        # Filename with range
        first_t = logs[0]['timestamp']
        last_t = logs[-1]['timestamp']
        fmt = lambda t: datetime.fromtimestamp(t).strftime('%Y%m%d_%H%M')
        filename = f"logs_{fmt(first_t)}_{fmt(last_t)}.txt"
        file_obj.name = filename
        
        user_id = user_data.get("user_id")
        
        # Send via Telegram
        await bot_instance.app.bot.send_document(
            chat_id=user_id,
            document=file_obj,
            caption=f"📄 <b>Logs del Sistema</b>\nFiltro: {level}\nPeriodo: {fmt(first_t)} a {fmt(last_t)}",
            parse_mode="HTML"
        )
        
        return {"success": True, "message": "Logs enviados a tu Telegram correctamente."}
    except Exception as e:
        logger.error(f"Error sending logs to Telegram: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}
