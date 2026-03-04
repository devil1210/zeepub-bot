import asyncio
import logging
from typing import Any

from fastapi import HTTPException

from services.library_service import LibraryService
from services.notion_service import notion_service
from services.rating_service import RatingService

logger = logging.getLogger(__name__)


async def handle_book_detail(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve el detalle de un libro desde la base de datos local."""
    book_id_raw = data.get("bookId")
    logger.info(f"[book-detail] Request received - bookId: {book_id_raw}")

    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    # 1. Series/Group Handling
    is_series_request = False
    s_hash = None

    if isinstance(book_id_raw, str):
        if book_id_raw.startswith("series_"):
            is_series_request = True
            s_hash = book_id_raw.replace("series_", "")
        elif not book_id_raw.isdigit() and not book_id_raw.startswith("local_"):
            # Probable series_hash directo (desde URL o navegación profunda)
            is_series_request = True
            s_hash = book_id_raw

    if is_series_request and s_hash:
        v_limit = data.get("limit", 100)
        v_offset = data.get("offset", 0)

        # Optimization: Fetch metadata, total downloads and volumes in parallel
        series_task = LibraryService.get_series_metadata(s_hash)
        downloads_task = LibraryService.get_series_total_downloads(s_hash)
        volumes_task = LibraryService.get_series_volumes(s_hash, limit=v_limit, offset=v_offset)

        series, total_downloads, volumes = await asyncio.gather(series_task, downloads_task, volumes_task)

        if not series and not volumes:
            raise HTTPException(status_code=404, detail="Serie no encontrada")

        # Representative for fields not in SeriesMetadata or fallback
        rep = volumes[0] if volumes else {}

        return {
            "id": f"series_{s_hash}",
            "series_hash": s_hash,
            "title": series.series_name if series else (rep.get("series") or rep.get("title")),
            "author": series.author if series else rep.get("author"),
            "summary": series.description if series else rep.get("description"),
            "cover": series.cover_url if series else rep.get("cover"),
            "coverUrl": {
                "cover_low": series.cover_url if series else rep.get("cover_low"),
                "cover_medium": (series.cover_url if series else rep.get("cover_low")).replace(
                    "_low.jpg", "_medium.jpg"
                )
                if (series.cover_url if series else rep.get("cover_low"))
                else None,
                "cover_high": (series.cover_url if series else rep.get("cover_low")).replace("_low.jpg", "_high.jpg")
                if (series.cover_url if series else rep.get("cover_low"))
                else None,
                "cover_original": (series.cover_url if series else rep.get("cover_low")).replace(
                    "_low.jpg", "_original.jpg"
                )
                if (series.cover_url if series else rep.get("cover_low"))
                else None,
            }
            if (series and series.cover_url) or (rep and rep.get("cover_low"))
            else None,
            "rating_average": series.rating_average if series else 0,
            "rating_count": (series.rating_count if series else 0) or 0,
            "download_count": total_downloads,
            "numBooks": series.book_count if series else len(volumes),
            "is_uncensored": rep.get("is_uncensored", False) if rep else False,
            "color_mode": rep.get("color_mode") if rep else None,
            "demographics": series.demographics if series else rep.get("demographics", []),
            "tags": series.tags if series else rep.get("tags", []),
            "book_type": series.book_type if series else rep.get("book_type"),
            "is_series": True,
            "volumes": volumes,
        }

    # 2. Local Book Handling
    if str(book_id_raw).isdigit() or (
        str(book_id_raw).startswith("local_") and not str(book_id_raw).startswith("series_")
    ):
        clean_id = int(str(book_id_raw).replace("local_", ""))
        local_book = await LibraryService.get_book_by_id(clean_id)

        if local_book:
            logger.info(
                f"[book-detail] Found local book: {local_book['title']} (series_hash: {local_book.get('series_hash')})"
            )

            # If part of a series, ALWAYS include volumes to avoid "empty volumes list" in frontend
            s_hash = local_book.get("series_hash")
            if s_hash:
                v_limit = data.get("limit", 100)
                v_offset = data.get("offset", 0)
                volumes = await LibraryService.get_series_volumes(s_hash, limit=v_limit, offset=v_offset)
                local_book["volumes"] = volumes
                local_book["series_hash"] = s_hash
            else:
                local_book["volumes"] = [local_book]

            # Crucial: if it was explicitly a book_id (starts with local_ or digit), it's NOT a series view
            local_book["is_series"] = False

            return local_book

    # OPDS fallback removed
    raise HTTPException(status_code=404, detail="Book not found in local library")


async def handle_rate_book(data: dict[str, Any], user_data: dict[str, Any]):
    """Permite al usuario calificar un libro."""
    user_id = user_data.get("user_id")
    book_id_raw = data.get("bookId")
    rating = data.get("rating")

    if not book_id_raw or rating is None:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId o rating")

    try:
        book_id = int(str(book_id_raw).replace("local_", ""))
    except ValueError as e:
        raise HTTPException(status_code=400, detail="ID de libro inválido para votación") from e

    return await RatingService.rate_book(user_id, book_id, rating)


async def handle_remove_rating(data: dict[str, Any], user_data: dict[str, Any]):
    """Elimina la calificación previa del usuario sobre un libro."""
    user_id = user_data.get("user_id")
    book_id_raw = data.get("bookId")
    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    try:
        book_id = int(str(book_id_raw).replace("local_", ""))
    except ValueError as e:
        raise HTTPException(status_code=400, detail="ID de libro inválido") from e

    return await RatingService.remove_rating(user_id, book_id)


async def handle_rating_breakdown(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve el desglose de calificaciones para un libro."""
    book_id_raw = data.get("bookId")
    if not book_id_raw:
        raise HTTPException(status_code=400, detail="Faltan parámetros bookId")

    try:
        book_id = int(str(book_id_raw).replace("local_", ""))
    except ValueError as e:
        raise HTTPException(status_code=400, detail="ID de libro inválido") from e

    return {"breakdown": await RatingService.get_rating_breakdown(book_id)}


async def handle_request_book(data: dict[str, Any], user_data: dict[str, Any]):
    """Permite al usuario solicitar un libro no disponible."""
    user_id = user_data.get("user_id")
    book_name = data.get("title")
    author = data.get("author", "")
    notes = data.get("notes", "")

    if not book_name:
        raise HTTPException(status_code=400, detail="Falta el título del libro")

    # Log to Notion
    username = user_data.get("nickname") or user_data.get("name") or f"User_{user_id}"
    asyncio.create_task(notion_service.log_book_request(username, book_name, author, notes))

    return {"success": True, "message": "Solicitud enviada a los bibliotecarios"}
