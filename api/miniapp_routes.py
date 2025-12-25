import json
import logging
import os

import hashlib
import hmac
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from typing import List
from functools import wraps

from config.config_settings import config
from services.user_service import get_effective_user
from utils.security import validate_telegram_data, verify_telegram_user
from services.opds_service import get_cached_feed
from services.telegram_service import enviar_libro_directo
from utils.helpers import build_search_url, abs_url

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

# --- Dependencias y Decoradores ---


async def verify_admin(
    x_telegram_init_data: str = Header(None, alias="x-telegram-init-data")
) -> bool:
    """
    Verifica si el usuario es administrador (desde config o tabla admins).
    """
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not x_telegram_init_data or not bot_token:
        # Fallback para desarrollo si se requiere
        if os.getenv("DEV_MODE") == "true":
            return True
        return False

    user_data = validate_telegram_data(x_telegram_init_data, bot_token)
    if not user_data:
        return False

    user_id = user_data.get("user", {}).get("id")
    if not user_id:
        return False

    # Check config
    if user_id in config.ADMIN_USERS:
        return True

    # Check DB
    from services.user_service import user_repo
    return await user_repo.is_admin(user_id)


def require_mini_app_access(func):
    """
    Decorador para requerir acceso a Mini App.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Intentar obtener user_id de los argumentos o el request meta
        request = kwargs.get('request')
        user_id = None

        if hasattr(request, "state") and hasattr(request.state, "user_id"):
            user_id = request.state.user_id

        if not user_id:
            # Si no está en el state, buscar en el body del request si es posible
            # pero esto es específico para cada ruta.
            # Por simplicidad en este bot, asumimos que se inyecta o se valida antes.
            pass

        if user_id:
            from services.user_service import user_repo
            access_info = await user_repo.get_access_info(user_id)
            if access_info and not access_info.get("hasAccess") and not access_info.get("isAdmin"):
                raise HTTPException(
                    status_code=403,
                    detail="Tu nivel de usuario no tiene acceso a la Mini App"
                )

        return await func(*args, **kwargs)

    return wrapper


@router.post("/api/bot")
async def handle_bot_request(
    request: Request,
    x_telegram_init_data: str = Header(None, alias="x-telegram-init-data"),
):
    """
    Main endpoint for Mini App requests.
    Dispatches actions: search, download, status, etc.
    """
    bot_token = os.getenv("TELEGRAM_TOKEN")
    user_data = None

    if x_telegram_init_data and bot_token:
        user_data = validate_telegram_data(x_telegram_init_data, bot_token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid Telegram data")
    else:
        # For development or if header is missing, we might want to fail or allow.
        # Strict mode:
        if not os.getenv("DEV_MODE"):
            raise HTTPException(status_code=401, detail="Missing auth header")

    user_id = user_data.get("user", {}).get("id") if user_data else 0
    # Fetch effective role for permissions
    user_effective = await get_effective_user(user_id)
    user_role = user_effective.get("role", "free")

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
                author = entry.get("author", "Desconocido")
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
                    if rel == "subsection":
                        subsection_url = href
                    elif rel == "self" or rel == "alternate":
                        if not detail_url or rel == "self":
                            detail_url = href
                    elif "acquisition" in rel or "epub" in link.get("type", ""):
                        download_url = href
                        file_type = link.get("type")
                        # Try to get size from link attributes if available
                        size = link.get("contentlength") or link.get("length")
                    elif "image" in rel or "cover" in rel:
                        cover_url = href

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

            if not book_id_url:
                logger.error("[book-detail] Missing bookId parameter")
                raise HTTPException(status_code=400, detail="Missing bookId (URL)")

            # Ensure we have a valid URL (sometimes frontend might pass raw ID)
            if not book_id_url.startswith("http"):
                logger.warning(
                    f"[book-detail] bookId {book_id_url} is not a URL. Attempting to build one."
                )
                # Fallback: if it's just an id, we might need a search or a direct link
                # but for simplicity, let's assume it MUST be a URL for now as per search logic.
                pass

            logger.info(f"[book-detail] Fetching feed from: {book_id_url}")
            feed = await get_cached_feed(book_id_url)

            if not feed:
                logger.error(f"[book-detail] Failed to fetch feed from {book_id_url}")
                raise HTTPException(status_code=404, detail="Could not fetch book feed")

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

            # Fallback for cover if not found in links but exists in content
            if not cover_url and "content" in entry:
                for content in entry.get("content", []):
                    if "image" in content.get("type", ""):
                        cover_url = abs_url(entry_base_url, content.get("value", ""))
                        break

            result = {
                "id": entry.get("id", ""),
                "title": entry.get("title", "Sin título"),
                "author": entry.get("author", "Desconocido"),
                "summary": entry.get("summary", ""),
                "cover": cover_url,
                "downloadUrl": download_url,
                "publisher": publisher,
                "language": language,
                "isbn": isbn,
                "year": year,
                "size": size,
                "fileType": file_type,
            }

            logger.info(
                f"[book-detail] Returning result: {result['title']} (Cover: {result['cover']}, DL: {result['downloadUrl']})"
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

            # If fronted doesn't send title/cover, we only have book_id (which is the url)
            if not book_id:
                raise HTTPException(status_code=400, detail="Missing bookId")

            from api.main import bot

            success = await enviar_libro_directo(
                bot=bot.app.bot,
                user_id=user_id,
                title=title,
                download_url=book_id,
                # cover_url=... we don't have it easily here unless we pass it from frontend
            )
            return {"success": success}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"Error handling action {action}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# --- Nuevos Endpoints de Control de Acceso ---

@router.post("/api/user/access", response_model=AccessResponse)
async def check_user_access(
    request: AccessCheckRequest,
    user_data: dict = Depends(verify_telegram_user)
):
    from services.user_service import get_effective_user, user_repo

    # Priorizar el ID verificado por Telegram
    uid = user_data.get("id") or request.user_id
    logger.info(f"Access check for UID: {uid}")
    # 1. Obtener información efectiva (Roles config, expiración, etc)
    eff = await get_effective_user(uid)

    # 2. Obtener información de niveles de la base de datos
    access_info = await user_repo.get_access_info(uid)

    if not access_info:
        # Si no existe en la tabla de niveles, creamos registro con nivel básico
        logger.info(f"User {uid} not found in user_levels, creating minimal entry.")
        await user_repo.create_minimal_user(uid, level_id=6)  # Lector
        access_info = await user_repo.get_access_info(uid)

    if not access_info:
        logger.error(f"Failed to retrieve access info for user {uid}")
        raise HTTPException(status_code=500, detail="Error al recuperar nivel de usuario")

    # 3. Determinar flags finales mezclando ambos sistemas
    # El usuario tiene acceso si su nivel de DB lo permite O si su rol efectivo tiene el flag activo
    is_admin = (eff.get("role") == "admin") or access_info.get("isAdmin", False)
    has_access = eff.get("has_mini_app_access", False) or access_info.get("hasAccess", False) or is_admin

    logger.info(f"Access response for UID {uid}: hasAccess={has_access}, isAdmin={is_admin}")
    return AccessResponse(
        level=UserLevelModel(**access_info["level"]),
        hasAccess=has_access,
        isAdmin=is_admin
    )


@router.get("/api/admin/levels")
@router.get("/api/admin/access-levels")
async def get_levels(
    is_admin: bool = Depends(verify_admin)
):
    if not is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info("Fetching all access levels")
    from services.user_service import user_repo
    levels = await user_repo.get_all_levels()

    logger.info(f"Found {len(levels)} access levels")
    return {"levels": [UserLevelModel(**l) for l in levels]}


@router.put("/api/admin/levels")
@router.post("/api/admin/access-levels")
async def update_levels(
    request: UpdateLevelsRequest,
    is_admin: bool = Depends(verify_admin)
):
    if not is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    from services.user_service import user_repo
    for level in request.levels:
        await user_repo.update_level_access(int(level.id), level.hasAccess)

    return {
        "success": True,
        "message": "Niveles actualizados correctamente"
    }
