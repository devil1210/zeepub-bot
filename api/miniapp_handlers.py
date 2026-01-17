import json
import logging
from sqlalchemy import func
import urllib.parse
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import HTTPException

from config.config_settings import config
import os
from core.db_manager import db_manager
from core.supabase_manager import supabase_manager
from utils.library_db import get_session
from models.library_models import LocalBook, LibrarySource
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
        "user": {
            "id": user_id,
            "username": user_data.get("nickname") or f"User_{user_id}",
            "role": role_key,
            "status_label": system_role_text,
            "downloads": {
                "used": used,
                "limit": max_dl
            }
        },
        "timeUntilReset": f"{hours}h {minutes}m",
        "hasUnlimitedDownloads": max_dl is None and role_key != "banned",
        "isBanned": role_key == "banned",
        "isAdmin": role_key == "admin",
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
    # user_role = user_data.get("role", "free")

    # if user_role not in ("admin", "staff"):
    #     raise HTTPException(status_code=403, detail="Beta exclusiva para Staff")

    limit = data.get("limit", 10)
    recs = await RecommendationService.get_recommendations(user_id, limit=limit)

    results = []
    for r in recs:
        is_dict = isinstance(r, dict)
        r_id = r.get("id") if is_dict else r.id
        # Extract numeric ID from prefixed ID if needed
        numeric_id = str(r_id).replace("local_", "") if isinstance(r_id, str) else r_id
        
        # Always generate cover URL if book has a cover
        has_cover = (r.get("cover_path") if is_dict else getattr(r, 'cover_path', None)) or (r.get("cover") if is_dict else getattr(r, 'cover', None))
        cover_url = f"/api/library/covers/{numeric_id}" if has_cover else None
        
        results.append(
            {
                "id": f"local_{numeric_id}",
                "title": r.get("title") if is_dict else r.title,
                "author": r.get("author") if is_dict else r.author,
                "cover": cover_url,
                "downloadUrl": f"local_{numeric_id}",
                "is_folder": False,
                "series": r.get("series") if is_dict else getattr(r, 'series', None),
                "seriesIndex": r.get("series_index") if is_dict else getattr(r, 'series_index', None),
                "cleanTitle": r.get("title") if is_dict else r.title,
                "rating_average": (
                    r.get("rating_average") if is_dict else getattr(r, 'rating_average', 0)
                ) or 0,
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


async def handle_admin_stats(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Calcula y devuelve estadísticas globales para el Panel Admin."""
    user_role = user_data.get("role", "free")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    # 1. Dynamic System Metrics
    total_users = 0
    total_books = 0
    dls_24h = 0
    
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
                    lb = session.query(LocalBook).filter((LocalBook.content_hash == b_hash) | (LocalBook.title == b_title)).first()
                    if lb:
                        popular_book["author"] = lb.author
                        popular_book["cover"] = lb.cover_path
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
                lb = session.query(LocalBook).filter((LocalBook.content_hash == book_hash) | (LocalBook.title == title)).first()
                if lb:
                    popular_book["author"] = lb.author
                    popular_book["cover"] = lb.cover_path
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
        "totalBooks": total_books,
        "downloads24h": dls_24h,
        "uptime": uptime_text
    }


async def handle_admin_get_tiers(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Obtiene todos los niveles y su configuración."""
    user_role = user_data.get("role", "free")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    levels = await user_repo.get_all_levels()
    logger.info(f"ADMIN: handle_admin_get_tiers found {len(levels)} levels")
    return {"levels": levels}


async def handle_admin_save_tier(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Guarda cambios en un nivel."""
    user_role = user_data.get("role", "free")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    level_id = data.get("id")
    if not level_id:
        raise HTTPException(status_code=400, detail="Falta level_id")
    
    await user_repo.update_level(int(level_id), data)
    return {"success": True}


async def handle_admin_get_users(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Obtiene la lista paginada de usuarios para el panel admin."""
    user_role = user_data.get("role", "free")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    limit = data.get("limit", 20)
    offset = data.get("offset", 0)
    search = data.get("search")
    
    users = await user_repo.list_users(limit=limit, offset=offset, search=search)
    logger.info(f"ADMIN: handle_admin_get_users found {len(users)} users (limit={limit}, offset={offset}, search={search})")
    return {"users": users}


async def handle_admin_set_user_level(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Cambia el nivel de un usuario específico."""
    user_role = user_data.get("role", "free")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    target_id = data.get("userId")
    level_id = data.get("levelId")
    
    if not target_id or not level_id:
        raise HTTPException(status_code=400, detail="Faltan parámetros userId o levelId")
    
    await user_repo.update_user_level(int(target_id), int(level_id))
    return {"success": True}


async def handle_admin_backup_library(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Syncs SQLite library data to Supabase."""
    user_role = user_data.get("role", "free")
    if user_role != "admin":
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
                    "series_clean": b.series_clean,
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
                    "cover_path": b.cover_path,
                    "file_created_at": b.file_created_at.isoformat() if b.file_created_at else None,
                    "file_modified_at": b.file_modified_at.isoformat() if b.file_modified_at else None,
                    "indexed_at": b.indexed_at.isoformat() if b.indexed_at else None,
                    "series_hash": b.series_hash,
                    "content_hash": b.content_hash
                })
            client.table('local_books').upsert(books_data).execute()
            
        session.close()
        return {"success": True, "message": f"Sincronizados {len(sources)} fuentes y {len(books)} libros."}
    except Exception as e:
        logger.error(f"Error backup library to Supabase: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_scan_library(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Activates forced library scan."""
    user_role = user_data.get("role", "free")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    force = data.get("force", False)
    
    try:
        from services.scanner_service import ScannerService
        libs_json = os.getenv("LOCAL_LIBRARIES")
        if not libs_json:
            return {"success": False, "message": "LOCAL_LIBRARIES no configurada."}
            
        scanner = ScannerService(libs_json)
        # We use asyncio.to_thread to not block the FastAPI loop
        await asyncio.to_thread(scanner.sync_all, force_scan=force)
        
        return {"success": True, "message": "Escaneo completado."}
    except Exception as e:
        logger.error(f"Error scanning library via API: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_save_tier_config(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Guarda la configuración completa de un nivel/tier."""
    user_role = user_data.get("role", "free")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    tier_name = data.get("name")
    if not tier_name:
        raise HTTPException(status_code=400, detail="Falta el nombre del tier")
    
    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}
    
    try:
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
            "uiPrimaryColor": "ui_primary_color",
            "panelTransparency": "panel_transparency"
        }
        
        for frontend_key, db_key in field_mapping.items():
            if frontend_key in data and data[frontend_key] is not None:
                update_data[db_key] = data[frontend_key]
        
        # Update tier in Supabase
        client.table('user_levels').update(update_data).eq('id', tier_id).execute()
        
        logger.info(f"ADMIN: Saved tier config for '{tier_name}' (ID: {tier_id})")
        return {"success": True, "tierId": tier_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving tier config: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_tier_config(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Obtiene la configuración completa de un nivel/tier."""
    user_role = user_data.get("role", "free")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    tier_name = data.get("name")
    tier_id = data.get("id")
    
    if not tier_name and not tier_id:
        raise HTTPException(status_code=400, detail="Falta name o id del tier")
    
    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}
    
    try:
        # from core.supabase_client import get_supabase_client
        client = supabase_manager.get_client()
        
        query = client.table('user_levels').select('*')
        if tier_id:
            query = query.eq('id', tier_id)
        else:
            query = query.ilike('name', tier_name)
        
        result = query.execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Tier no encontrado")
        
        tier = result.data[0]
        return {
            "success": True,
            "tier": {
                "id": tier.get("id"),
                "name": tier.get("name"),
                "icon": tier.get("icon", "verified"),
                "color": tier.get("color", "#0da6f2"),
                "dailyDownloads": tier.get("daily_downloads", 1),
                "maxConcurrent": tier.get("max_concurrent", 3),
                "priorityRequests": tier.get("priority_requests", False),
                "earlyAccess": tier.get("early_access", False),
                "customThemes": tier.get("custom_themes", False),
                "uiPrimaryColor": tier.get("ui_primary_color", "#0da6f2"),
                "panelTransparency": tier.get("panel_transparency", 70),
                "price": tier.get("price", 0),
                "priority": tier.get("priority", 0)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tier config: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_save_user_permissions(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Guarda los permisos de un usuario específico."""
    logger.info(f"ADMIN: Save permissions request for data: {data}")
    user_role = user_data.get("role", "free")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Falta userId")
    
    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}
    
    try:
        # from core.supabase_client import get_supabase_client
        client = supabase_manager.get_client()
        
        # Build update data
        update_data = {
            "updated_at": "now()"
        }
        
        # Map frontend fields to database columns
        field_mapping = {
            "levelId": "level_id",
            "canReport": "can_report",
            "bypassLimits": "bypass_limits",
            "betaTester": "beta_tester",
            "isAdmin": "is_super_admin",
            "role": "role"
        }
        
        for frontend_key, db_key in field_mapping.items():
            if frontend_key in data and data[frontend_key] is not None:
                # Special handling for isAdmin -> sets role to 'admin'
                if frontend_key == "isAdmin" and data[frontend_key]:
                    update_data["role"] = "admin"
                elif frontend_key == "isAdmin" and not data[frontend_key]:
                    # Don't downgrade if we're not explicitly setting role
                    if "role" not in data:
                        continue
                else:
                    update_data[db_key] = data[frontend_key]
        
        # Update user in Supabase
        client.table('users').update(update_data).eq('telegram_id', int(user_id)).execute()
        
        logger.info(f"ADMIN: Saved user permissions for user {user_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error saving user permissions: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_user_permissions(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Obtiene los permisos de un usuario específico."""
    logger.info(f"ADMIN: Get permissions request for data: {data}")
    user_role = user_data.get("role", "free")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Falta userId")
    
    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}
    
    try:
        # from core.supabase_client import get_supabase_client
        client = supabase_manager.get_client()
        
        result = client.table('users').select(
            'telegram_id, nickname, role, level_id, can_report, bypass_limits, beta_tester, is_super_admin, added_at'
        ).eq('telegram_id', int(user_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user = result.data[0]
        
        # Get level info
        level_info = None
        if user.get("level_id"):
            level_result = client.table('user_levels').select('name, color').eq('id', user['level_id']).execute()
            if level_result.data:
                level_info = level_result.data[0]
        
        return {
            "success": True,
            "user": {
                "id": str(user.get("telegram_id")),
                "username": user.get("nickname", f"User_{user.get('telegram_id')}"),
                "role": user.get("role", "free"),
                "levelId": user.get("level_id"),
                "levelName": level_info.get("name") if level_info else "Básico",
                "levelColor": level_info.get("color") if level_info else "#6b7280",
                "canReport": user.get("can_report", True),
                "bypassLimits": user.get("bypass_limits", False),
                "betaTester": user.get("beta_tester", False),
                "isAdmin": user.get("is_super_admin", False) or user.get("role") == "admin",
                "addedAt": user.get("added_at")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return {"success": False, "message": str(e)}
