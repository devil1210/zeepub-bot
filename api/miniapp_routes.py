import json
import logging
import os

import hashlib
import hmac
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from functools import wraps

from api.deps import get_telegram_user_id, get_current_user_data, require_admin, require_mini_app_access
from config.config_settings import config
from services.user_service import get_effective_user
from utils.security import validate_telegram_data, verify_telegram_user
from services.opds_service import get_cached_feed
from services.telegram_service import enviar_libro_directo
from utils.helpers import build_search_url, abs_url, extract_author

router = APIRouter(tags=["miniapp"])
logger = logging.getLogger(__name__)


# --- Modelos Pydantic ---


class AccessCheckRequest(BaseModel):
    user_id: int


class UserLevelModel(BaseModel):
    id: str
    name: str
    priority: int
    color: str
    hasAccess: bool


class AccessResponse(BaseModel):
    level: UserLevelModel
    hasAccess: bool
    isAdmin: bool


class LevelUpdate(BaseModel):
    id: str
    hasAccess: bool


class UpdateLevelsRequest(BaseModel):
    levels: List[LevelUpdate]

# --- Routes ---


@router.post("/api/bot")
async def handle_bot_request(
    request: Request,
    user_data: Dict[str, Any] = Depends(require_mini_app_access),
):
    """
    Main endpoint for Mini App requests.
    Dispatches actions: search, download, status, etc.
    """
    user_id = user_data.get("user_id", 0)
    user_role = user_data.get("role", "free")
    # Store for further use
    user_effective = user_data

    try:
        body = await request.json()
    except Exception:
        body = {}

    action = body.get("action")
    data = body.get("data", {})

    # --- Control de Acceso por Niveles ---
    # Los administradores siempre tienen acceso.
    # El resto depende de su nivel (has_mini_app_access).
    if user_effective.get("has_mini_app_access") is False and action != "status":
        raise HTTPException(
            status_code=403,
            detail="Tu nivel de usuario no tiene acceso a la Mini App"
        )

    logger.info(f"Miniapp action: {action} User: {user_id} Role: {user_role}")

    try:
        if action == "search":
            query = data.get("query")
            page_url = data.get("pageUrl")

            if not query and not page_url:
                return {"results": []}

            target_url = (
                page_url
                if page_url
                else build_search_url(query, uid=user_id, role=user_role)
            )

            # API 9.3: Feedback en streaming vía borrador de mensaje
            if not page_url:  # Solo en búsqueda inicial, no en paginación
                from utils.streaming import send_message_draft
                from api.main import bot
                await send_message_draft(
                    bot=bot.app.bot,
                    chat_id=user_id,
                    text=f"🔍 <b>Buscando:</b> {query}..."
                )

            feed = await get_cached_feed(target_url)

            # Determine the best base URL for relative links
            feed_base_url = target_url
            for link in getattr(feed.feed, "links", []):
                if link.get("rel") == "self":
                    feed_base_url = abs_url(target_url, link.get("href"))
                    break

            results = []
            entries = getattr(feed, "entries", [])

            # Extract pagination links from feed.links
            next_page = None
            prev_page = None
            first_page = None
            last_page = None

            for link in getattr(feed.feed, "links", []):
                rel = link.get("rel", "")
                href = abs_url(feed_base_url, link.get("href", ""))
                if rel == "next":
                    next_page = href
                elif rel == "previous" or rel == "prev":
                    prev_page = href
                elif rel == "first":
                    first_page = href
                elif rel == "last":
                    last_page = href

            # Try to guess current page from URL or feed metadata
            # (This part depends on the OPDS server implementation)
            current_page = 1
            if page_url and "page=" in page_url:
                import urllib.parse

                parsed = urllib.parse.urlparse(page_url)
                params = urllib.parse.parse_qs(parsed.query)
                current_page = int(params.get("page", [1])[0])

            # Total results/pages if available
            total_pages = None
            # Some feeds provide opensearch:totalResults and opensearch:itemsPerPage
            # feedparser might put them in feed.feed
            total_results = feed.feed.get("opensearch_totalresults")
            items_per_page = feed.feed.get("opensearch_itemsperpage")
            if total_results and items_per_page:
                try:
                    total_pages = (int(total_results) + int(items_per_page) - 1) // int(
                        items_per_page
                    )
                except Exception:  # Changed from bare except
                    pass

            # First pass: collect all data
            for entry in entries:
                book_id = entry.get("id", "")
                title = entry.get("title", "Sin título")

                # Robust author extraction
                is_folder = any(link.get("rel") == "subsection" for link in getattr(entry, "links", []))
                author = extract_author(entry, is_folder=is_folder)

                summary = entry.get("summary", "")

                # Extra metadata
                publisher = entry.get("dc_publisher") or entry.get("dcterms_publisher")
                language = entry.get("dc_language") or entry.get("dcterms_language")
                published = entry.get("published") or entry.get("issued")
                year = published[:4] if published and len(published) >= 4 else None

                # Try to find ISBN
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
                    elif rel == "self" or rel == "alternate" or "type=entry" in ltype:
                        if not detail_url or rel == "self":
                            detail_url = href
                    elif "acquisition" in rel or "epub" in ltype:
                        download_url = href
                        file_type = ltype
                        size = link.get("contentlength") or link.get("length")
                    elif "image" in rel or "cover" in rel:
                        cover_url = href

                # Fallback for detail_url: if missing, try to resolve the ID as a relative URL
                if not detail_url and book_id:
                    detail_url = abs_url(feed_base_url, book_id)

                results.append(
                    {
                        "id": book_id,
                        "title": title,
                        "author": author,
                        "summary": summary,
                        "cover": cover_url,
                        "download_url": download_url,
                        "subsection_url": subsection_url,
                        "detail_url": detail_url,
                        "publisher": publisher,
                        "language": language,
                        "isbn": isbn,
                        "year": year,
                        "size": size,
                        "file_type": file_type,
                        "is_folder": subsection_url is not None,
                    }
                )

            # Second pass: fetch covers for folders that don't have one
            import asyncio

            async def fetch_folder_cover(res):
                if res["is_folder"] and not res["cover"]:
                    try:
                        # Fetch the subsection feed to find the first book's cover
                        sub_feed = await get_cached_feed(res["subsection_url"])
                        sub_entries = getattr(sub_feed, "entries", [])
                        if sub_entries:
                            first_book = sub_entries[0]
                            for l in getattr(first_book, "links", []):
                                if "image" in l.get("rel", "") or "cover" in l.get(
                                    "rel", ""
                                ):
                                    res["cover"] = abs_url(
                                        config.BASE_URL, l.get("href", "")
                                    )
                                    break
                    except Exception:
                        pass

            # Only fetch for the first N folders to avoid massive delays if search is huge
            folder_tasks = [
                fetch_folder_cover(r)
                for r in results
                if r["is_folder"] and not r["cover"]
            ]
            if folder_tasks:
                await asyncio.gather(
                    *folder_tasks[:10]
                )  # Limit to 10 concurrent sub-fetches

            return {
                "results": results,
                "nextPage": next_page,
                "prevPage": prev_page,
                "firstPage": first_page,
                "lastPage": last_page,
                "currentPage": current_page,
                "totalPages": total_pages,
            }

        elif action == "book-detail":
            book_id_url = data.get("bookId")
            logger.info(f"[book-detail] Request received - bookId: {book_id_url}")

            # Initialize for extraction fallback
            subsection_url = None

            if not book_id_url:
                logger.error("[book-detail] Missing bookId parameter")
                raise HTTPException(status_code=400, detail="Missing bookId (URL)")

            # Ensure we have a valid URL (sometimes frontend might pass raw ID)
            if not book_id_url.startswith("http"):
                logger.warning(
                    f"[book-detail] bookId {book_id_url} is not a URL. Attempting to build one."
                )
                # If it's not a URL, it might be a relative path or an ID.
                # We try several fallbacks:
                # 1. Assume it's relative to the OPDS root
                book_id_url = abs_url(config.OPDS_ROOT_START, book_id_url)
                logger.info(f"[book-detail] Resolved relative ID to: {book_id_url}")

            logger.info(f"[book-detail] Fetching feed from: {book_id_url}")
            try:
                feed = await get_cached_feed(book_id_url)
            except Exception as e:
                logger.error(f"[book-detail] Error fetching {book_id_url}: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid book URL: {book_id_url}")

            if not feed:
                logger.error(f"[book-detail] No feed data returned from {book_id_url}")
                raise HTTPException(status_code=404, detail="Book detail feed not found")

            # OPDS entries can be at the top level or in feed.entries
            entries = getattr(feed, "entries", [])
            logger.info(f"[book-detail] Feed has {len(entries)} entries")

            entry = None
            if entries:
                # Try to find exact match by ID if possible, otherwise use first
                entry = entries[0]
                logger.info(
                    f"[book-detail] Using first entry: {entry.get('title', 'Unknown')}"
                )
            else:
                # Some servers return the entry as the main feed element
                if getattr(feed, "feed", None) and (
                    feed.feed.get("title") or feed.feed.get("links")
                ):
                    logger.info(
                        "[book-detail] Using feed.feed as entry (single-entry feed)"
                    )
                    entry = feed.feed

            if not entry:
                logger.error(
                    f"[book-detail] No entry or feed info found in {book_id_url}"
                )
                raise HTTPException(status_code=404, detail="Book detail not found")

            # Determine base URL for relative links
            # We try to find a 'self' link in the entry or use the fetching URL
            entry_base_url = book_id_url
            for link in getattr(entry, "links", []):
                if link.get("rel") == "self":
                    entry_base_url = abs_url(book_id_url, link.get("href"))
                    break

            # Extract metadata (same logic as search)
            publisher = entry.get("dc_publisher") or entry.get("dcterms_publisher")
            language = entry.get("dc_language") or entry.get("dcterms_language")
            published = entry.get("published") or entry.get("issued")
            year = published[:4] if published and len(published) >= 4 else None

            isbn = None
            identifier = entry.get("identifier")
            if identifier and "isbn" in identifier.lower():
                # Handle urn:isbn:978...
                parts = identifier.split(":")
                isbn = parts[-1].strip()

            # Rich Metadata: Series and Tags
            series = entry.get("calibre_series") or entry.get("schema_series")
            series_index = entry.get("calibre_series_index")
            categories = [cat.get("term") for cat in entry.get("tags", []) if cat.get("term")]

            download_url = None
            cover_url = None
            size = None
            file_type = None

            links = getattr(entry, "links", [])
            logger.info(
                f"[book-detail] Entry has {len(links)} links. Base URL: {entry_base_url}"
            )

            for link in links:
                rel = link.get("rel", "")
                l_type = link.get("type", "")
                href = abs_url(entry_base_url, link.get("href", ""))

                # Check for acquisition (download)
                if "acquisition" in rel or "epub" in l_type.lower():
                    # Prioritize epub if multiple types exist
                    if not download_url or "epub" in l_type.lower():
                        download_url = href
                        file_type = l_type
                        size = link.get("contentlength") or link.get("length")

                # Check for image (cover)
                elif "image" in rel or "cover" in rel or "thumbnail" in rel:
                    if (
                        not cover_url or "image" in rel
                    ):  # Prioritize rel="image" over others
                        cover_url = href

                # Check for parent/collection navigation
                elif rel in ["up", "collection", "ancestor", "index", "breadcrumb"]:
                    # Prioritize 'up' but accept others as fallbacks
                    if not subsection_url or rel == "up":
                        subsection_url = href

            # Fallback for cover if not found in links but exists in content
            if not cover_url and "content" in entry:
                for content in entry.get("content", []):
                    if "image" in content.get("type", ""):
                        cover_url = abs_url(entry_base_url, content.get("value", ""))
                        break

            # Robust author extraction for detail
            author = extract_author(entry, is_folder=subsection_url is not None)

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
                "series": series,
                "seriesIndex": series_index,
                "categories": categories,
                "year": year,
                "size": size,
                "fileType": file_type,
                "upUrl": subsection_url,
            }

            logger.info(
                f"[book-detail] Returning result: {result['title']} (Cover: {result['cover']}, DL: {result['downloadUrl']}, Up: {result['upUrl']})"
            )
            return result

        elif action == "user_status":
            # Return user level and download information
            from core.state_manager import state_manager
            from datetime import datetime, timedelta

            st = state_manager.get_user_state(user_id)

            # Role display mapping
            roles_display = {
                "admin": "Admin 🛠️",
                "staff": "Staff 🛡️",
                "premium": "Premium ✨",
                "vip": "VIP ⭐️",
                "white": "Patrocinador 🤍",
                "free": "Lector 📚",
            }

            role_key = user_effective.get("role", "free")
            system_role_text = roles_display.get(role_key, "Lector")
            if role_key == "banned":
                system_role_text = "🚫 Baneado"

            # Determine max downloads
            if role_key in ("admin", "staff", "premium", "banned"):
                max_dl = None
            elif role_key == "vip":
                max_dl = config.VIP_DOWNLOADS_PER_DAY
            elif role_key == "white":
                max_dl = config.WHITELIST_DOWNLOADS_PER_DAY
            else:
                max_dl = config.MAX_DOWNLOADS_PER_DAY

            # Downloads used
            used = st.get("downloads_used", 0)

            # Calculate time until next reset (midnight)
            now = datetime.now()
            next_midnight = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            time_left = next_midnight - now
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)

            result = {
                "level": system_role_text,
                "downloadsUsed": used,
                "downloadsLimit": max_dl,
                "timeUntilReset": f"{hours}h {minutes}m",
                "hasUnlimitedDownloads": max_dl is None and role_key != "banned",
                "isBanned": role_key == "banned"
            }

            logger.info(f"[user_status] User {user_id} - Role: {role_key}, Level: {system_role_text}, Used: {used}, Limit: {max_dl}, Reset: {hours}h {minutes}m")

            return result

        elif action == "user_downloads_history":
            # Return user's recent download history
            try:
                from repositories.download_repository import download_repo

                downloads = await download_repo.get_user_downloads(user_id, limit=10)

                logger.info(f"[user_downloads_history] User {user_id} - Retrieved {len(downloads)} downloads")

                return {
                    "downloads": downloads
                }
            except Exception as e:
                logger.error(f"Error fetching download history for user {user_id}: {e}")
                return {"downloads": []}

        elif action == "status":
            return {"status": "online", "version": os.getenv("BOT_VERSION", "4.0.0")}

        elif action == "download":
            book_id = data.get(
                "bookId"
            )  # Frontend sends bookId which we set as download_url
            title = data.get(
                "title", "Libro"
            )  # Optional from frontend if we update it, or we can fetch it?
            target = data.get("target", "private")
            target_id_override = data.get("targetId")
            thread_id_override = data.get("threadId")

            # If fronted doesn't send title/cover, we only have book_id (which is the url)
            if not book_id:
                raise HTTPException(status_code=400, detail="Missing bookId")

            from api.main import bot
            from config.config_settings import config
            from services.settings_service import get_setting

            # Map target to chat_id
            target_chat_id = user_id  # Default to private
            message_thread_id = None
            is_admin = user_id in config.ADMIN_USERS

            if is_admin:
                if target == "channel":
                    target_chat_id = target_id_override or get_setting("mini_app_channel_id", "@ZeePubs")
                elif target == "group":
                    target_chat_id = target_id_override or get_setting("mini_app_group_id", "@ZeePubBotTest")
                    message_thread_id = thread_id_override

            success = await enviar_libro_directo(
                bot=bot.app.bot,
                user_id=user_id,
                title=title,
                download_url=book_id,
                target_chat_id=target_chat_id,
                message_thread_id=message_thread_id,
            )
            return {"success": success}

        elif action == "bot_info":
            # Fetch bot info dynamically if possible
            from api.main import bot

            bot_user = await bot.app.bot.get_me()
            return {
                "name": bot_user.first_name or "ZeePubBot",
                "username": f"@{bot_user.username}" if bot_user.username else "@ZeePubBot",
                "description": "Asistente de EPUB del grupo. Preciso, limpio y siempre listo para ayudarte. 📚",
                "avatar": "/robot-librarian.jpg",  # Default or fetched avatar
            }

        elif action == "create_stars_invoice":
            tier = data.get("tier", "premium")
            amount = data.get("amount", 100)  # Default stars amount

            # Fetch Bot instance and plugin
            from api.main import bot
            stars_plugin = bot.plugin_manager.get_plugin("stars_payment")
            cms_plugin = bot.plugin_manager.get_plugin("custom_messages")
            if not stars_plugin:
                raise HTTPException(status_code=500, detail="Stars Payment Plugin not found")

            # Prepare invoice details using CMS strings if available
            title = f"Nivel {tier.capitalize()}"
            desc = f"Suscripción al nivel {tier.capitalize()}"
            if cms_plugin:
                desc = await cms_plugin.get_text("star_payment_invoice_desc", Nivel=tier.capitalize())

            # Generate Link
            invoice_link = await stars_plugin.create_stars_invoice_link(
                title=title,
                description=desc,
                payload=f"upgrade_{tier}",
                amount=amount
            )

            return {"invoiceLink": invoice_link}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"Error handling action {action}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# --- Nuevos Endpoints de Control de Acceso ---

