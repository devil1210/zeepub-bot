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
            if not query:
                return {"results": []}

            search_url = build_search_url(query, uid=user_id)
            feed = await get_cached_feed(search_url)

            results = []
            entries = getattr(feed, "entries", [])
            
            # First pass: collect all data
            for entry in entries:
                book_id = entry.get("id", "")
                title = entry.get("title", "Sin título")
                author = entry.get("author", "Desconocido")
                summary = entry.get("summary", "")

                download_url = None
                cover_url = None
                subsection_url = None

                for link in getattr(entry, "links", []):
                    rel = link.get("rel", "")
                    href = abs_url(config.BASE_URL, link.get("href", ""))
                    if rel == "subsection":
                        subsection_url = href
                    elif "acquisition" in rel or "epub" in link.get("type", ""):
                        download_url = href
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

            return {"results": results}

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
