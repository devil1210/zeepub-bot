import asyncio
import json
import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import desc, func, or_, select

from config.config_settings import config
from core.db_manager_pg import pg_manager
from core.state_manager import state_manager
from core.supabase_manager import supabase_manager
from models.library_models import AILearningFeedback, DuplicateBook, LibrarySource, LocalBook, UploadBook, SeriesMetadata, MetadataProposal
from repositories.download_repository import download_repo
from repositories.user_repository import user_repo
from services.library_service import LibraryService
from services.opds_service import get_cached_feed
from services.rating_service import RatingService
from services.rbac_service import rbac_service
from services.settings_service import get_setting, set_setting
from services.telegram_service import enviar_libro_directo
from utils.helpers import (
    limpiar_html_basico,
    parse_metadata_from_title,
)
from utils.library_db import get_session

logger = logging.getLogger(__name__)


def check_admin(user_data: dict[str, Any]):
    uid = user_data.get("user_id") or user_data.get("telegram_id")
    if not rbac_service.is_admin(user_data):
        logger.warning(f"Admin Access Denied for user {uid} (Level: {user_data.get('level')})")
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requieren permisos de Administrador")


def check_staff(user_data: dict[str, Any]):
    uid = user_data.get("user_id") or user_data.get("telegram_id")
    if not rbac_service.is_staff(user_data):
        logger.warning(f"Staff Access Denied for user {uid} (Level: {user_data.get('level')})")
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requieren permisos de Staff")

# --- Handlers ---


async def handle_search(data: dict[str, Any], user_data: dict[str, Any]):
    """Busca libros en la base de datos local o en el servidor OPDS."""
    user_data.get("user_id", 0)
    user_data.get("level", "free")
    query = data.get("query")
    page = data.get("page", 1)
    search_type = data.get("type", "todos")
    sort = data.get("sort", "a-z")

    is_local_search = True # Always enforced for web interface
    
    if is_local_search:
        return await LibraryService.search_series(
            query or "", page=page, search_type=search_type, sort_by=sort
        )

    # REMOVED: OPDS Fallback Logic
    return {"results": []}