@router.post("/api/user/access", response_model=AccessResponse)
async def check_user_access(
    request: AccessCheckRequest,
    user_data: Dict[str, Any] = Depends(get_current_user_data)
):
    from services.user_service import get_effective_user
    from repositories.user_repository import user_repo

    current_uid = user_data.get("user_id", 0)
    # Priorizar el ID verificado por Telegram
    uid = current_uid or request.user_id
    logger.info(f"Access check for UID: {uid}")
    # 1. Obtener información efectiva (Roles config, expiración, etc)
    eff = user_data if current_uid == uid else await get_effective_user(uid)

    # 2. Obtener información de niveles de la base de datos
    access_info = await user_repo.get_access_info(uid)

    if not access_info:
        # Si no existe en la tabla de niveles, creamos registro.
        # Si get_effective_user ya sabe que es staff/admin/premium, usamos ese nivel.
        role = eff.get("role", "free")
        # El nivel id por defecto para free es 6 (Lector)
        # IDs mapping: Admin=1, Staff=2, Premium=3, VIP=4, Patrocinador=5, Lector=6
        role_to_level = {
            'admin': 1,
            'staff': 2,
            'premium': 3,
            'vip': 4,
            'white': 5,
            'free': 6
        }
        level_id = role_to_level.get(role, 6)

        logger.info(f"User {uid} not found in user_levels. Role effective: {role}. Creating entry with Level ID {level_id}.")
        await user_repo.create_minimal_user(uid, level_id=level_id)
        access_info = await user_repo.get_access_info(uid)

    if not access_info:
        logger.error(f"Failed to retrieve access info for user {uid}")
        # Fallback de emergencia
        return AccessResponse(
            level=UserLevelModel(id="6", name="Lector", priority=1, color="#9E9E9E", hasAccess=False),
            hasAccess=eff.get("has_mini_app_access", False),
            isAdmin=(eff.get("role") == "admin")
        )

    # 3. Determinar flags finales mezclando ambos sistemas
    # El usuario tiene acceso si:
    # - Es Admin (de Config o DB)
    # - Es Staff (de Config o DB)
    # - Tiene acceso explícito por su nivel de DB
    # - Tiene acceso explícito por get_effective_user (fallbacks de config)

    is_admin = (eff.get("role") == "admin") or access_info.get("isAdmin", False)
    is_staff = (eff.get("role") == "staff")

    # Priority: Roles admin/staff TRUMP level restrictions
    has_access = (
        is_admin or
        is_staff or
        eff.get("has_mini_app_access", False) or
        access_info.get("hasAccess", False)
    )

    logger.info(f"Access response for UID {uid}: hasAccess={has_access}, isAdmin={is_admin}, role={eff.get('role')}")
    return AccessResponse(
        level=UserLevelModel(**access_info["level"]),
        hasAccess=has_access,
        isAdmin=is_admin
    )


@router.get("/api/admin/levels")
@router.get("/api/admin/access-levels")
async def get_levels(
    user_data: Dict[str, Any] = Depends(require_admin)
):

    logger.info("Fetching all access levels")
    from repositories.user_repository import user_repo
    levels = await user_repo.get_all_levels()

    logger.info(f"Found {len(levels)} access levels")
    return {"levels": [UserLevelModel(**l) for l in levels]}


@router.put("/api/admin/levels")
@router.post("/api/admin/access-levels")
async def update_levels(
    request: UpdateLevelsRequest,
    user_data: Dict[str, Any] = Depends(require_admin)
):

    from repositories.user_repository import user_repo
    for level in request.levels:
        await user_repo.update_level_access(int(level.id), level.hasAccess)

    return {
        "success": True,
        "message": "Niveles actualizados correctamente"
    }
