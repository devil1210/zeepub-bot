from fastapi import APIRouter, HTTPException, Header, Depends, Request
from utils.security import validate_telegram_data, verify_telegram_user
from services.opds_service import get_cached_feed
from services.telegram_service import enviar_libro_directo
from utils.helpers import build_search_url, abs_url
from config.config_settings import config
import os
import logging

router = APIRouter(tags=["miniapp"])
logger = logging.getLogger(__name__)


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

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    action = body.get("action")
    data = body.get("data", {})

    logger.info(f"Miniapp action: {action} User: {user_id}")

    try:
        if action == "search":
            query = data.get("query")
            page_url = data.get("pageUrl")
            
            if not query and not page_url:
                return {"results": []}

            target_url = page_url if page_url else build_search_url(query, uid=user_id)
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
                    total_pages = (int(total_results) + int(items_per_page) - 1) // int(items_per_page)
                except:
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
                        "is_folder": subsection_url is not None
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
                                if "image" in l.get("rel", "") or "cover" in l.get("rel", ""):
                                    res["cover"] = abs_url(config.BASE_URL, l.get("href", ""))
                                    break
                    except Exception:
                        pass

            # Only fetch for the first N folders to avoid massive delays if search is huge
            folder_tasks = [fetch_folder_cover(r) for r in results if r["is_folder"] and not r["cover"]]
            if folder_tasks:
                await asyncio.gather(*folder_tasks[:10]) # Limit to 10 concurrent sub-fetches

            return {
                "results": results,
                "nextPage": next_page,
                "prevPage": prev_page,
                "firstPage": first_page,
                "lastPage": last_page,
                "currentPage": current_page,
                "totalPages": total_pages
            }

        elif action == "book-detail":
            book_id_url = data.get("bookId")
            if not book_id_url:
                raise HTTPException(status_code=400, detail="Missing bookId (URL)")

            feed = await get_cached_feed(book_id_url)
            
            # OPDS entries can be at the top level or in feed.entries
            entries = getattr(feed, "entries", [])
            if not entries:
                # Some servers return the entry as the main feed element
                if getattr(feed, "feed", None) and feed.feed.get("title"):
                    entry = feed.feed
                else:
                    raise HTTPException(status_code=404, detail="Book detail not found")
            else:
                entry = entries[0]
            
            # Extract metadata (same logic as search)
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
            size = None
            file_type = None

            # Base URL for this entry's links
            entry_base_url = book_id_url

            for link in getattr(entry, "links", []):
                rel = link.get("rel", "")
                href = abs_url(entry_base_url, link.get("href", ""))
                if "acquisition" in rel or "epub" in link.get("type", ""):
                    download_url = href
                    file_type = link.get("type")
                    size = link.get("contentlength") or link.get("length")
                elif "image" in rel or "cover" in rel:
                    cover_url = href

            return {
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
                "fileType": file_type
            }

        elif action == "status":
            return {"status": "online", "version": os.getenv("BOT_VERSION", "4.0.0")}

        elif action == "download":
            book_id = data.get("bookId")  # Frontend sends bookId which we set as download_url
            title = data.get("title", "Libro") # Optional from frontend if we update it, or we can fetch it?
            
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