async def handle_book_detail(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve el detalle de un libro desde la base de datos local o OPDS."""
    user_id = user_data.get("user_id", 0)
    book_id_raw = data.get("bookId")
    logger.info(f"[book-detail] Request received - bookId: {book_id_raw}")

    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    # 1. Series/Group Handling
    if isinstance(book_id_raw, str) and book_id_raw.startswith("series_"):
        s_hash = book_id_raw.replace("series_", "")
        v_limit = data.get("limit", 100)
        v_offset = data.get("offset", 0)
        
        # Obtener metadata oficial de la serie
        async with pg_manager.get_session() as session:
            stmt_s = select(SeriesMetadata).where(SeriesMetadata.series_hash == s_hash)
            res_s = await session.execute(stmt_s)
            series = res_s.scalar_one_or_none()
            
        volumes = await LibraryService.get_series_volumes(s_hash, limit=v_limit, offset=v_offset)
        if not series and not volumes:
            raise HTTPException(status_code=404, detail="Serie no encontrada")
        
        # Representative for fields not in SeriesMetadata or fallback
        rep = volumes[0] if volumes else {}
        
        return {
            "id": book_id_raw,
            "series_hash": s_hash,
            "title": series.series_name if series else (rep.get("series") or rep.get("title")),
            "series_spanish": series.series_spanish if series else None,
            "author": series.author if series else rep.get("author"),
            "summary": series.description if series else rep.get("description"),
            "cover": series.cover_url if series else rep.get("cover"),
            "rating_average": series.rating_average if series else 0,
            "rating_count": (series.rating_count if series else 0) or 0,
            "numBooks": series.book_count if series else len(volumes), 
            "is_uncensored": rep.get("is_uncensored", False) if rep else False,
            "color_mode": rep.get("color_mode") if rep else None,
            "is_series": True,
            "volumes": volumes 
        }

    # 2. Local Book Handling
    if isinstance(book_id_raw, str) and (
        book_id_raw.isdigit() or (book_id_raw.startswith("local_") and not book_id_raw.startswith("series_"))
    ):
        clean_id = int(str(book_id_raw).replace("local_", ""))
        local_book = await LibraryService.get_book_by_id(clean_id)
        
        if local_book:
            logger.info(
                f"[book-detail] Found local book: {local_book['title']} (series_hash: {local_book.get('series_hash')})"
            )
            
            # Enrich with download info
            local_book["is_downloaded"] = await download_repo.has_user_downloaded(
                user_id,
                local_book["title"],
                local_book.get("cleanTitle"),
                local_book.get("book_hash"),
            )
            local_book["download_count"] = await download_repo.get_total_download_count(
                local_book["title"],
                local_book.get("cleanTitle"),
                local_book.get("book_hash"),
            )
            
            # If part of a series, ALWAYS include volumes to avoid "empty volumes list" in frontend
            s_hash = local_book.get("series_hash")
            if s_hash:
                v_limit = data.get("limit", 100)
                v_offset = data.get("offset", 0)
                volumes = await LibraryService.get_series_volumes(s_hash, limit=v_limit, offset=v_offset)
                local_book["volumes"] = volumes
                local_book["is_series"] = True # Treat as series for UI consistency if requested from series detail
                local_book["series_hash"] = s_hash
            else:
                local_book["volumes"] = [local_book]
                local_book["is_series"] = False
                
            return local_book
    
    # OPDS fallback removed
    raise HTTPException(status_code=404, detail="Book not found in local library")


async def handle_bot_info(data: dict[str, Any], user_data: dict[str, Any]):
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

    ui_defaults = {}
    try:
        ui_defaults_raw = get_setting("ui_defaults_global", "{}")
        ui_defaults = json.loads(ui_defaults_raw)
    except:
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
            "glassOpacity": 0.6
        }

    return {
        "name": bot_user.first_name or "ZeePubBot",
        "username": f"@{bot_user.username}" if bot_user.username else "@ZeePubBot",
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
    next_midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
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
            "has_library_access": bool((user_data.get("has_library_access", True) is not False) and (level_info.get("hasLibraryAccess", True) is not False)),
            "can_request_books": bool((user_data.get("can_request_books", True) is not False) and (level_info.get("canRequestBooks", True) is not False)),
            "can_download": bool(level_info.get("canDownload", True) is not False),
            "can_read": bool(level_info.get("canRead", True) is not False),
            "can_upload_epub": bool(user_data.get("can_upload_epub", False) or level_info.get("canUploadEpub", False)),
            "is_real_admin": user_data.get("is_real_admin", False),
            "downloads": {
                "used": int(used or 0),
                "limit": max_dl if max_dl is not None else 999
            }
        },
        "timeUntilReset": f"{hours}h {minutes}m",
        "hasUnlimitedDownloads": max_dl is None and level_key != "banned",
        "isBanned": level_key == "banned",
        "isAdmin": level_key == "admin",
    }


async def handle_user_downloads_history(
    data: dict[str, Any], user_data: dict[str, Any]
):
    """Devuelve el historial reciente de descargas del usuario."""
    user_id = user_data.get("user_id")
    try:
        downloads = await download_repo.get_user_downloads(user_id, limit=20)
        return {"downloads": downloads}
    except Exception as e:
        logger.error(f"Error fetching download history for user {user_id}: {e}")
        return {"downloads": []}


async def handle_recommendations(data: dict[str, Any], user_data: dict[str, Any]):
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
                "book_type": book_data.get("book_type"),
            }
        )
    return {"results": results}


async def handle_rate_book(data: dict[str, Any], user_data: dict[str, Any]):
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

    return await RatingService.rate_book(user_id, book_id, rating)


async def handle_remove_rating(data: dict[str, Any], user_data: dict[str, Any]):
    """Elimina la calificación previa del usuario sobre un libro."""
    user_id = user_data.get("user_id")
    book_id_raw = data.get("bookId")
    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    try:
        book_id = int(str(book_id_raw).replace("local_", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de libro inválido")

    return await RatingService.remove_rating(user_id, book_id)


async def handle_save_badge_config(data: dict[str, Any], user_data: dict[str, Any]):
    """Guarda la configuración global de los badges (solo Admin)."""
    user_level = user_data.get("level", "free")
    if user_level not in ["admin", "staff"]:
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden guardar configuración global",
        )

    set_setting("badge_pos_top", str(data.get("badgeTop", 8)))
    set_setting("badge_pos_right", str(data.get("badgeRight", 8)))
    set_setting("show_pos_tool", str(data.get("showPosTool", False)))
    set_setting("badge_pos_mode", data.get("badgePosMode", "relative"))

    return {"success": True, "message": "Configuración de badge guardada correctamente"}


async def handle_download(data: dict[str, Any], user_data: dict[str, Any]):
    """Envía el archivo del libro directamente a través del bot."""
    from services.identity.identity_service import identity_service
    from services.metadata_orchestrator.metadata_service import metadata_orchestrator
    from services.delivery.delivery_service import delivery_service

    user_id = user_data.get("user_id")
    book_id = data.get("bookId")
    title = data.get("title", "Libro")
    target = data.get("target", "private")
    target_id_override = data.get("targetId")
    thread_id_override = data.get("threadId")

    if not book_id:
        raise HTTPException(status_code=400, detail="Missing bookId")

    # 1. Resolve Target Chat and Thread
    target_chat_id = user_id
    message_thread_id = None
    
    if identity_service.is_admin(user_data):
        if target == "channel":
            target_chat_id = target_id_override or get_setting("mini_app_channel_id", "@ZeePubs")
        elif target == "group":
            target_chat_id = target_id_override or get_setting("mini_app_group_id", "@ZeePubBotTest")
            message_thread_id = thread_id_override

    # 2. Get/Resolve Metadata
    book_metadata = await metadata_orchestrator.resolve_book(book_id)
    if not book_metadata:
        # Fallback for books not in local library but available via URL
        book_metadata = {"title": title, "url": book_id}
        if not book_id.startswith("http"):
            logger.warning(f"Book not found in library and not a URL: {book_id}")

    # 3. Deliver Book
    success = await delivery_service.deliver(
        platform="telegram",
        target_id=user_id,
        book_data=book_metadata,
        options={
            "target_chat_id": target_chat_id,
            "message_thread_id": message_thread_id,
            "title_override": title
        }
    )
    
    return {"success": success}


async def handle_ui_settings(data: dict[str, Any], user_data: dict[str, Any]):
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
            
            # Bidirectional Sync Trigger (Local -> Cloud -> Local)
            from core.optimized_sync_engine import optimized_sync_engine
            await optimized_sync_engine.force_sync_all()
            
            return {"success": True, "message": "Configuración personal guardada y sincronizada con la nube"}
        else:
            if user_level not in ["admin", "staff"]:
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


async def handle_create_stars_invoice(data: dict[str, Any], user_data: dict[str, Any]):
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


async def handle_status(data: dict[str, Any], user_data: dict[str, Any]):
    """Alias para handle_user_status (compatible con acción 'status')."""
    return await handle_user_status(data, user_data)


async def handle_get_download_count(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve el conteo de descargas de un libro específico."""
    book_id_raw = data.get("bookId")
    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    book_id = str(book_id_raw)
    title_for_query = None
    book_hash_for_query = None

    if book_id.startswith("local_") or book_id.isdigit():
        clean_id_int = int(book_id.replace("local_", ""))
        local_book = await LibraryService.get_book_by_id(clean_id_int)
        if local_book:
            title_for_query = local_book["title"]
            local_book.get("cleanTitle")
            book_hash_for_query = local_book.get("book_hash")
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
                    meta.get("clean_title")
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


async def handle_rating_breakdown(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve el desglose de calificaciones para un libro."""
    book_id_raw = data.get("bookId")
    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    try:
        book_id = int(str(book_id_raw).replace("local_", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de libro inválido")

    return {"breakdown": await RatingService.get_rating_breakdown(book_id)}


async def handle_admin_stats(data: dict[str, Any], user_data: dict[str, Any]):
    """Calcula y devuelve estadísticas globales reales desde PostgreSQL para el Panel Admin."""
    check_staff(user_data)

    from sqlalchemy import select, text

    from core.db_manager_pg import pg_manager
    from models.library_models import LocalBook
    
    total_users = 0
    total_books = 0
    dls_24h = 0
    dls_prev_24h = 0
    users_7d = 0
    storage_gb = 0
    total_revenue = 0.0
    
    try:
        async with pg_manager.get_session() as session:
            # 1. Users Metrics
            total_users = (await session.execute(text("SELECT COUNT(*) FROM users"))).scalar() or 0
            users_7d = (await session.execute(text("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days'"))).scalar() or 0
            
            # 2. Book Metrics
            total_books = (await session.execute(select(func.count(LocalBook.id)))).scalar() or 0
            storage_bytes = (await session.execute(select(func.sum(LocalBook.file_size)))).scalar() or 0
            storage_gb = round(storage_bytes / (1024**3), 2) if storage_bytes else 0.0
            
            # 3. Download Metrics
            # Use a more explicit comparison for 24h
            dls_24h = (await session.execute(text("SELECT COUNT(*) FROM download_history WHERE downloaded_at >= (CURRENT_TIMESTAMP - INTERVAL '1 day')"))).scalar() or 0
            dls_prev_24h = (await session.execute(text("SELECT COUNT(*) FROM download_history WHERE downloaded_at >= (CURRENT_TIMESTAMP - INTERVAL '2 days') AND downloaded_at < (CURRENT_TIMESTAMP - INTERVAL '1 day')"))).scalar() or 0
            
            # 4. Revenue Estimation (Real from levels)
            cursor = await session.execute(text("""
                SELECT ul.price, COUNT(u.telegram_id) 
                FROM user_levels ul
                LEFT JOIN users u ON u.level_id = ul.id
                GROUP BY ul.id, ul.price
            """))
            tier_revenue = cursor.fetchall()
            total_revenue = sum((price or 0.0) * count for price, count in tier_revenue)
    except Exception as e:
        logger.error(f"Error fetching global stats from Postgres: {e}")

    # Calculate Uptime
    import time

    from api.main import app_state
    start_time = app_state.get("start_time", time.time())
    uptime_seconds = int(time.time() - start_time)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_text = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"

    # Active Sessions
    active_sessions = len(state_manager.user_state)

    # 5. Popular Book (Last 30 days)
    popular_book = None
    try:
        async with pg_manager.get_session() as session:
            cursor = await session.execute(text("""
                SELECT title, clean_title, book_hash, COUNT(*) as dls
                FROM download_history 
                WHERE downloaded_at >= NOW() - INTERVAL '30 days'
                GROUP BY book_hash, title, clean_title
                ORDER BY dls DESC
                LIMIT 1
            """))
            row = cursor.fetchone()
            if row:
                p_title, p_clean_title, p_book_hash, p_dls = row
                popular_book = {
                    "title": p_clean_title or p_title,
                    "downloads": p_dls,
                    "author": "N/A"
                }
                stmt_lb = select(LocalBook).where(or_(LocalBook.book_hash == p_book_hash, LocalBook.title == p_title))
                lb_res = await session.execute(stmt_lb)
                lb = lb_res.scalar_one_or_none()
                if lb:
                    popular_book["author"] = lb.author
                    popular_book["cover"] = lb.cover_low
    except Exception as e:
        logger.error(f"Error fetching popular book: {e}")

    return {
        "revenue": round(total_revenue, 2),
        "activeSessions": active_sessions,
        "storageUsedGB": storage_gb,
        "storageTotalGB": 1000, 
        "popularBook": popular_book,
        "growthTrend": [
            {"date": "Semana 1", "users": total_users - users_7d, "downloads": dls_prev_24h},
            {"date": "Semana 2", "users": total_users, "downloads": dls_24h}
        ],
        "totalUsers": total_users,
        "users7d": users_7d,
        "totalBooks": total_books,
        "downloads24h": dls_24h,
        "downloadsPrev24h": dls_prev_24h,
        "uptime": uptime_text
    }


async def handle_admin_get_tiers(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene todos los niveles y su configuración."""
    check_staff(user_data)
    
    from services.tier_service import tier_service
    levels = await tier_service.get_all_tiers()
    logger.info(f"ADMIN: handle_admin_get_tiers found {len(levels)} levels")
    return {"success": True, "levels": levels, "tiers": levels}


async def handle_admin_save_tier(data: dict[str, Any], user_data: dict[str, Any]):
    """Guarda cambios en un nivel."""
    check_staff(user_data)
    
    level_id = data.get("id")
    if not level_id:
        raise HTTPException(status_code=400, detail="Falta level_id")
    
    from services.tier_service import tier_service
    await tier_service.update_tier(int(level_id), data)
    return {"success": True}


async def handle_admin_get_users(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene la lista paginada de usuarios para el panel admin."""
    check_staff(user_data)
    
    limit = data.get("limit", 20)
    offset = data.get("offset", 0)
    search = data.get("search")
    
    users = await user_repo.list_users(limit=limit, offset=offset, search=search)
    logger.info(f"ADMIN: handle_admin_get_users found {len(users)} users (limit={limit}, offset={offset}, search={search})")
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


async def handle_admin_backup_library(data: dict[str, Any], user_data: dict[str, Any]):
    """Syncs SQLite library data (books, duplicates, uploads) to Supabase."""
    check_staff(user_data)
    
    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}

    try:
        session = get_session()
        sources = session.query(LibrarySource).all()
        books = session.query(LocalBook).all()
        duplicates = session.query(DuplicateBook).all()
        uploads = session.query(UploadBook).all()
        
        client = supabase_manager.get_client()
        
        # 1. Sync Sources
        for s in sources:
            source_data = {
                "id": s.id,
                "name": s.name,
                "path": s.path,
                "last_scanned": s.last_scanned.isoformat() if s.last_scanned else None
            }
            client.table("library_sources").upsert(source_data, on_conflict="path").execute()
            
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
                    "author_jap": b.author_jap,
                    "illustrator": b.illustrator,
                    "illustrator_jap": b.illustrator_jap,
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
                    "description": limpiar_html_basico(b.description),
                    "demographics": b.demographics,
                    "tags": b.tags,
                    "language": b.language,
                    "cover_original": b.cover_original,
                    "cover_high": b.cover_high,
                    "cover_medium": b.cover_medium,
                    "cover_low": b.cover_low,
                    "cover_path": b.cover_low or b.cover_medium,
                    "cover_thumb_path": b.cover_low,
                    "file_created_at": b.file_created_at.isoformat() if b.file_created_at else None,
                    "file_modified_at": b.file_modified_at.isoformat() if b.file_modified_at else None,
                    "indexed_at": b.indexed_at.isoformat() if b.indexed_at else None,
                    "series_hash": b.series_hash,
                    "book_hash": b.book_hash
                })
            client.table("local_books").upsert(books_data).execute()

        # 3. Sync Duplicate Books
        if duplicates:
            dups_data = []
            for d in duplicates:
                dups_data.append({
                    "id": d.id,
                    "book_hash": d.book_hash,
                    "original_filepath": d.original_filepath,
                    "duplicate_filepath": d.duplicate_filepath,
                    "title": d.title,
                    "author": d.author,
                    "detected_at": d.detected_at.isoformat() if d.detected_at else None
                })
            client.table("duplicate_books").upsert(dups_data).execute()

        # 4. Sync Uploads (pendientes)
        if uploads:
            uploads_data = []
            for u in uploads:
                uploads_data.append({
                    "id": u.id,
                    "telegram_id": u.telegram_id,
                    "original_filename": u.original_filename,
                    "temp_filepath": u.temp_filepath,
                    "title": u.title,
                    "series": u.series,
                    "volume": float(u.volume) if u.volume is not None else None,
                    "author": u.author,
                    "author_jap": u.author_jap,
                    "illustrator": u.illustrator,
                    "illustrator_jap": u.illustrator_jap,
                    "book_type": u.book_type,
                    "translator": u.translator,
                    "layout_by": u.layout_by,
                    "language": u.language,
                    "is_uncensored": u.is_uncensored,
                    "color_mode": u.color_mode,
                    "book_hash": u.book_hash,
                    "series_hash": u.series_hash,
                    "identity_match": str(u.identity_match),
                    "path_collision": str(u.path_collision),
                    "processed": str(u.processed),
                    "upload_metadata": u.upload_metadata,
                    "created_at": u.created_at.isoformat() if u.created_at else None
                })
            client.table("upload_books").upsert(uploads_data).execute()
            
        session.close()
        return {"success": True, "message": f"Sincronizados {len(sources)} fuentes, {len(books)} libros, {len(duplicates)} duplicados y {len(uploads)} uploads."}
    except Exception as e:
        logger.error(f"Error backup library to Supabase: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_sync_users_cloud(data: dict[str, Any], user_data: dict[str, Any]):
    """Sincroniza usuarios y niveles locales (Postgres) a Supabase."""
    check_staff(user_data)
    
    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}

    try:

        from sqlalchemy import select

        from core.db_manager_pg import pg_manager
        from core.supabase_manager import supabase_manager
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
                    "default_theme_id": lvl.default_theme_id
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
                    # Remove created_at/updated_at as they are managed by DB or might not exist in schema cache
                }
                user_batch.append(u_data)
            
            if user_batch:
                # Chunked upsert to avoid request limits
                for i in range(0, len(user_batch), 50):
                    batch = user_batch[i:i+50]
                    try:
                        client.table("users").upsert(batch).execute()
                    except Exception as upsert_e:
                        logger.error(f"Supabase PUSH error for user batch (indices {i}-{i+len(batch)-1}): {upsert_e}")

            # 3. Pull from Supabase to ensure Local is up to date (Bidirectional)
            logger.info("ADMIN: Triggering immediate PULL from Supabase to Local to sync missing data")
            from core.optimized_sync_engine import optimized_sync_engine
            
            # Force status to pending and reset timestamps to ensure everything is pulled
            await optimized_sync_engine.force_sync_all()
            
            # Execute immediate sync for users and levels
            try:
                # We call the internal methods directly for immediate response
                await optimized_sync_engine._sync_users_optimized()
                await optimized_sync_engine._sync_user_levels_optimized()
                await optimized_sync_engine._sync_admins_optimized()
            except Exception as pull_e:
                logger.error(f"Error during bidirectional PULL: {pull_e}")
                return {"success": True, "message": f"Push completado ({len(users)} users), pero el Pull falló: {pull_e}"}
            
            return {"success": True, "message": f"Sincronización bidireccional completada. Pushed {len(users)} users, Local updated from Cloud."}
    except Exception as e:
        return {"success": False, "message": str(e)}

async def handle_admin_sync_library_cloud(data: dict[str, Any], user_data: dict[str, Any]):
    """Sincroniza metadatos de series, propuestas IA, feedback, fuentes y libros locales con Supabase."""
    check_staff(user_data)
    
    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}

    client = supabase_manager.get_client()
    if not client:
        return {"success": False, "message": "Supabase no está configurado"}

    stats = {"series": 0, "proposals": 0, "feedback": 0, "sources": 0, "books": 0}
    try:
        async with pg_manager.get_session() as session:
            # 1. Sync SeriesMetadata
            res_series = await session.execute(select(SeriesMetadata))
            all_series = res_series.scalars().all()
            for s in all_series:
                s_data = {
                    "series_hash": s.series_hash,
                    "series_name": s.series_name,
                    "series_spanish": s.series_spanish,
                    "author": s.author,
                    "description": s.description,
                    "tags": s.tags,
                    "cover_url": s.cover_url,
                    "book_type": s.book_type,
                    "rating_average": float(s.rating_average) if s.rating_average is not None else 0.0,
                    "rating_count": s.rating_count,
                    "book_count": s.book_count
                }
                client.table("series_metadata").upsert(s_data, on_conflict="series_hash").execute()
                stats["series"] += 1

            # 2. Sync AI Learning Feedback
            res_feedback = await session.execute(select(AILearningFeedback))
            all_feedback = res_feedback.scalars().all()
            feedback_batch = []
            for f in all_feedback:
                f_data = {
                    "series_hash": f.series_hash,
                    "original_name": f.original_name,
                    "proposed_name": f.proposed_name,
                    "final_name": f.final_name,
                    "status": f.status,
                    "ai_reason": f.ai_reason,
                    "user_reason": f.user_reason,
                    "created_at": f.created_at.isoformat() if f.created_at else None
                }
                feedback_batch.append(f_data)
                
            if feedback_batch:
                for i in range(0, len(feedback_batch), 50):
                    batch = feedback_batch[i:i+50]
                    client.table("ai_learning_feedback").upsert(batch).execute()
                    stats["feedback"] += len(batch)

            # 3. Sync AI Proposals (MetadataProposals)
            res_props = await session.execute(select(MetadataProposal))
            all_props = res_props.scalars().all()
            props_batch = []
            for p in all_props:
                p_data = {
                    "series_hash": p.series_hash,
                    "secondary_hash": p.secondary_hash,
                    "type": p.type,
                    "proposal_data": p.proposal_data,
                    "status": p.status,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "processed_at": p.processed_at.isoformat() if p.processed_at else None
                }
                props_batch.append(p_data)

            if props_batch:
                for i in range(0, len(props_batch), 50):
                    batch = props_batch[i:i+50]
                    client.table("metadata_proposals").upsert(batch).execute()
                    stats["proposals"] += len(batch)

            # 4. Sync Library Sources
            res_sources = await session.execute(select(LibrarySource))
            sources = res_sources.scalars().all()
            for s in sources:
                s_data = {
                    "name": s.name,
                    "path": s.path,
                    "last_scanned": s.last_scanned.isoformat() if s.last_scanned else None
                }
                client.table("library_sources").upsert(s_data, on_conflict="path").execute()
                stats["sources"] += 1

            # 5. Sync Local Books
            res_books = await session.execute(select(LocalBook))
            books = res_books.scalars().all()
            if books:
                for i in range(0, len(books), 100):
                    batch = books[i:i+100]
                    books_data = []
                    for b in batch:
                        b_dict = b.to_dict()
                        # Ensure numeric types are JSON serializable and IDs are removed to avoid conflict
                        clean_data = {
                            "book_hash": b_dict.get("book_hash"),
                            "series_hash": b_dict.get("series_hash"),
                            "filepath": b_dict.get("filepath"),
                            "filename": b_dict.get("filename"),
                            "title": b_dict.get("title"),
                            "volume": float(b_dict.get("volume")) if b_dict.get("volume") is not None else None,
                            "author": b_dict.get("author"),
                            "translator": b_dict.get("translator"),
                            "layout_by": b_dict.get("layout_by"),
                            "book_type": b_dict.get("book_type"),
                            "language": b_dict.get("language"),
                            "description": b_dict.get("description"),
                            "tags": b_dict.get("tags"),
                            "cover_low": b_dict.get("cover_low"),
                            "rating_average": float(b_dict.get("rating_average")) if b_dict.get("rating_average") is not None else 0.0,
                            "rating_count": b_dict.get("rating_count"),
                            "indexed_at": b_dict.get("indexed_at")
                        }
                        books_data.append(clean_data)
                    client.table("local_books").upsert(books_data, on_conflict="book_hash").execute()
                    stats["books"] += len(batch)

        return {
            "success": True, 
            "message": f"Sincronización completada: {stats['series']} series, {stats['books']} libros, {stats['proposals']} propuestas.",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error syncing library to Supabase: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_scan_library(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates forced library scan."""
    check_staff(user_data)
    
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


async def handle_admin_scan_series(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates forced scan for a specific series."""
    check_staff(user_data)
    
    series_hash = data.get("series_hash")
    force = data.get("force", True) # Default to True for series sync
    
    if not series_hash:
        return {"success": False, "message": "series_hash es requerido."}
    
    async def run_sync_in_background(scanner_obj, s_hash, force_val):
        try:
            logger.info(f"Background series scan started (Hash: {s_hash}, Force: {force_val})")
            await asyncio.to_thread(scanner_obj.sync_series, s_hash, force_scan=force_val)
            logger.info(f"Background series scan for {s_hash} completed successfully.")
        except Exception as e:
            logger.error(f"Background series scan error for {s_hash}: {e}")

    try:
        from services.scanner_service import ScannerService
        
        if ScannerService._is_scanning:
            return {"success": False, "message": "⚠️ Ya hay un escaneo de librería en progreso."}

        libs_json = os.getenv("LOCAL_LIBRARIES")
        if not libs_json:
            return {"success": False, "message": "LOCAL_LIBRARIES no configurada."}
            
        scanner = ScannerService(libs_json)
        
        # Start the intensive task in background
        asyncio.create_task(run_sync_in_background(scanner, series_hash, force))
        
        return {
            "success": True, 
            "message": "Sincronización de serie iniciada en segundo plano."
        }
    except Exception as e:
        logger.error(f"Error starting background series scan: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_enrich_metadata(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates manual enrichment of metadata from online sources."""
    check_staff(user_data)
    
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


async def handle_admin_reset_library(data: dict[str, Any], user_data: dict[str, Any]):
    """Reset complete library database (admin only, requires confirmation)."""
    check_staff(user_data)
    
    # Require explicit confirmation
    confirmed = data.get("confirmed", False)
    if not confirmed:
        return {
            "success": False, 
            "message": "Confirmación requerida para eliminar la base de datos.",
            "requireConfirmation": True
        }
    
    try:
        import sqlalchemy as sa

        from utils.library_db import COVERS_DIR, engine
        
        items_deleted = []
        cover_count = 0
        
        try:
            with engine.begin() as conn:
                # Order of deletion matters due to FKs
                conn.execute(sa.text("DELETE FROM user_ratings"))
                conn.execute(sa.text("DELETE FROM user_downloads"))
                conn.execute(sa.text("DELETE FROM metadata_proposals"))
                conn.execute(sa.text("DELETE FROM ai_learning_feedback"))
                conn.execute(sa.text("DELETE FROM local_books"))
                conn.execute(sa.text("DELETE FROM series_metadata"))
                conn.execute(sa.text("DELETE FROM library_sources"))
                conn.execute(sa.text("DELETE FROM duplicate_books"))
                conn.execute(sa.text("DELETE FROM upload_books"))
            items_deleted.append("Tablas de PostgreSQL limpiadas (series_metadata, local_books, sources, ratings, downloads, proposals, feedback)")
        except Exception as e:
            logger.error(f"Error clearing Postgres tables: {e}")
            return {"success": False, "message": f"Error limpiando tablas Postgres: {e}"}

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


async def handle_admin_restart_docker(data: dict[str, Any], user_data: dict[str, Any]):
    """Restart Docker container (admin only)."""
    check_staff(user_data)
    
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


async def handle_admin_update_system(data: dict[str, Any], user_data: dict[str, Any]):
    """Trigger system update (git pull + restart) using existing bot infrastructure."""
    check_staff(user_data)
    
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


async def handle_admin_save_tier_config(data: dict[str, Any], user_data: dict[str, Any]):
    """Guarda la configuración completa de un nivel/tier."""
    check_staff(user_data)
    
    tier_name = data.get("name")
    level_id = data.get("level_id") or data.get("id")
    
    try:
        is_global = (level_id == "global" or tier_name == "Global" or (tier_name and "Global" in str(tier_name)))
        if is_global:
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
            logger.info("ADMIN: Saved GLOBAL tier config locally and to Supabase (if active)")
            return {"success": True, "tierId": "global"}

        # Determine tier_id
        client = supabase_manager.get_client()
        tier_id = None
        if level_id and str(level_id).isdigit():
            tier_id = int(level_id)
        else:
            # Find tier by name
            result = client.table("user_levels").select("id").ilike("name", tier_name).execute()
            if not result.data:
                raise HTTPException(status_code=404, detail=f"Tier '{tier_name}' no encontrado")
            tier_id = result.data[0]["id"]
        
        # Build update data
        update_data = {}
        
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
            "canUploadEpub": "can_upload_epub",
            "hasLibraryAccess": "has_library_access",
            "canRequestBooks": "can_request_books",
            "bannerContentOffset": "banner_content_offset",
            "backgroundColor": "background_color",
            "cardColor": "card_color",
            "forceSettings": "force_settings",
            "cardGlowIntensity": "ui_glow_intensity",
            "ui_exported_settings": "ui_exported_settings",
            "allowThemeTemplates": "allow_theme_templates",
            "defaultThemeId": "default_theme_id"
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
            client.table("user_levels").update(update_data).eq("id", tier_id).execute()
        except Exception as e:
            msg = str(e)
            if "Could not find the" in msg and "column" in msg:
                logger.warning(f"Supabase schema missing columns. Retrying with basic fields only. Error: {msg}")
                # Retry with only core fields that surely exist
                core_fields = ["name", "icon", "color", "daily_downloads", "priority_requests"]
                safe_data = {k: v for k, v in update_data.items() if k in core_fields}
                if safe_data:
                    client.table("user_levels").update(safe_data).eq("id", tier_id).execute()
                    return {"success": True, "tierId": tier_id, "warning": "Partial save: Schema update required"}
            raise e
        
        # Update tier locally (SQLite)
        try:
            from repositories.user_repository import user_repo
            await user_repo.update_level(tier_id, data)
        except Exception as e:
            logger.error(f"Error updating tier locally: {e}")
            # Non-fatal, we continue since Supabase was updated
        
        # Trigger bidirectional sync to ensure everything is in sync after manual update
        from core.optimized_sync_engine import optimized_sync_engine
        await optimized_sync_engine.force_sync_all()

        logger.info(f"ADMIN: Saved tier config for '{tier_name}' (ID: {tier_id}) in Cloud and Local (Bidirectional Sync triggered)")
        return {"success": True, "tierId": tier_id, "message": "Configuración guardada y sincronizada bidireccionalmente."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving tier config: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_tier_config(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene la configuración completa de un nivel/tier."""
    check_staff(user_data)
    
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
                "canUploadEpub": g.get("canUploadEpub", False),
                "forceSettings": g.get("forceSettings", False),
                "cardGlowIntensity": g.get("cardGlowIntensity", 0.5),
                "backgroundColor": g.get("backgroundColor", "#0f172a"),
                "cardColor": g.get("cardColor", "#1e293b"),
                "bannerContentOffset": g.get("bannerContentOffset", 0),
                "allowThemeTemplates": g.get("allowThemeTemplates", False)
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
        elif tier_name and str(tier_name).isdigit():
            # If name is numeric, treat as ID
            tier = await user_repo.get_level_by_id(int(tier_name))
        elif tier_name:
            # Fallback to fetching all and finding by name if no ID
            all_lvls = await user_repo.get_all_levels()
            tier = next((l for l in all_lvls if l["name"].lower() == tier_name.lower()), None)
        
        if not tier:
            raise HTTPException(status_code=404, detail=f"Tier '{tier_name or tier_id}' no encontrado")
        
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



async def handle_admin_get_themes(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna la lista de plantillas de temas disponibles."""
    # Relaxed permission: Allow all authorized mini-app users to view themes (controlled by UI)
    # if user_data.get("level") != "admin":
    #    raise HTTPException(status_code=403, detail="No tienes permisos")
    
    from services.theme_service import theme_service
    try:
        themes = await theme_service.get_all_themes()
        logger.info(f"Returning {len(themes)} themes to frontend")
        return {"success": True, "themes": themes}
    except Exception as e:
        logger.error(f"Error fetching themes: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_sync_themes(data: dict[str, Any], user_data: dict[str, Any]):
    """Ejecuta sincronización manual de temas."""
    if user_data.get("level") not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    from services.theme_sync_service import theme_sync_service
    
    try:
        result = await theme_sync_service.manual_sync()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error in manual theme sync: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_get_sync_status(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene estado del motor de sincronización optimizado."""
    if user_data.get("level") not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    from core.optimized_sync_engine import optimized_sync_engine
    from services.cache_service import cache_manager
    
    try:
        sync_status = await optimized_sync_engine.get_sync_status()
        cache_stats = await cache_manager.get_stats()
        
        return {
            "success": True, 
            "sync_status": sync_status,
            "cache_stats": cache_stats
        }
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_force_sync(data: dict[str, Any], user_data: dict[str, Any]):
    """Fuerza sincronización completa de todas las tablas."""
    if user_data.get("level") not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    from core.optimized_sync_engine import optimized_sync_engine
    
    try:
        await optimized_sync_engine.force_sync_all()
        return {"success": True, "message": "Sincronización forzada iniciada"}
    except Exception as e:
        logger.error(f"Error forcing sync: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_rename_themes(data: dict[str, Any], user_data: dict[str, Any]):
    """Renombra temas duplicados con nombres únicos usando detección mejorada."""
    if user_data.get("level") not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    from sqlalchemy import text
    
    try:
        from core.db_manager_pg import pg_manager
        
        async with pg_manager.get_session() as session:
            # 1. Obtener TODOS los temas existentes
            result = await session.execute(text("SELECT id, name FROM app_themes ORDER BY name"))
            all_themes = result.fetchall()
            
            logger.info(f"Found {len(all_themes)} total themes")
            
            # 2. Encontrar temas que terminan con " 2" o contienen "2"
            themes_to_rename = []
            for theme in all_themes:
                name = theme[1]
                if name and ("2" in name):
                    # Priorizar temas que terminan exactamente con " 2"
                    if name.strip().endswith("2"):
                        themes_to_rename.append(theme)
                        logger.info(f"Found theme ending with '2': ID {theme[0]}, Name: '{name}'")
                    else:
                        logger.info(f"Theme containing '2' (not ending): ID {theme[0]}, Name: '{name}'")
            
            if not themes_to_rename:
                logger.info("No themes found ending with '2'")
                return {
                    "success": True, 
                    "message": "No se encontraron temas que terminen en '2' para renombrar",
                    "renamed_count": 0
                }
            
            logger.info(f"Found {len(themes_to_rename)} themes to rename")
            
            # 3. Renombrar con nombres únicos generados automáticamente
            renamed_count = 0
            import time
            
            for theme_id, old_name in themes_to_rename:
                # Extraer el nombre base
                base_name = old_name.replace(" 2", "").replace("2", "").strip()
                
                # Generar nombres únicos
                name_variants = [
                    f"{base_name} Pro",
                    f"{base_name} Plus", 
                    f"{base_name} Advanced",
                    f"{base_name} Premium",
                    f"{base_name} Elite",
                    f"{base_name} Max",
                    f"{base_name} Ultra",
                    f"{base_name} Special",
                    f"{base_name} Enhanced",
                    f"{base_name} Professional",
                    f"{base_name} Modern",
                    f"{base_name} Classic",
                    f"{base_name} Dark",
                    f"{base_name} Light",
                    f"Dark {base_name}",
                    f"Light {base_name}",
                    f"Deep {base_name}",
                    f"Soft {base_name}",
                    f"Neo {base_name}"
                ]
                
                # Buscar nombre único
                new_name = None
                for candidate in name_variants:
                    result = await session.execute(text("SELECT id FROM app_themes WHERE name = :candidate"), {"candidate": candidate})
                    existing = result.fetchone()
                    
                    if not existing:
                        new_name = candidate
                        break
                
                if not new_name:
                    # Último recurso: timestamp
                    new_name = f"{base_name} ({int(time.time())})"
                
                # Realizar renombrado
                await session.execute(
                    text("UPDATE app_themes SET name = :new_name, updated_at = CURRENT_TIMESTAMP WHERE id = :theme_id"),
                    {"new_name": new_name, "theme_id": theme_id}
                )
                
                logger.info(f"Renamed theme ID {theme_id}: '{old_name}' → '{new_name}'")
                renamed_count += 1
            
            await session.commit()
            
            # Invalidate cache after bulk rename
            from services.theme_service import theme_service
            await theme_service.invalidate_caches()
            
            logger.info(f"Enhanced theme renaming completed. {renamed_count} themes renamed.")
            
            return {
                "success": True, 
                "message": f"Se renombraron {renamed_count} temas exitosamente",
                "renamed_count": renamed_count
            }
            
    except Exception as e:
        logger.error(f"Error in enhanced theme renaming: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_get_theme_sync_logs(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene historial de sincronizaciones de temas."""
    if user_data.get("level") not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    from services.theme_sync_service import theme_sync_service
    
    try:
        logs = await theme_sync_service.get_sync_logs(limit=50)
        return {"success": True, "logs": logs}
    except Exception as e:
        logger.error(f"Error getting theme sync logs: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_save_theme(data: dict[str, Any], user_data: dict[str, Any]):
    if user_data.get("level") not in ["admin", "staff"]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    
    theme_name = data.get("name")
    if not theme_name:
        return {"success": False, "message": "El tema necesita un nombre"}
    
    import re
    # Clean name: remove trailing numbers that look like " 2", " 3"
    theme_name = re.sub(r"\s+\d+$", "", theme_name).strip()
    
    from services.theme_service import theme_service
    
    # Ensure name uniqueness if it's a new theme request
    if data.get("is_new"):
        existing_themes = await theme_service.get_all_themes()
        existing_names = [t["name"] for t in existing_themes]
        
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
        res = await theme_service.save_theme(insert_data)
        if not res:
             return {"success": False, "message": "No se pudo guardar el tema"}
        return {"success": True, "theme": res}
    except Exception as e:
        logger.error(f"Error saving theme: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_save_user_permissions(data: dict[str, Any], user_data: dict[str, Any]):
    """Guarda los permisos de un usuario específico."""
    logger.info(f"ADMIN: Save permissions request for data: {data}")
    check_staff(user_data)
    
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Falta userId")
    
    try:
        import asyncio

        from repositories.user_repository import user_repo
        from services.user_audit_service import UserAuditService
        from services.user_service import invalidate_user_cache
        
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
            "hasLibraryAccess": "has_library_access",
            "canUploadEpub": "can_upload_epub",
            "settings": "settings",
            "allowThemeTemplates": "allow_theme_templates"
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
            can_upload_epub=data.get("canUploadEpub"),
            level_id=level_id,
            settings=data.get("settings"),
            allow_theme_templates=data.get("allowThemeTemplates")
        )
        
        # betaTester is handled separately if needed, or we could add it to upsert too
        if config.ENABLE_SUPABASE and "betaTester" in data:
            supabase_manager.get_client().table("users").update({"beta_tester": data["betaTester"]}).eq("telegram_id", int(user_id)).execute()

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


async def handle_admin_get_user_permissions(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene los permisos de un usuario específico."""
    check_staff(user_data)
    
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
                "canUploadEpub": raw_user.get("can_upload_epub", access_info["level"].get("canUploadEpub", False)),
                "allowThemeTemplates": raw_user.get("allow_theme_templates", access_info["level"].get("allowThemeTemplates", False)),
                "insignias": raw_user.get("insignias") or [],
                "settings": raw_user.get("settings") or {},
                "photo_url": access_info.get("photo_url") or raw_user.get("photo_url")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_find_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    """
    Find all duplicate books grouped by content_hash.
    Returns duplicate groups with file info and statistics.
    """
    check_staff(user_data)
    
    try:
        from sqlalchemy import func

        from models.library_models import LocalBook
        from utils.library_db import get_session
        
        session = get_session()
        
        # Query to find duplicates
        duplicate_hashes = session.query(
            LocalBook.book_hash,
            func.count().label("count")
        ).filter(
            LocalBook.book_hash.isnot(None)
        ).group_by(
            LocalBook.book_hash
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
                LocalBook.book_hash == content_hash
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
                "book_hash": content_hash,
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
        
        duplicate_groups.sort(key=lambda x: x["wasted_space"], reverse=True)
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


async def handle_admin_delete_duplicate(data: dict[str, Any], user_data: dict[str, Any]):
    """Delete duplicate books safely, ensuring at least one copy remains."""
    check_staff(user_data)
    
    book_ids = data.get("book_ids", [])
    if not book_ids:
        return {"success": False, "message": "No se especificaron libros"}
    
    try:
        import os
        from collections import defaultdict

        from sqlalchemy import func

        from models.library_models import LocalBook
        from utils.library_db import COVERS_DIR, get_session
        
        session = get_session()
        
        books_to_delete = session.query(LocalBook).filter(
            LocalBook.id.in_(book_ids)
        ).all()
        
        if not books_to_delete:
            return {"success": False, "message": "No se encontraron libros"}
        
        # Group by book_hash
        by_hash = defaultdict(list)
        for book in books_to_delete:
            by_hash[book.book_hash].append(book)
        
        deleted_count = 0
        deleted_size = 0
        errors = []
        
        for content_hash, books in by_hash.items():
            # Count total books with this hash
            total_with_hash = session.query(func.count(LocalBook.id)).filter(
                LocalBook.book_hash == content_hash
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
                        cover_file = book.cover_path.replace("/api/library/covers/", "")
                        cover_path = os.path.join(COVERS_DIR, cover_file)
                        if os.path.exists(cover_path):
                            os.remove(cover_path)
                        thumb_path = cover_path.replace(".jpg", "_thumb.jpg")
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


async def handle_update_user_setting(data: dict[str, Any], user_data: dict[str, Any]):
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


async def handle_get_user_audit_history(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene el historial de cambios de un usuario."""
    check_staff(user_data)
    
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
        
        
async def handle_admin_get_recent_audit_logs(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene los cambios recientes en el sistema."""
    check_staff(user_data)
    
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


async def handle_admin_get_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna la lista de archivos duplicados detectados."""
    if user_data.get("level") not in ["admin", "staff"]:
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

async def handle_admin_clear_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    """Limpia la tabla de registros de duplicados."""
    if user_data.get("level") not in ["admin", "staff"]:
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

async def handle_admin_get_system_logs(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna los últimos logs capturados en memoria con opción de filtrado."""
    check_staff(user_data)
    
    try:
        from utils.log_manager import log_buffer_handler
        
        level = data.get("level", "INFO")
        hours = data.get("hours") # None for all in buffer
        
        logs = log_buffer_handler.get_logs(level=level, last_hours=hours)
        return {"success": True, "logs": logs}
    except Exception as e:
        logger.error(f"Error fetching system logs: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_send_logs_telegram(data: dict[str, Any], user_data: dict[str, Any]):
    """Envía los logs capturados directamente al chat de Telegram del usuario."""
    check_staff(user_data)
    
    try:
        import io
        from datetime import datetime

        from api.main import bot as bot_instance
        from utils.log_manager import log_buffer_handler

        level = data.get("level", "DEBUG") 
        hours = data.get("hours")
        
        logs = log_buffer_handler.get_logs(level=level, last_hours=hours)
        if not logs:
            return {"success": False, "message": "No hay logs disponibles para enviar."}
            
        # Format logs
        log_text = "\n".join([f"[{l['time']}] {l['level']}: {l['msg']}" for l in logs])
        
        # Create file
        file_obj = io.BytesIO(log_text.encode("utf-8"))
        
        # Filename with range
        first_t = logs[0]["timestamp"]
        last_t = logs[-1]["timestamp"]
        def fmt(t):
            return datetime.fromtimestamp(t).strftime("%Y%m%d_%H%M")
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

async def handle_admin_bulk_upload_confirm(data: dict[str, Any], user_data: dict[str, Any]):
    """Confirma y finaliza múltiples subidas de EPUB."""
    selected_ids = data.get("selected_ids", [])
    discarded_ids = data.get("discarded_ids", [])
    
    # Si no vienen selected_ids, probamos con upload_ids (compatibilidad)
    if not selected_ids:
        selected_ids = data.get("upload_ids", [])
        
    if not selected_ids and not discarded_ids:
        raise HTTPException(status_code=400, detail="No selected or discarded IDs provided")
    
    from pathlib import Path

    from handlers.epub_upload_handler import epub_uploader, pending_uploads
    
    # 1. Manejar descartados (limpieza)
    for disc_id in discarded_ids:
        if disc_id in pending_uploads:
            info = pending_uploads[disc_id]
            epub_uploader.cleanup_upload(disc_id, Path(info["file_path"]))
            
    # 2. Manejar seleccionados (procesamiento)
    results = []
    for upload_id in selected_ids:
        if upload_id not in pending_uploads:
            results.append({"upload_id": upload_id, "success": False, "error": "No encontrado"})
            continue
            
        upload_info = pending_uploads[upload_id]
        file_path = Path(upload_info["file_path"])
        metadata = upload_info["metadata"]
        suggested_path = metadata.get("suggested_path")
        
        try:
            success = await epub_uploader.add_to_library(file_path, suggested_path, metadata)
            if success:
                epub_uploader._log_history(
                    user_id=upload_info["user_id"],
                    filename=upload_info["original_filename"],
                    book_hash=metadata.get("book_hash"),
                    status="success",
                    final_path=suggested_path
                )
                epub_uploader.cleanup_upload(upload_id, file_path)
                results.append({"upload_id": upload_id, "success": True})
            else:
                epub_uploader._log_history(
                    user_id=upload_info["user_id"],
                    filename=upload_info["original_filename"],
                    book_hash=metadata.get("book_hash"),
                    status="error",
                    error_message="Failed to move file to library"
                )
                results.append({"upload_id": upload_id, "success": False, "error": "Error al mover a librería"})
        except Exception as e:
            results.append({"upload_id": upload_id, "success": False, "error": str(e)})
            
    return {"success": True, "results": results}


async def handle_get_upload_history(limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    """Obtiene el historial de subidas paginado."""
    from sqlalchemy import desc

    from models.library_models import UploadHistory
    from utils.library_db import get_session

    try:
        with get_session() as session:
            query = session.query(UploadHistory).order_by(desc(UploadHistory.created_at))
            query = query.limit(limit).offset(offset)
            results = query.all()

            history_list = []
            for item in results:
                history_list.append({
                    "id": item.id,
                    "user_id": item.user_id,
                    "filename": item.filename,
                    "book_hash": item.book_hash,
                    "status": item.status,
                    "final_path": item.final_path,
                    "error_message": item.error_message,
                    "created_at": item.created_at.isoformat() if item.created_at else None
                })
            return history_list
    except Exception as e:
        logger.error(f"Error fetching upload history: {e}")
        return []


async def handle_ai_stats(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve estadísticas sobre el uso de la IA."""
    from sqlalchemy import func
    from models.library_models import LocalBook, AILearningFeedback
    from utils.library_db import get_session

    try:
        with get_session() as session:
            # 1. Total de libros
            total_books = session.query(func.count(LocalBook.id)).scalar()

            # 2. Libros en series YA revisadas (que están en ai_learning_feedback)
            # Usamos una subquery para mayor eficiencia
            reviewed_hashes = session.query(AILearningFeedback.series_hash).distinct()
            total_processed = session.query(func.count(LocalBook.id)).filter(
                LocalBook.series_hash.in_(reviewed_hashes)
            ).scalar() or 0
            
            # 3. Libros pendientes de estandarización
            pending = total_books - total_processed if total_books > total_processed else 0
            
            # 4. Eficiencia (Estimado)
            # Asumimos que cada renombrado manual toma 30 segundos
            time_saved_minutes = total_processed * 0.5

            res = {
                "total_processed": total_processed,
                "total_books": total_books,
                "pending_optimization": pending,
                "time_saved_hours": round(time_saved_minutes / 60, 1),
                "ai_active": bool(config.GEMINI_API_KEY),
                "background_scan_enabled": get_setting("enable_background_ai_scan", "false").lower() == "true",
                "ai_key_masked": f"{config.GEMINI_API_KEY[:4]}...{config.GEMINI_API_KEY[-4:]}" if config.GEMINI_API_KEY else "NONE"
            }
            logger.info(f"📊 AI Stats requested. Active: {res['ai_active']}, Key Masked: {res['ai_key_masked']}")
            return {"result": res}
    except Exception as e:
        logger.error(f"Error getting AI stats: {e}")
        return {"error": str(e)}

async def handle_ai_toggle_background_scan(data: dict[str, Any], user_data: dict[str, Any]):
    """Activa o desactiva el escaneo con IA en segundo plano."""
    enabled = data.get("enabled", False)
    set_setting("enable_background_ai_scan", "true" if enabled else "false")
    return {"success": True, "enabled": enabled}


async def handle_ai_get_lists(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve listados de series pendientes y revisadas por la IA."""
    from sqlalchemy import func, text

    from core.db_manager_pg import pg_manager
    from models.library_models import LocalBook, SeriesMetadata
    
    list_type = data.get("type", "pending") # 'pending' or 'reviewed'
    limit = data.get("limit", 100)
    offset = data.get("offset", 0)

    try:
        async with pg_manager.get_session() as session:
            if list_type == "reviewed":
                # Series que están en ai_learning_feedback
                query = text("""
                    SELECT f.series_hash, f.original_name, f.proposed_name, f.final_name, f.status, f.created_at,
                           (SELECT COUNT(*) FROM local_books WHERE series_hash = f.series_hash) as books_count
                    FROM ai_learning_feedback f
                    INNER JOIN (
                        SELECT series_hash, MAX(created_at) as max_date
                        FROM ai_learning_feedback
                        GROUP BY series_hash
                    ) latest ON f.series_hash = latest.series_hash AND f.created_at = latest.max_date
                    ORDER BY f.created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                res = await session.execute(query, {"limit": limit, "offset": offset})
                items = []
                for row in res:
                    items.append({
                        "series_hash": row.series_hash,
                        "original_name": row.original_name,
                        "proposed_name": row.proposed_name,
                        "final_name": row.final_name,
                        "status": row.status,
                        "reviewed_at": row.created_at.isoformat() if row.created_at else None,
                        "books_count": row.books_count
                    })
                return {"success": True, "items": items}
            
            else:
                # Pendientes: Series en local_books que NO están en ai_learning_feedback
                # Y que no tengan series_spanish (opcional, pero mejor ser estrictos con la tabla de feedback)
                query = text("""
                    SELECT series_hash, series as name, COUNT(*) as books_count
                    FROM local_books
                    WHERE series_hash NOT IN (SELECT series_hash FROM ai_learning_feedback)
                    GROUP BY series_hash, series
                    ORDER BY books_count DESC
                    LIMIT :limit OFFSET :offset
                """)
                res = await session.execute(query, {"limit": limit, "offset": offset})
                items = []
                for row in res:
                    items.append({
                        "series_hash": row.series_hash,
                        "name": row.name,
                        "books_count": row.books_count
                    })
                return {"success": True, "items": items}

    except Exception as e:
        logger.error(f"Error getting AI lists: {e}")
        return {"success": False, "message": str(e)}


async def handle_ai_scan_series(data: dict[str, Any], user_data: dict[str, Any]):
    """Dispara un escaneo on-demand de una serie específica."""
    series_hash = data.get("series_hash")
    series_name = data.get("series_name") # Optional fallback
    dry_run = data.get("dry_run", False)
    
    if not config.GEMINI_API_KEY:
        return {"success": False, "message": "IA no configurada (Falta API Key)"}
        
    try:
        from models.library_models import LocalBook
        from services.ai_service import AIService
        from utils.library_db import get_session

        with get_session() as session:
             # Buscar libros de esa serie
             query = session.query(LocalBook).filter(LocalBook.series_hash == series_hash)
             books = query.order_by(LocalBook.volume.asc()).all()
             
             if not books:
                  return {"success": False, "message": "Serie no encontrada"}

             count = len(books)
             rep_book = books[0] # Usar cualquiera como representante base
             current_name = rep_book.series or series_name or rep_book.title

             # --- DRY RUN MODE (PROPOSAL) ---
             if dry_run:
                 books_dicts = [b.to_dict() for b in books]
                 proposal = await AIService.analyze_series_for_updates(series_hash, current_name, books_dicts)
                 
                 if "error" in proposal:
                      return {"success": False, "message": f"Error de IA: {proposal['error']}"}

                 return {
                     "success": True,
                     "proposal": proposal,
                     "dry_run": True
                 }

             # --- EXECUTE MODE (STAGING) ---
             # Ya NO aplicamos cambios directamente. Guardamos como propuesta.
             books_dicts = [b.to_dict() for b in books]
             proposal = await AIService.analyze_series_for_updates(series_hash, current_name, books_dicts)
             
             if not proposal or "error" in proposal:
                  return {"success": False, "message": f"Error de IA: {proposal.get('error', 'Fallo desconocido')}"}
             
             from models.library_models import MetadataProposal
             
             # Verificar si ya existe una pendiente
             existing = session.query(MetadataProposal).filter_by(series_hash=series_hash, status="pending").first()
             if existing:
                 existing.proposal_data = proposal
                 existing.created_at = datetime.utcnow()
             else:
                 new_prop = MetadataProposal(
                     series_hash=series_hash,
                     proposal_data=proposal,
                     status="pending"
                 )
                 session.add(new_prop)
             
             session.commit()
             
             return {
                 "success": True, 
                 "message": f"Propuesta para '{current_name}' generada. Revisa la bandeja de entrada para aprobarla."
             }
             
    except Exception as e:
        logger.error(f"Error in AI scan series: {e}")
        return {"success": False, "message": str(e)}


async def handle_ai_apply_changes(data: dict[str, Any], user_data: dict[str, Any]):
    """Aplica los cambios confirmados por el usuario desde la propuesta de IA."""
    if not config.GEMINI_API_KEY:
        return {"success": False, "message": "IA no configurada"}

    proposal = data.get("proposal")
    proposal_id = data.get("proposal_id")
    
    if not proposal and not proposal_id:
        raise HTTPException(status_code=400, detail="Faltan datos de la propuesta")
 
    from models.library_models import LocalBook, SeriesMetadata, MetadataProposal
    from utils.library_db import get_session
 
    with get_session() as session:
        # Si nos pasan un proposal_id, cargamos los datos y lo marcamos como aprobado al final
        db_proposal = None
        if proposal_id:
            db_proposal = session.query(MetadataProposal).get(proposal_id)
            if not db_proposal:
                raise HTTPException(status_code=404, detail="Propuesta no encontrada")
            proposal = db_proposal.proposal_data
        else:
            # Intentar encontrar una propuesta pendiente automática para esta misma serie
            # (Por si el usuario triggeró el escaneo manualmente pero ya había una pendiente)
            series_hash_raw = proposal.get("series_hash")
            if series_hash_raw:
                db_proposal = session.query(MetadataProposal).filter_by(
                    series_hash=series_hash_raw, status="pending"
                ).first()

        series_hash = proposal.get("series_hash")
        # Changes is a list of approved changes: { "book_id": 123, "proposed_filename": "..." }
        approved_changes = data.get("approved_changes", []) 
        # Global series metadata overrides
        proposed_series = data.get("proposed_series")
        proposed_spanish = data.get("proposed_spanish")
        
        # Optional flags
        apply_renames = data.get("apply_renames", True)
        apply_meta = data.get("apply_meta", True)

        updated_count = 0
        errors = []

        import os
        import shutil
        from sqlalchemy import select

        # 1. Update Series Metadata (Global)
        if apply_meta and proposed_series:
            # Sync with SeriesMetadata table
            series = session.query(SeriesMetadata).filter_by(series_hash=series_hash).first()
            # If not in data, fallback to proposal
            if not proposed_spanish:
                proposed_spanish = proposal.get("proposed_spanish")
            
            if series:
                series.series_name = proposed_series
                series.series_spanish = proposed_spanish or proposed_series
                if proposal.get("description"):
                    series.description = proposal["description"]
                
                # Sincronizamos tags proactivamente si la IA propone nuevos géneros BASE
                if proposal.get("genres"):
                    current_tags = set(series.tags) if series.tags else set()
                    new_base_tags = set(proposal["genres"])
                    series.tags = list(current_tags | new_base_tags)
            else:
                # Create if missing
                series = SeriesMetadata(
                    series_hash=series_hash,
                    series_name=proposed_series,
                    series_spanish=proposed_spanish or proposed_series,
                    tags=proposal.get("genres"),
                    description=proposal.get("description")
                )
                session.add(series)
                session.flush()

            # 1.1 Update Translator Group Metadata
            group_full = proposal.get("group_full")
            group_siglas = proposal.get("group_siglas")
            if group_full and group_siglas and group_full != "Unknown":
                from models.library_models import TranslatorsGroup
                # Try to find by name (case insensitive)
                existing_group = session.query(TranslatorsGroup).filter(func.lower(TranslatorsGroup.name) == func.lower(group_full)).first()
                if existing_group:
                    existing_group.siglas = group_siglas
                else:
                    new_group = TranslatorsGroup(name=group_full, siglas=group_siglas)
                    session.add(new_group)

            # Cloud Sync immediately if enabled
            if config.ENABLE_SUPABASE:
                try:
                    from core.supabase_manager import supabase_manager
                    client = supabase_manager.get_client()
                    s_data = {
                        "series_hash": series.series_hash,
                        "series_name": series.series_name,
                        "series_spanish": series.series_spanish,
                        "description": series.description,
                        "tags": series.tags,
                        "author": series.author,
                        "book_count": series.book_count,
                        "rating_average": series.rating_average
                    }
                    client.table("series_metadata").upsert(s_data, on_conflict="series_hash").execute()
                except Exception as cloud_e:
                    logger.warning(f"Failed to sync series to cloud: {cloud_e}")

            # Update all books in this hash group to the new series name and link them
            stmt = select(LocalBook).where(LocalBook.series_hash == series_hash)
            books = session.execute(stmt).scalars().all()
            
            for book in books:
                book.series_metadata_id = series.id
                book.series = proposed_series  # English
                book.series_spanish = proposed_spanish or proposed_series # Spanish (Always set for consistency)
                
                book.is_uncensored = proposal.get("is_uncensored_series", False)
                
                # Aprovechar y actualizar volumen si está en la propuesta
                orig_filename = book.filename or book.title
                if proposal.get("volumes") and orig_filename in proposal["volumes"]:
                    book.volume = proposal["volumes"][orig_filename]
            
            updated_count += len(books)

        # 2. Apply File Renames
        if apply_renames and approved_changes:
             for change in approved_changes:
                 book_id_raw = change.get("book_id")
                 proposed_filename = change.get("proposed_filename")
                 
                 if not book_id_raw or not proposed_filename:
                     continue

                 try:
                    book_id = int(str(book_id_raw).replace("local_", ""))
                 except ValueError:
                    errors.append(f"ID de libro inválido: {book_id_raw}")
                    continue

                 book = session.query(LocalBook).filter(LocalBook.id == book_id).scalar()
                 if not book or not book.filepath or not os.path.exists(book.filepath):
                     errors.append(f"Libro {book_id} no encontrado en disco")
                     continue

                 old_path = book.filepath
                 dir_name = os.path.dirname(old_path)
                 new_path = os.path.join(dir_name, proposed_filename)
                 
                 if old_path != new_path:
                     try:
                        shutil.move(old_path, new_path)
                        book.filepath = new_path
                        book.filename = proposed_filename
                        # Update database record
                        updated_count += 1
                     except Exception as e:
                        errors.append(f"Error renombrando {book.filename}: {e}")

        session.commit()
        
        # 3. Consolidar metadata de serie tras los cambios
        from services.scanner_service import ScannerService
        ScannerService.sync_series_metadata(session, series_hash)
        session.commit()

        # 4. Log feedback for learning
        from services.ai_service import AIService
        status = "accepted"
        if proposed_series != proposal.get("proposed_series"):
            status = "edited"
            
        await AIService.log_feedback(
            series_hash=series_hash,
            original=proposal.get("current_series"),
            proposed=proposal.get("proposed_series"),
            final=proposed_series,
            status=status,
            ai_reason=proposal.get("reason")
        )

        # Si venía de una propuesta almacenada, marcarla como aprobada
        if db_proposal:
            db_proposal.status = "approved"
            db_proposal.processed_at = datetime.utcnow()
            session.commit()

    return {
        "success": True, 
        "message": f"Cambios aplicados. {updated_count} actualizaciones.",
        "errors": errors
    }


async def handle_ai_apply_merge(data: dict[str, Any], user_data: dict[str, Any]):
    """Consolida dos series en una sola tras aprobación de la IA."""
    proposal_id = data.get("proposal_id")
    if not proposal_id:
        raise HTTPException(status_code=400, detail="Falta proposal_id")

    from models.library_models import LocalBook, SeriesMetadata, MetadataProposal
    from utils.library_db import get_session
    from services.scanner_service import ScannerService

    with get_session() as session:
        db_proposal = session.query(MetadataProposal).get(proposal_id)
        if not db_proposal or db_proposal.type != "merge":
            raise HTTPException(status_code=404, detail="Propuesta de fusión no encontrada")

        hash_a = db_proposal.series_hash
        hash_b = db_proposal.secondary_hash
        proposal = db_proposal.proposal_data
        
        # 1. Mover todos los libros de B a A
        from sqlalchemy import update
        res = session.execute(
            update(LocalBook)
            .where(LocalBook.series_hash == hash_b)
            .values(series_hash=hash_a)
        )
        moved_count = res.rowcount

        # 2. Actualizar metadata de la serie A si el usuario aprobó un nombre específico
        main_name = proposal.get("suggested_main_name")
        main_spanish = proposal.get("suggested_spanish_name")
        if main_name:
            series_a = session.query(SeriesMetadata).filter_by(series_hash=hash_a).first()
            if series_a:
                series_a.series_name = main_name
                if main_spanish:
                    series_a.series_spanish = main_spanish
            
            # Sincronizar nombre en los libros movidos
            session.execute(
                update(LocalBook)
                .where(LocalBook.series_hash == hash_a)
                .values(
                    series=main_name,
                    series_spanish=main_spanish or main_name
                )
            )
            
            # Cloud Sync A
            if config.ENABLE_SUPABASE:
                try:
                    from core.supabase_manager import supabase_manager
                    client = supabase_manager.get_client()
                    if series_a:
                        client.table("series_metadata").upsert({
                            "series_hash": series_a.series_hash,
                            "series_name": series_a.series_name,
                            "series_spanish": series_a.series_spanish
                        }, on_conflict="series_hash").execute()
                    # Delete B from cloud too
                    client.table("series_metadata").delete().eq("series_hash", hash_b).execute()
                except Exception: pass

        # 3. Eliminar la serie B nula
        session.query(SeriesMetadata).filter_by(series_hash=hash_b).delete()

        # 4. Marcar como procesada
        db_proposal.status = "approved"
        db_proposal.processed_at = datetime.utcnow()
        
        session.commit()
        
        # 5. Volver a sincronizar metadata para consolidar conteos, etc.
        ScannerService.sync_series_metadata(session, hash_a)
        session.commit()

        return {
            "success": True,
            "message": f"Fusión completada. {moved_count} libros movidos a la serie principal."
        }

async def handle_ai_generate_summary(data: dict[str, Any], user_data: dict[str, Any]):
    """
    Genera una sinopsis corta por IA para un libro.
    """
    from sqlalchemy import select

    from core.db_manager_pg import pg_manager
    from models.library_models import LocalBook
    from services.ai_service import AIService

    book_id_raw = data.get("bookId")
    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    try:
        book_id = int(str(book_id_raw).replace("local_", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de libro inválido")

    async with pg_manager.get_session() as session:
        stmt = select(LocalBook).where(LocalBook.id == book_id)
        res = await session.execute(stmt)
        book = res.scalar()

        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        if not book.description:
            return {"success": False, "message": "El libro no tiene una descripción base para resumir."}

        # Generar sinopsis
        summary = await AIService.generate_synopsis(book.title, book.description)
        if summary:
            book.summary = summary
            await session.commit()
            return {
                "success": True, 
                "summary": summary,
                "message": "Sinopsis generada y guardada."
            }
        else:
            return {"success": False, "message": "Fallo al generar la sinopsis con IA."}

async def handle_ai_get_proposals(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve la lista de propuestas de IA pendientes de revisión."""
    from models.library_models import MetadataProposal
    from utils.library_db import get_session
    
    with get_session() as session:
        proposals = session.query(MetadataProposal).filter_by(status="pending").order_by(MetadataProposal.created_at.desc()).all()
        return {
            "success": True,
            "proposals": [
                {
                    "id": p.id,
                    "series_hash": p.series_hash,
                    "secondary_hash": p.secondary_hash,
                    "type": p.type,
                    "proposal": p.proposal_data,
                    "created_at": p.created_at.isoformat()
                } for p in proposals
            ]
        }

async def handle_ai_reject_proposal(data: dict[str, Any], user_data: dict[str, Any]):
    """Rechaza una propuesta de IA."""
    proposal_id = data.get("proposal_id")
    if not proposal_id:
        raise HTTPException(status_code=400, detail="Falta proposal_id")
        
    from models.library_models import MetadataProposal
    from utils.library_db import get_session
    from datetime import datetime
    
    with get_session() as session:
        p = session.query(MetadataProposal).get(proposal_id)
        if p:
            p.status = "rejected"
            p.processed_at = datetime.utcnow()
            session.commit()
            return {"success": True, "message": "Propuesta rechazada."}
        else:
            return {"success": False, "message": "Propuesta no encontrada."}

async def handle_ai_reset_series(data: dict[str, Any], user_data: dict[str, Any]):
    """Limpia los metadatos de una serie para que la IA la vuelva a analizar."""
    series_hash = data.get("series_hash")
    if not series_hash:
        raise HTTPException(status_code=400, detail="Falta series_hash")
        
    from models.library_models import LocalBook, SeriesMetadata, MetadataProposal
    from utils.library_db import get_session
    from sqlalchemy import update
    
    with get_session() as session:
        # 1. Resetear libros
        session.execute(
            update(LocalBook)
            .where(LocalBook.series_hash == series_hash)
            .values(series_spanish=None)
        )
        
        # 2. Resetear Serie
        series = session.query(SeriesMetadata).filter_by(series_hash=series_hash).first()
        if series:
            series.series_spanish = None
            
        # 3. Eliminar propuestas pendientes/anteriores
        session.query(MetadataProposal).filter_by(series_hash=series_hash).delete()
        
        session.commit()
        return {"success": True, "message": "Metadatos de la serie reseteados. El Jardinero IA la procesará en breve."}
