import json
import logging
import re
import urllib.parse
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import HTTPException
from sqlalchemy import func

from config.config_settings import config
from core.state_manager import state_manager
from models.download_models import DownloadHistory
from models.library_models import LocalBook
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
from utils.library_db import get_session

logger = logging.getLogger(__name__)

# --- Handlers ---


async def handle_search(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Busca libros en la base de datos local o en el servidor OPDS."""
    user_id = user_data.get("user_id", 0)
    user_role = user_data.get("role", "free")
    query = data.get("query")
    page_url = data.get("pageUrl")
    page = data.get("page", 1)

    if not query and not page_url:
        return {"results": []}

    # [NEW] Prioritize Local DB Search for ZeePub library
    is_local_search = not page_url or (
        page_url == config.OPDS_ROOT_START
        or page_url == config.OPDS_ROOT_EVIL
        or page_url == "root"
        or "/api/library/catalog" in page_url
    )

    if is_local_search and query:
        logger.info(f"[search] Using LibraryService for native SQL search: {query}")
        return await LibraryService.search_books(query, page=page, search_type=data.get("type", "all"))

    # OPDS Fallback
    target_url = (
        page_url
        if page_url
        else build_search_url(query, uid=user_id, role=user_role)
    )

    # API 9.3: Feedback en streaming
    if not page_url:
        from utils.streaming import send_message_draft
        from api.main import bot
        await send_message_draft(bot=bot.app.bot, chat_id=user_id, text=f"🔍 <b>Buscando:</b> {query}...")

    feed = await get_cached_feed(target_url)

    # Determine the best base URL for relative links
    feed_base_url = target_url
    for link in getattr(feed.feed, "links", []):
        if link.get("rel") == "self":
            feed_base_url = abs_url(target_url, link.get("href"))
            break

    results = []
    entries = getattr(feed, "entries", [])

    # Extract pagination links
    next_page = None
    prev_page = None
    first_page = None
    last_page = None

    for link in getattr(feed.feed, "links", []):
        rel = link.get("rel", "")
        href = abs_url(feed_base_url, link.get("href", ""))
        if rel == "next":
            next_page = href
        elif rel in ("previous", "prev"):
            prev_page = href
        elif rel == "first":
            first_page = href
        elif rel == "last":
            last_page = href

    current_page = 1
    if page_url and "page=" in page_url:
        parsed = urllib.parse.urlparse(page_url)
        params = urllib.parse.parse_qs(parsed.query)
        try:
            current_page = int(params.get("page", [1])[0])
        except (ValueError, TypeError):
            current_page = 1

    total_pages = None
    total_results = feed.feed.get("opensearch_totalresults")
    items_per_page = feed.feed.get("opensearch_itemsperpage")
    if total_results and items_per_page:
        try:
            total_pages = (int(total_results) + int(items_per_page) - 1) // int(items_per_page)
        except Exception:
            pass

    for entry in entries:
        book_id = entry.get("id", "")
        title = entry.get("title", "Sin título")

        is_folder = any(link.get("rel") == "subsection" for link in getattr(entry, "links", []))
        author = extract_author(entry, is_folder=is_folder)

        summary = entry.get("summary", "")
        if summary:
            summary = summary.replace("Format: Epub Summary: ", "").replace("Format: Epub ", "").replace("Summary: ", "").strip()

        publisher = entry.get("dc_publisher") or entry.get("dcterms_publisher")
        language = entry.get("dc_language") or entry.get("dcterms_language")
        published = entry.get("published") or entry.get("issued")
        year = published[:4] if published and len(published) >= 4 else None

        isbn = None
        identifier = entry.get("identifier")
        if identifier and "isbn" in identifier.lower():
            isbn = identifier.split(":")[-1].strip()

        download_url = None
        cover_url = None
        subsection_url = None
        detail_url = None
        size = None
        file_type = None

        for link in getattr(entry, "links", []):
            rel = link.get("rel", "")
            href = abs_url(feed_base_url, link.get("href", ""))
            ltype = link.get("type", "")

            if rel == "subsection":
                subsection_url = href
            elif rel in ("self", "alternate") or "type=entry" in ltype:
                if not detail_url or rel == "self":
                    detail_url = href
            elif "acquisition" in rel or "epub" in ltype:
                download_url = href
                file_type = ltype
                size = link.get("contentlength") or link.get("length")
            elif "image" in rel or "cover" in rel:
                cover_url = href

        if not detail_url and book_id:
            detail_url = abs_url(feed_base_url, book_id)

        raw_tags = getattr(entry, "tags", [])
        categories = [tag.get("label") or tag.get("term") for tag in raw_tags if tag.get("label") or tag.get("term")]

        title_meta = parse_metadata_from_title(title)
        entry_series = entry.get("calibre_series") or entry.get("schema_series")
        entry_series_index = entry.get("calibre_series_index")

        final_series = entry_series or title_meta.get("series", "")
        final_series_index = entry_series_index or title_meta.get("volume", "")

        results.append({
            "id": book_id,
            "title": title,
            "author": author,
            "illustrator": extract_creators_by_role(entry, "ill"),
            "translator": extract_creators_by_role(entry, "trl"),
            "summary": summary,
            "cover": cover_url,
            "downloadUrl": download_url,
            "subsectionUrl": subsection_url,
            "detailUrl": detail_url,
            "publisher": publisher,
            "language": language,
            "isbn": isbn,
            "year": year,
            "size": size,
            "fileType": file_type,
            "is_folder": subsection_url is not None,
            "updatedDate": entry.get("updated") or entry.get("published") or "",
            "series": final_series,
            "seriesIndex": final_series_index,
            "tags": title_meta.get("tags", []),
            "cleanTitle": title_meta.get("clean_title", title),
            "romaji": title_meta.get("romaji", ""),
            "categories": categories,
            "wordCount": entry.get("kavita_wordcount") or entry.get("calibre_wordcount"),
            "pageCount": entry.get("kavita_pagecount") or entry.get("calibre_pagecount"),
            "readingTime": entry.get("kavita_readingtime") or entry.get("calibre_readingtime"),
        })

    async def fetch_folder_cover(res):
        if res["is_folder"] and not res["cover"]:
            try:
                sub_feed = await get_cached_feed(res["subsectionUrl"])
                sub_entries = getattr(sub_feed, "entries", [])
                if sub_entries:
                    first_book = sub_entries[0]
                    for l in getattr(first_book, "links", []):
                        if "image" in l.get("rel", "") or "cover" in l.get("rel", ""):
                            res["cover"] = abs_url(config.BASE_URL, l.get("href", ""))
                            break
            except Exception:
                pass

    folder_tasks = [fetch_folder_cover(r) for r in results if r["is_folder"] and not r["cover"]]
    if folder_tasks:
        await asyncio.gather(*folder_tasks[:10])

    return {
        "results": results,
        "nextPage": next_page,
        "prevPage": prev_page,
        "firstPage": first_page,
        "lastPage": last_page,
        "currentPage": current_page,
        "totalPages": total_pages,
    }


async def handle_book_detail(data: Dict[str, Any], user_data: Dict[str, Any]):
    """Devuelve el detalle de un libro desde la base de datos local o OPDS."""
    user_id = user_data.get("user_id", 0)
    book_id_raw = data.get("bookId")
    logger.info(f"[book-detail] Request received - bookId: {book_id_raw}")

    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    # 1. Local Book
    if isinstance(book_id_raw, str) and (book_id_raw.startswith("local_") or book_id_raw.isdigit()):
        clean_id = int(book_id_raw.replace("local_", ""))
        local_book = await LibraryService.get_book_by_id(clean_id)
        if local_book:
            logger.info(f"[book-detail] Found local book via LibraryService: {local_book['title']}")
            local_book["is_downloaded"] = await download_repo.has_user_downloaded(
                user_id, local_book["title"], local_book.get("cleanTitle"), local_book.get("content_hash")
            )
            local_book["download_count"] = await download_repo.get_total_download_count(
                local_book["title"], local_book.get("cleanTitle"), local_book.get("content_hash")
            )
            return local_book

    # 2. OPDS detail
    book_id_url = book_id_raw
    if not book_id_url.startswith("http"):
        book_id_url = abs_url(config.OPDS_ROOT_START, book_id_url)

    logger.info(f"[book-detail] Fetching feed from: {book_id_url}")
    try:
        feed = await get_cached_feed(book_id_url)
    except Exception as e:
        logger.error(f"[book-detail] Error fetching {book_id_url}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid book URL: {book_id_url}")

    if not feed:
        raise HTTPException(status_code=502, detail="Error en el servidor de origen (OPDS). Intenta más tarde.")

    entries = getattr(feed, "entries", [])
    entry = entries[0] if entries else (feed.feed if getattr(feed, "feed", None) else None)

    if not entry:
        raise HTTPException(status_code=404, detail="Book detail not found")

    entry_base_url = book_id_url
    for link in getattr(entry, "links", []):
        if link.get("rel") == "self":
            entry_base_url = abs_url(book_id_url, link.get("href"))
            break

    publisher = entry.get("dc_publisher") or entry.get("dcterms_publisher")
    language = entry.get("dc_language") or entry.get("dcterms_language")
    published = entry.get("published") or entry.get("issued")
    year = published[:4] if published and len(published) >= 4 else None

    isbn = None
    identifier = entry.get("identifier")
    if identifier and "isbn" in identifier.lower():
        isbn = identifier.split(":")[-1].strip()

    series = entry.get("calibre_series") or entry.get("schema_series")
    series_index = entry.get("calibre_series_index")
    categories = [cat.get("term") for cat in entry.get("tags", []) if cat.get("term")]

    asin = None
    for ident in entry.get("identifiers", []):
        if isinstance(ident, dict) and ident.get("scheme", "").upper() == "ASIN":
            asin = ident.get("value")
            break
    if not asin and identifier and "asin" in identifier.lower():
        asin = identifier.split(":")[-1].strip()

    extracted_meta = parse_metadata_from_title(entry.get("title", ""))
    for ttag in extracted_meta.get("tags", []):
        if ttag not in categories:
            categories.append(ttag)

    if not series and extracted_meta.get("series"):
        series = extracted_meta["series"]
    if not series_index and extracted_meta.get("volume"):
        series_index = extracted_meta["volume"]

    download_url = None
    cover_url = None
    size = None
    file_type = None
    up_url = None

    for link in getattr(entry, "links", []):
        rel = link.get("rel", "")
        l_type = link.get("type", "")
        href = abs_url(entry_base_url, link.get("href", ""))

        if "acquisition" in rel or "epub" in l_type.lower():
            if not download_url or "epub" in l_type.lower():
                download_url = href
                file_type = l_type
                size = link.get("contentlength") or link.get("length")
        elif "image" in rel or "cover" in rel or "thumbnail" in rel:
            if not cover_url or "image" in rel:
                cover_url = href
        elif rel in ["up", "collection", "ancestor", "index", "breadcrumb"]:
            if not up_url or rel == "up":
                up_url = href

    if not cover_url and "content" in entry:
        for content in entry.get("content", []):
            if "image" in content.get("type", ""):
                cover_url = abs_url(entry_base_url, content.get("value", ""))
                break

    is_folder = up_url is not None
    author = extract_author(entry, is_folder=is_folder)

    result = {
        "id": entry.get("id", ""),
        "title": entry.get("title", "Sin título"),
        "author": author,
        "summary": entry.get("summary", ""),
        "cover": cover_url,
        "downloadUrl": download_url,
        "publisher": publisher,
        "language": language,
        "isbn": isbn,
        "asin": asin,
        "series": series or "",
        "seriesIndex": series_index or "",
        "categories": categories,
        "year": year,
        "size": size,
        "fileType": file_type,
        "upUrl": up_url,
        "updatedDate": entry.get("updated", "") or entry.get("published", ""),
        "illustrator": extract_creators_by_role(entry, "ill"),
        "translator": extract_creators_by_role(entry, "trl"),
        "layoutBy": extract_creators_by_role(entry, "bkp"),
        "epubVersion": entry.get("dc_version") or entry.get("kavita_format_version"),
        "wordCount": entry.get("kavita_wordcount") or entry.get("calibre_wordcount"),
        "pageCount": entry.get("kavita_pagecount") or entry.get("calibre_pagecount"),
        "readingTime": entry.get("kavita_readingtime") or entry.get("calibre_readingtime"),
        "romaji": extracted_meta.get("romaji", ""),
        "cleanTitle": extracted_meta.get("clean_title") or entry.get("title", ""),
        "tags": extracted_meta.get("tags", []),
        "content_hash": entry.get("content_hash") or entry.get("hash"),
        "is_downloaded": False,
        "download_count": 0
    }

    # Get metrics from centralized DB
    from repositories.metrics_repository import metrics_repo
    content_hash = entry.get("content_hash") or entry.get("hash")
    if content_hash:
        result["is_downloaded"] = await metrics_repo.has_downloaded(user_id, content_hash)
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
        "admin": "Admin 🛠️", "staff": "Staff 🛡️", "premium": "Premium ✨",
        "vip": "VIP ⭐️", "white": "Patrocinador 🤍", "free": "Lector 📚",
        "banned": "🚫 Baneado"
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
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
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
        "role": role_key
    }


async def handle_user_downloads_history(data: Dict[str, Any], user_data: Dict[str, Any]):
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
        results.append({
            "id": f"local_{r_id}",
            "title": r.get("title") if is_dict else r.title,
            "author": r.get("author") if is_dict else r.author,
            "cover": f"/api/library/covers/{r_id}" if (r.get("cover_path") if is_dict else r.cover_path) else None,
            "downloadUrl": f"local_{r_id}",
            "is_folder": False,
            "series": r.get("series") if is_dict else r.series,
            "seriesIndex": r.get("series_index") if is_dict else r.series_index,
            "cleanTitle": r.get("title") if is_dict else r.title,
            "rating_average": (r.get("rating_average") if is_dict else r.rating_average) or 0
        })
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
        raise HTTPException(status_code=400, detail="ID de libro inválido para votación")

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
        raise HTTPException(status_code=403, detail="Solo administradores pueden guardar configuración global")

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
            target_chat_id = target_id_override or get_setting("mini_app_channel_id", "@ZeePubs")
        elif target == "group":
            target_chat_id = target_id_override or get_setting("mini_app_group_id", "@ZeePubBotTest")
            message_thread_id = thread_id_override

    metadata_override = None
    actual_download_url = book_id  # Default to book_id for remote books

    if book_id.startswith("local_") or book_id.isdigit():
        try:
            local_id = int(str(book_id).replace("local_", ""))
            local_book_obj = await LibraryService.get_book_by_id(local_id)
            if local_book_obj:
                # Get the actual file path
                actual_download_url = local_book_obj.get("downloadUrl") or local_book_obj.get("filepath")

                # We need the full dict with hashes
                from services.library_service import LibraryService
                async with LibraryService._session_scope() as session:
                    from models.library_models import LocalBook
                    lb = session.query(LocalBook).get(local_id)
                    if lb:
                        metadata_override = lb.to_dict()
                        # Ensure the file path is set
                        if not actual_download_url:
                            actual_download_url = lb.filepath
                        logger.debug(f"Local book metadata: content_hash={metadata_override.get('content_hash')}, filepath={actual_download_url}")
        except Exception as e:
            logger.error(f"Error fetching metadata for handle_download: {e}")

    success = await enviar_libro_directo(
        bot=bot.app.bot,
        user_id=user_id,
        title=title,
        download_url=actual_download_url,
        target_chat_id=target_chat_id,
        message_thread_id=message_thread_id,
        metadata_override=metadata_override
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
            "primaryColor": "#3b82f6", "uiScale": 1.0, "avatarScale": 1.0,
            "isDarkMode": True, "showSearchCard": True, "showSearchBar": False,
            "showDonateCard": True, "showHelpCard": True, "showSettingsInMenu": False,
            "dataSaver": False, "badgePosTop": 8, "badgePosRight": 8,
            "showPosTool": False, "badgePosMode": "relative"
        }

        # Load global and badge config
        try:
            final_settings.update({
                "badgePosTop": int(get_setting("badge_pos_top", "8")),
                "badgePosRight": int(get_setting("badge_pos_right", "8")),
                "showPosTool": get_setting("show_pos_tool", "false").lower() == "true",
                "badgePosMode": get_setting("badge_pos_mode", "relative")
            })
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
                raise HTTPException(status_code=403, detail="Solo administradores pueden cambiar la configuración global")

            settings_obj["ui_version"] = int(time.time())
            set_setting(f"ui_defaults_{target_role}", json.dumps(settings_obj))

            if data.get("forceOverwrite"):
                role_to_level = {"admin": 1, "staff": 2, "premium": 3, "vip": 4, "white": 5, "free": 6}
                l_id = role_to_level.get(target_role)
                if l_id:
                    await user_repo.reset_level_users_settings(l_id)

            return {"success": True, "message": f"Configuración para {target_role} guardada (v{settings_obj['ui_version']})"}


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
        desc = await cms_plugin.get_text("star_payment_invoice_desc", Nivel=tier.capitalize())

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
                entry = entries[0] if entries else (feed.feed if getattr(feed, "feed", None) else None)
                if entry:
                    title_for_query = entry.get("title")
                    meta = parse_metadata_from_title(title_for_query)
                    clean_title_for_query = meta.get("clean_title")
                    # For OPDS books we don't have a stable binary hash,
                    # but we can simulate one if we want consistency across scanners.
                    # For now, title-based fallback in repository will handle it.
        except Exception as e:
            logger.error(f"[handle_get_download_count] Error resolving OPDS title for {book_id}: {e}")

    if not title_for_query and not book_hash_for_query:
        return {"count": 0}

    from repositories.metrics_repository import metrics_repo
    count = await metrics_repo.get_total_downloads(book_hash_for_query) if book_hash_for_query else 0
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
