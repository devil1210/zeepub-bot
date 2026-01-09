import json
import logging
import os

import hashlib
import hmac
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from functools import wraps

from api.deps import (
    get_telegram_user_id,
    get_current_user_data,
    require_admin,
    require_mini_app_access,
)
from config.config_settings import config
from services.user_service import get_effective_user
from utils.security import validate_telegram_data, verify_telegram_user
from services.opds_service import get_cached_feed
from services.telegram_service import enviar_libro_directo
from services.settings_service import get_setting, set_setting
from utils.helpers import (
    build_search_url,
    abs_url,
    extract_author,
    extract_creators_by_role,
    parse_metadata_from_title,
)

router = APIRouter(tags=["miniapp"])
logger = logging.getLogger(__name__)


# --- Modelos Pydantic ---


class AccessCheckRequest(BaseModel):
    user_id: int
    force: bool = False


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
            status_code=403, detail="Tu nivel de usuario no tiene acceso a la Mini App"
        )

    logger.info(f"Miniapp action: {action} User: {user_id} Role: {user_role}")

    try:
        if action == "search":
            query = data.get("query")
            page_url = data.get("pageUrl")
            page = data.get("page", 1)

            if not query and not page_url:
                return {"results": []}

            # [NEW] Prioritize Local DB Search for ZeePub library
            is_local_search = not page_url or (
                page_url == config.OPDS_ROOT_START or 
                page_url == config.OPDS_ROOT_EVIL or 
                page_url == "root" or
                "/api/library/catalog" in page_url
            )

            if is_local_search and query:
                logger.info(f"[search] Using NATIVE SQL search for query: {query}")
                from utils.library_db import get_session
                from sqlalchemy import text
                import re

                session = get_session()
                try:
                    clean_q = re.sub(r"[^\w\s]", " ", query).strip()
                    if not clean_q:
                        books = session.query(LocalBook).filter(LocalBook.title.ilike(f"%{query}%")).limit(100).all()
                    else:
                        match_expr = "books_fts MATCH :q"
                        sql = text(f"SELECT rowid FROM books_fts WHERE {match_expr} ORDER BY rank")
                        params = {"q": f"{clean_q}*"}
                        matching_ids = session.execute(sql, params).scalars().all()
                        books = session.query(LocalBook).filter(LocalBook.id.in_(matching_ids)).all()
                        id_to_book = {b.id: b for b in books}
                        books = [id_to_book[id] for id in matching_ids if id in id_to_book]

                    items_per_page = 10
                    start = (page - 1) * items_per_page
                    end = start + items_per_page
                    paginated = books[start:end]

                    results = []
                    for b in paginated:
                        d = b.to_dict()
                        d["is_folder"] = False
                        results.append(d)
                    
                    return {
                        "results": results,
                        "currentPage": page,
                        "totalPages": (len(books) + items_per_page - 1) // items_per_page,
                        "totalItems": len(books)
                    }
                except Exception as e:
                    logger.error(f"[search] Native search failed: {e}")
                finally:
                    session.close()

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
                is_folder = any(
                    link.get("rel") == "subsection"
                    for link in getattr(entry, "links", [])
                )
                author = extract_author(entry, is_folder=is_folder)

                summary = entry.get("summary", "")
                # Clean summary: remove "Format: Epub Summary:" prefix that Kavita adds
                if summary:
                    # Remove common Kavita prefixes
                    summary = summary.replace("Format: Epub Summary: ", "")
                    summary = summary.replace("Format: Epub ", "")
                    summary = summary.replace("Summary: ", "")
                    summary = summary.strip()

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

                # Categories/Genres
                raw_tags = getattr(entry, "tags", [])
                categories = [
                    tag.get("label") or tag.get("term")
                    for tag in raw_tags
                    if tag.get("label") or tag.get("term")
                ]
                # logger.info(f"[DEBUG CATS] Title: {title} | Extracted: {categories} | Raw: {raw_tags}")

                # Parse metadata from title for better display
                title_meta = parse_metadata_from_title(title)

                # Series/Volume extraction from entry metadata
                entry_series = entry.get("calibre_series") or entry.get("schema_series")
                entry_series_index = entry.get("calibre_series_index")

                # Fallback to title parsing if metadata is missing
                final_series = entry_series or title_meta.get("series", "")
                final_series_index = entry_series_index or title_meta.get("volume", "")

                # Extra technical and role metadata
                illustrator = extract_creators_by_role(entry, "ill")
                translator = extract_creators_by_role(entry, "trl")
                word_count = entry.get("kavita_wordcount") or entry.get("calibre_wordcount")
                page_count = entry.get("kavita_pagecount") or entry.get("calibre_pagecount")
                reading_time = entry.get("kavita_readingtime") or entry.get("calibre_readingtime")

                results.append(
                    {
                        "id": book_id,
                        "title": title,
                        "author": author,
                        "illustrator": illustrator,
                        "translator": translator,
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
                        "updatedDate": entry.get("updated")
                        or entry.get("published")
                        or "",
                        # Enhanced metadata for better UI display
                        "series": final_series,
                        "seriesIndex": final_series_index,
                        "tags": title_meta.get("tags", []),
                        "cleanTitle": title_meta.get("clean_title", title),
                        "romaji": title_meta.get("romaji", ""),
                        "categories": categories,
                        "wordCount": word_count,
                        "pageCount": page_count,
                        "readingTime": reading_time,
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
            book_id_raw = data.get("bookId")
            logger.info(f"[book-detail] Request received - bookId: {book_id_raw}")

            if not book_id_raw:
                raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

            # 1. Check if it's a LOCAL book (id or local_ prefix)
            local_book = None
            if isinstance(book_id_raw, str) and (book_id_raw.startswith("local_") or book_id_raw.isdigit()):
                from utils.library_db import get_session
                session = get_session()
                try:
                    clean_id = book_id_raw.replace("local_", "")
                    local_book = session.query(LocalBook).filter(LocalBook.id == int(clean_id)).first()
                    if local_book:
                        logger.info(f"[book-detail] Found local book in DB: {local_book.title}")
                        result = local_book.to_dict()
                        result["is_downloaded"] = await download_repo.has_user_downloaded(user_id, local_book.title)
                        return result
                except Exception as e:
                    logger.warning(f"[book-detail] Local DB lookup failed for {book_id_raw}: {e}")
                finally:
                    session.close()

            # 2. Traditional OPDS Flow (for remote or unmapped books)
            book_id_url = book_id_raw
            # Initialize for extraction fallback
            subsection_url = None

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
                raise HTTPException(
                    status_code=400, detail=f"Invalid book URL: {book_id_url}"
                )

            if not feed:
                logger.error(f"[book-detail] No feed data returned from {book_id_url}")
                # Use a more descriptive error if we can detect it's a 500
                # Since get_cached_feed hides the status, we assume if it's None and it was a valid-looking URL,
                # it's likely a server error from source.
                raise HTTPException(
                    status_code=502,
                    detail="Error en el servidor de origen (OPDS). Intenta más tarde.",
                )

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
            categories = [
                cat.get("term") for cat in entry.get("tags", []) if cat.get("term")
            ]

            # Enriched Roles
            illustrator = extract_creators_by_role(entry, "ill")
            translator = extract_creators_by_role(entry, "trl")
            layout_by = extract_creators_by_role(entry, "bkp")
            
            # ASIN Extraction
            asin = None
            for ident in entry.get("identifiers", []):
                if isinstance(ident, dict) and ident.get("scheme", "").upper() == "ASIN":
                    asin = ident.get("value")
                    break
            if not asin and identifier and "asin" in identifier.lower():
                asin = identifier.split(":")[-1].strip()
            
            # Tech metrics
            epub_version = entry.get("dc_version") or entry.get("kavita_format_version")
            word_count = entry.get("kavita_wordcount") or entry.get("calibre_wordcount")
            page_count = entry.get("kavita_pagecount") or entry.get("calibre_pagecount")
            reading_time = entry.get("kavita_readingtime") or entry.get("calibre_readingtime")

            # [NEW] Smart Tags & Series Extraction Fallback
            extracted_meta = parse_metadata_from_title(entry.get("title", ""))

            # Capture tags from title (e.g. [Tag])
            title_tags = extracted_meta.get("tags", [])
            # Add to categories or a separate field?
            # The user asked to "save them" to replace properly later.
            # We'll prepend them to categories for now to make them visible,
            # or could add a 'publisher_groups' field if the frontend supported it.
            # Let's add them to categories with a prefix or just raw for now.
            for ttag in title_tags:
                if ttag not in categories:
                    categories.append(ttag)

            # Fallback for Series/Volume if not provided by server
            if not series and extracted_meta.get("series"):
                series = extracted_meta["series"]

            if not series_index and extracted_meta.get("volume"):
                series_index = extracted_meta["volume"]

            download_url = None
            cover_url = None
            size = None
            file_type = None
            subsection_url = None

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

            # Enhanced metadata
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
                "upUrl": subsection_url,
                "updatedDate": entry.get("updated", "") or entry.get("published", ""),
                # Enriched metadata
                "illustrator": illustrator,
                "translator": translator,
                "layoutBy": layout_by,
                "epubVersion": epub_version,
                "wordCount": word_count,
                "pageCount": page_count,
                "readingTime": reading_time,
                "romaji": extracted_meta.get("romaji", ""),
                "cleanTitle": extracted_meta.get("clean_title")
                or entry.get("title", ""),
                "tags": extracted_meta.get("tags", []),
                "is_downloaded": await download_repo.has_user_downloaded(user_id, entry.get("title", ""))
            }

            logger.info(
                f"[book-detail] Title: {result['title']}\n"
                f"  -> Romaji: {result['romaji']}\n"
                f"  -> CleanTitle: {result['cleanTitle']}\n"
                f"  -> Author: {result['author']}\n"
                f"  -> Vol: {result['seriesIndex']}\n"
                f"  -> Tags: {result['tags']}"
            )

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
                "isBanned": role_key == "banned",
            }

            logger.info(
                f"[user_status] User {user_id} - Role: {role_key}, Level: {system_role_text}, Used: {used}, Limit: {max_dl}, "
                f"Reset: {hours}h {minutes}m, user_effective_role: {user_effective.get('role')}, status_label: {user_effective.get('status_label')}"
            )

            return result

        elif action == "user_downloads_history":
            # Return user's recent download history
            try:
                from repositories.download_repository import download_repo

                downloads = await download_repo.get_user_downloads(user_id, limit=20)

                # Map to frontend expected format
                formatted = []
                for d in downloads:
                    formatted.append(
                        {
                            "id": d["id"],
                            "title": d["title"],
                            "author": d["author"],
                            "downloaded_at": d["downloaded_at"],
                            "file_size": d["file_size"],
                            "romaji_title": d.get("romaji_title"),
                            "series": d.get("series"),
                            "volume": d.get("volume"),
                            "translator": d.get("translator"),
                            "clean_title": d.get("clean_title"),
                        }
                    )

                logger.info(
                    f"[user_downloads_history] User {user_id} - Retrieved {len(formatted)} downloads"
                )
                return {"downloads": formatted}
            except Exception as e:
                logger.error(f"Error fetching download history for user {user_id}: {e}")
                return {"downloads": []}

        elif action == "recommendations":
            from services.recommendation_service import RecommendationService
            
            # Security: Only for admin/staff to see the button, but we allow users to see their own recs if they know the action?
            # Actually, per user request, the feature is in Beta for Staff.
            if user_role not in ("admin", "staff"):
                 raise HTTPException(status_code=403, detail="Beta exclusiva para Staff")
            
            limit = data.get("limit", 10)
            recs = await RecommendationService.get_recommendations(user_id, limit=limit)
            
            # Formatear para el feed de la Mini App
            results = []
            for r in recs:
                results.append({
                    "id": f"local_{r.id}",
                    "title": r.title,
                    "author": r.author,
                    "cover": f"/api/library/covers/{r.id}" if r.cover_path else None,
                    "downloadUrl": f"local_{r.id}",
                    "is_folder": False,
                    "series": r.series,
                    "seriesIndex": r.series_index,
                    "cleanTitle": r.title,
                    "rating_average": r.rating_average or 0
                })
            return {"results": results}

        elif action == "rate_book":
            from services.rating_service import RatingService
            
            book_id_raw = data.get("bookId")
            rating = data.get("rating")
            
            if not book_id_raw or rating is None:
                raise HTTPException(status_code=400, detail="Faltan parámetros bookId o rating")
            
            # Handle local_ prefix
            try:
                if isinstance(book_id_raw, str) and book_id_raw.startswith("local_"):
                    book_id = int(book_id_raw.replace("local_", ""))
                else:
                    book_id = int(book_id_raw)
            except ValueError:
                raise HTTPException(status_code=400, detail="ID de libro inválido para votación")
                
            res = RatingService.rate_book(user_id, book_id, rating)
            return res

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

            # Map target to chat_id
            target_chat_id = user_id  # Default to private
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
            avatar_url = "/robot-librarian.jpg"

            try:
                photos = await bot.app.bot.get_user_profile_photos(bot_user.id, limit=1)
                if photos.photos:
                    # photos.photos[0] is the list of sizes for the first photo
                    # The last one [-1] is usually the largest
                    file_id = photos.photos[0][-1].file_id
                    avatar_url = f"/api/bot/avatar?file_id={file_id}"
                    logger.info(f"Bot avatar file_id: {file_id}")
            except Exception as e:
                logger.error(f"Could not fetch bot profile photo: {e}")

            res = {
                "name": bot_user.first_name or "ZeePubBot",
                "username": (
                    f"@{bot_user.username}" if bot_user.username else "@ZeePubBot"
                ),
                "description": "Asistente de EPUB del grupo. Preciso, limpio y siempre listo para ayudarte. 📚",
                "avatar": avatar_url,
                "ui_defaults": json.loads(get_setting("ui_defaults_global", "{}")),
            }
            logger.info(f"bot_info result for user {user_id}: {res}")
            return res

        elif action == "ui_settings":
            # Manage global/role-based/personal UI configurations

            sub_action = data.get("subAction", "get")

            # Helper to get user repo
            from repositories.user_repository import user_repo

            if sub_action == "get":
                target_role = data.get("role", "global")

                # If 'auto', determine if we should load personal or role-based defaults
                # Logic: Always load Global -> Role defaults -> User Personal Overrides
                if target_role == "auto":
                    target_role = user_role  # Effective role

                logger.info(
                    f"Fetching UI settings chain for user {user_id} (Role: {target_role})"
                )

                # 1. Load GLOBAL settings (Base)
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
                }

                try:
                    global_raw = get_setting("ui_defaults_global", "{}")
                    final_settings.update(json.loads(global_raw))
                except Exception:
                    pass

                # 2. Load ROLE settings (Mid Layer)
                role_version = 0
                if target_role and target_role != "global":
                    try:
                        role_raw = get_setting(f"ui_defaults_{target_role}", "{}")
                        role_settings = json.loads(role_raw)

                        # Extract version for notification logic
                        role_version = role_settings.get("ui_version", 0)

                        logger.info(
                            f"Merging {target_role} defaults (v{role_version}): {role_settings}"
                        )
                        final_settings.update(role_settings)
                    except Exception as e:
                        logger.error(f"Error merging role settings: {e}")

                # 3. Load USER settings (Top Layer) - Only if looking for "auto"/personal context
                # If specifically requesting "staff" defaults, we don't merge user settings
                update_notification = False

                if data.get("role") == "auto":
                    user_record = await user_repo.get_by_id(user_id)
                    if user_record and user_record.get("settings"):
                        user_settings = user_record.get("settings", {})
                        last_seen_version = user_settings.get("last_seen_version", 0)

                        # VERSION CHECK: If Admin pushed a new version, notify user
                        # But still merge their settings (user choice prevails, but they get notified)
                        if role_version > last_seen_version:
                            update_notification = True
                            final_settings["update_notification"] = True
                            logger.info(
                                f"User {user_id} has old version ({last_seen_version} < {role_version}). Sending update notification."
                            )

                        logger.info(f"Merging USER personal settings: {user_settings}")
                        final_settings.update(user_settings)

                return final_settings

            elif sub_action == "set":
                logger.info(
                    f"UI Settings SET request - user_id: {user_id}, role: {data.get('role')}"
                )

                target_role = data.get("role", "global")
                settings_obj = data.get("settings", {})

                if target_role == "personal":
                    # USER SAVING PERSONAL SETTINGS
                    # 1. Get current role version to ack checks
                    current_role = user_role
                    role_raw = get_setting(f"ui_defaults_{current_role}", "{}")
                    try:
                        role_data = json.loads(role_raw)
                        settings_obj["last_seen_version"] = role_data.get(
                            "ui_version", 0
                        )
                    except Exception:
                        settings_obj["last_seen_version"] = 0

                    # 2. Save to DB users table
                    await user_repo.update_user_settings(user_id, settings_obj)
                    logger.info(f"Saved PERSONAL settings for user {user_id}")
                    return {
                        "success": True,
                        "message": "Configuración personal guardada",
                    }

                else:
                    # ADMIN SAVING ROLE DEFAULTS
                    if user_role != "admin":
                        logger.warning(
                            f"User {user_id} tried to set UI settings for {target_role} - DENIED"
                        )
                        raise HTTPException(
                            status_code=403,
                            detail="Solo administradores pueden cambiar la configuración global",
                        )

                    # Increment Version to force notifications
                    import time

                    settings_obj["ui_version"] = int(time.time())

                    logger.info(
                        f"Saving UI settings for role '{target_role}' (v{settings_obj['ui_version']}): {settings_obj}"
                    )
                    set_setting(f"ui_defaults_{target_role}", json.dumps(settings_obj))

                    # Force Overwrite: Reset all users of this level/role
                    if data.get("forceOverwrite"):
                        role_to_level = {
                            "admin": 1,
                            "staff": 2,
                            "premium": 3,
                            "vip": 4,
                            "white": 5,
                            "free": 6,
                        }
                        level_id = role_to_level.get(target_role)
                        if level_id:
                            await user_repo.reset_level_users_settings(level_id)
                            logger.info(
                                f"Force Overwrite: Reset settings for level {level_id} (role {target_role})"
                            )
                        elif target_role == "global":
                            # If global overwrite is requested, technically we should do nothing or all?
                            # For safety, let's only log valid levels.
                            # If user wants to reset ALL users, that's a bigger nuke.
                            pass

                    return {
                        "success": True,
                        "message": f"Configuración para {target_role} guardada (v{settings_obj['ui_version']})",
                    }

        elif action == "create_stars_invoice":
            tier = data.get("tier", "premium")
            amount = data.get("amount", 100)  # Default stars amount

            # Fetch Bot instance and plugin
            from api.main import bot

            stars_plugin = bot.plugin_manager.get_plugin("stars_payment")
            cms_plugin = bot.plugin_manager.get_plugin("custom_messages")
            if not stars_plugin:
                raise HTTPException(
                    status_code=500, detail="Stars Payment Plugin not found"
                )

            # Prepare invoice details using CMS strings if available
            title = f"Nivel {tier.capitalize()}"
            desc = f"Suscripción al nivel {tier.capitalize()}"
            if cms_plugin:
                desc = await cms_plugin.get_text(
                    "star_payment_invoice_desc", Nivel=tier.capitalize()
                )

            # Generate Link
            invoice_link = await stars_plugin.create_stars_invoice_link(
                title=title, description=desc, payload=f"upgrade_{tier}", amount=amount
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
    user_data: Dict[str, Any] = Depends(get_current_user_data),
):
    from services.user_service import get_effective_user
    from repositories.user_repository import user_repo

    current_uid = user_data.get("user_id", 0)
    # Priorizar el ID verificado por Telegram
    uid = current_uid or request.user_id
    logger.info(f"Access check for UID: {uid} (Force: {request.force})")

    # 1. Obtener información efectiva (Roles config, expiración, etc)
    # Si force=True, ignoramos el caché del backend
    use_cache = not request.force
    eff = await get_effective_user(uid, use_cache=use_cache)

    # 2. Obtener información de niveles de la base de datos
    access_info = await user_repo.get_access_info(uid)

    if not access_info:
        # Si no existe en la tabla de niveles, creamos registro.
        # Si get_effective_user ya sabe que es staff/admin/premium, usamos ese nivel.
        role = eff.get("role", "free")
        # El nivel id por defecto para free es 6 (Lector)
        # IDs mapping: Admin=1, Staff=2, Premium=3, VIP=4, Patrocinador=5, Lector=6
        role_to_level = {
            "admin": 1,
            "staff": 2,
            "premium": 3,
            "vip": 4,
            "white": 5,
            "free": 6,
        }
        level_id = role_to_level.get(role, 6)

        logger.info(
            f"User {uid} not found in user_levels. Role effective: {role}. Creating entry with Level ID {level_id}."
        )
        await user_repo.create_minimal_user(uid, level_id=level_id)
        access_info = await user_repo.get_access_info(uid)

    if not access_info:
        logger.error(f"Failed to retrieve access info for user {uid}")
        # Fallback de emergencia
        return AccessResponse(
            level=UserLevelModel(
                id="6", name="Lector", priority=1, color="#9E9E9E", hasAccess=False
            ),
            hasAccess=eff.get("has_mini_app_access", False),
            isAdmin=(eff.get("role") == "admin"),
        )

    # 3. Determinar flags finales mezclando ambos sistemas
    # El usuario tiene acceso si:
    # - Es Admin (de Config o DB)
    # - Es Staff (de Config o DB)
    # - Tiene acceso explícito por su nivel de DB
    # - Tiene acceso explícito por get_effective_user (fallbacks de config)

    is_admin = (eff.get("role") == "admin") or access_info.get("isAdmin", False)
    is_staff = eff.get("role") == "staff"

    # Priority: Roles admin/staff TRUMP level restrictions
    has_access = (
        is_admin
        or is_staff
        or eff.get("has_mini_app_access", False)
        or access_info.get("hasAccess", False)
    )

    logger.info(
        f"Access response for UID {uid}: hasAccess={has_access}, isAdmin={is_admin}, role={eff.get('role')}"
    )
    return AccessResponse(
        level=UserLevelModel(**access_info["level"]),
        hasAccess=has_access,
        isAdmin=is_admin,
    )


@router.get("/api/admin/levels")
@router.get("/api/admin/access-levels")
async def get_levels(user_data: Dict[str, Any] = Depends(require_admin)):

    logger.info("Fetching all access levels")
    from repositories.user_repository import user_repo

    levels = await user_repo.get_all_levels()

    logger.info(f"Found {len(levels)} access levels")
    return {"levels": [UserLevelModel(**l) for l in levels]}


@router.put("/api/admin/levels")
@router.post("/api/admin/access-levels")
async def update_levels(
    request: UpdateLevelsRequest, user_data: Dict[str, Any] = Depends(require_admin)
):

    from repositories.user_repository import user_repo

    for level in request.levels:
        await user_repo.update_level_access(int(level.id), level.hasAccess)

    return {"success": True, "message": "Niveles actualizados correctamente"}
