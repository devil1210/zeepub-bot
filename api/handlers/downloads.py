import asyncio
import logging
from typing import Any

from fastapi import HTTPException

from repositories.download_repository import download_repo
from services.library_service import LibraryService
from services.notion_service import notion_service
from services.settings_service import get_setting

logger = logging.getLogger(__name__)


async def handle_user_downloads_history(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve el historial reciente de descargas del usuario."""
    user_id = user_data.get("user_id")
    if user_id is None:
        return {"downloads": []}
    try:
        downloads = await download_repo.get_user_downloads(int(user_id), limit=20)
        return {"downloads": downloads}
    except Exception as e:
        logger.error(f"Error fetching download history for user {user_id}: {e}")
        return {"downloads": []}


async def handle_download(data: dict[str, Any], user_data: dict[str, Any]):
    """Envía el archivo del libro directamente a través del bot."""
    from services.delivery.delivery_service import delivery_service
    from services.identity.identity_service import identity_service
    from services.metadata_orchestrator.metadata_service import metadata_orchestrator
    from utils.download_limiter import can_download

    user_id = user_data.get("user_id")
    book_id = data.get("bookId")
    title = data.get("title", "Libro")
    target = data.get("target", "private")
    target_id_override = data.get("targetId")
    thread_id_override = data.get("threadId")

    if not book_id:
        raise HTTPException(status_code=400, detail="Missing bookId")

    # 0. Quota Check (Synchronize with bot)
    if not await can_download(user_id):
        raise HTTPException(status_code=403, detail="Has alcanzado tu límite de descargas por hoy.")

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
        if not str(book_id).startswith("http"):
            logger.warning(f"Book not found in library and not a URL: {book_id}")

    # 3. Deliver Book
    success = await delivery_service.deliver(
        platform="telegram",
        target_id=user_id,
        book_data=book_metadata,
        options={
            "target_chat_id": target_chat_id,
            "message_thread_id": message_thread_id,
            "title_override": title,
        },
    )

    # 4. Log to Notion if successful
    if success:
        # We fire and forget or at least don't block the response
        asyncio.create_task(
            notion_service.log_download(
                user_name=user_data.get("nickname") or user_data.get("name") or f"User_{user_id}",
                book_title=book_metadata.get("title", title),
                series_name=book_metadata.get("series", "Single"),
                volume=str(book_metadata.get("volume", "1")),
                author=book_metadata.get("author", "Desconocido"),
            )
        )

    return {"success": success}


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
        # No OPDS fallback
        pass

    if not title_for_query and not book_hash_for_query:
        return {"count": 0}

    from repositories.metrics_repository import metrics_repo

    count = await metrics_repo.get_total_downloads(book_hash_for_query) if book_hash_for_query else 0
    return {"count": count}
