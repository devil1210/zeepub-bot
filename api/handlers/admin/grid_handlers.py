import logging
import re
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from core.db_manager_pg import pg_manager
from models.library import Book, Series
from services.cache_service import cache_manager
from utils.metadata_utils import generar_slug_from_meta

logger = logging.getLogger(__name__)


def _sanitize_slug(slug_str: str | None) -> str | None:
    if not slug_str:
        return None
    cleaned = slug_str.strip()
    if not cleaned:
        return None
    # Ensure it starts with #
    if not cleaned.startswith("#"):
        cleaned = f"#{cleaned}"
    # Replace spaces with underscores and remove disallowed chars
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"[^#a-zA-Z0-9_]", "", cleaned)
    return cleaned


async def handle_admin_get_library_grid(data: dict[str, Any], user_data: dict[str, Any]) -> dict[str, Any]:
    """
    Retorna la lista jerárquica de Series con sus Volúmenes/EPUBs asociados
    con soporte para búsqueda, filtros de consistencia y paginación rápida.
    """
    query_str = (data.get("query") or "").strip()
    missing_filter = (data.get("missing_filter") or "all").strip().lower()
    demography_filter = (data.get("demography") or "").strip()
    book_type_filter = (data.get("book_type") or "").strip()
    page = max(1, int(data.get("page") or 1))
    limit = min(100, max(5, int(data.get("limit") or 25)))
    offset = (page - 1) * limit

    async with pg_manager.get_session() as session:
        # Base query para series
        base_stmt = select(Series)

        # Filtro de búsqueda por texto
        if query_str:
            term = f"%{query_str}%"
            # Buscar en series o en libros pertenecientes a la serie
            matching_series_ids_stmt = select(Book.series_id).where(
                or_(
                    Book.title.ilike(term),
                    Book.filename.ilike(term),
                    Book.translator.ilike(term),
                    Book.layout_by.ilike(term),
                )
            )
            base_stmt = base_stmt.where(
                or_(
                    Series.id == query_str,
                    Series.id.ilike(term),
                    Series.name.ilike(term),
                    Series.name_english.ilike(term),
                    Series.name_spanish.ilike(term),
                    Series.slug.ilike(term),
                    Series.author.ilike(term),
                    Series.illustrator.ilike(term),
                    Series.publisher.ilike(term),
                    Series.id.in_(matching_series_ids_stmt),
                )
            )

        # Filtros de consistencia y metadatos faltantes
        if missing_filter == "no_slug":
            base_stmt = base_stmt.where(or_(Series.slug.is_(None), Series.slug == "", Series.slug == "#"))
        elif missing_filter == "no_english":
            base_stmt = base_stmt.where(or_(Series.name_english.is_(None), Series.name_english == ""))
        elif missing_filter == "no_spanish":
            base_stmt = base_stmt.where(or_(Series.name_spanish.is_(None), Series.name_spanish == ""))
        elif missing_filter == "no_illustrator":
            base_stmt = base_stmt.where(or_(Series.illustrator.is_(None), Series.illustrator == ""))
        elif missing_filter == "no_synopsis":
            base_stmt = base_stmt.where(or_(Series.description.is_(None), Series.description == ""))
        elif missing_filter == "no_translator":
            # Series que tengan al menos 1 libro sin traductor
            no_trans_series_stmt = select(Book.series_id).where(
                or_(Book.translator.is_(None), Book.translator == "", Book.translator.ilike("Desconocid%"))
            )
            base_stmt = base_stmt.where(Series.id.in_(no_trans_series_stmt))
        elif missing_filter == "single_volume":
            base_stmt = base_stmt.where(Series.book_count == 1)
        elif missing_filter == "multi_volume":
            base_stmt = base_stmt.where(Series.book_count > 1)

        # Filtro de tipo y demografía
        if book_type_filter:
            base_stmt = base_stmt.where(Series.book_type.ilike(f"%{book_type_filter}%"))
        if demography_filter:
            base_stmt = base_stmt.where(Series.demographics_json.cast(func.text).ilike(f"%{demography_filter}%"))

        # Conteo total de series coincidentes
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_series = (await session.execute(count_stmt)).scalar() or 0

        # Conteo total de libros global
        total_books = (await session.execute(select(func.count(Book.id)))).scalar() or 0

        # Paginación y orden
        sort_by = data.get("sort_by") or "name_asc"
        if sort_by == "name_desc":
            base_stmt = base_stmt.order_by(Series.name.desc())
        elif sort_by == "books_desc":
            base_stmt = base_stmt.order_by(Series.book_count.desc().nullslast(), Series.name.asc())
        elif sort_by == "updated_desc":
            base_stmt = base_stmt.order_by(Series.updated_at.desc().nullslast())
        else:
            base_stmt = base_stmt.order_by(Series.name.asc())

        base_stmt = base_stmt.options(selectinload(Series.books)).offset(offset).limit(limit)

        res = await session.execute(base_stmt)
        series_list = res.scalars().unique().all()

        results = []
        for s in series_list:
            # Ordenar volúmenes por volumen ascendente
            sorted_books = sorted(
                s.books,
                key=lambda b: (b.volume is None, b.volume if b.volume is not None else 9999, b.filename or "")
            )

            books_payload = []
            for b in sorted_books:
                size_mb = f"{(b.file_size / (1024 * 1024)):.2f} MB" if b.file_size else "0 MB"
                books_payload.append({
                    "id": b.id,
                    "book_hash": b.id,
                    "series_id": b.series_id,
                    "title": b.title or "",
                    "volume": b.volume if b.volume is not None else "",
                    "edition": b.edition or "",
                    "translator": b.translator or "",
                    "layout_by": b.layout_by or "",
                    "filename": b.filename or "",
                    "file_size": b.file_size or 0,
                    "size_mb": size_mb,
                    "filepath": b.filepath or "",
                    "cover_url": b.cover_high or b.cover_medium or b.cover_low or "",
                    "language": b.language or "es",
                    "updated_at": b.file_modified_at.isoformat() if b.file_modified_at else None,
                })

            results.append({
                "id": s.id,
                "series_hash": s.id,
                "name": s.name,
                "series_english": s.name_english or "",
                "series_spanish": s.name_spanish or "",
                "slug": s.slug or "",
                "author": s.author or "",
                "author_jap": s.author_jap or "",
                "illustrator": s.illustrator or "",
                "illustrator_jap": s.illustrator_jap or "",
                "description": s.description or "",
                "publisher": s.publisher or "",
                "book_type": s.book_type or "Novela Ligera",
                "demographics": s.demographics_json or [],
                "tags": s.tags_json or [],
                "cover_url": s.cover_url or "",
                "book_count": len(books_payload),
                "books": books_payload,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            })

        pages = (total_series + limit - 1) // limit if total_series > 0 else 1

        return {
            "success": True,
            "series": results,
            "total_series": total_series,
            "total_books": total_books,
            "page": page,
            "pages": pages,
            "limit": limit,
        }


async def handle_admin_update_series_grid(data: dict[str, Any], user_data: dict[str, Any]) -> dict[str, Any]:
    """Actualiza metadatos de una Serie desde la vista Data Grid."""
    series_id = data.get("series_id") or data.get("id")
    if not series_id:
        raise HTTPException(status_code=400, detail="series_id es requerido")

    clean_id = series_id.replace("series_", "") if series_id.startswith("series_") else series_id

    async with pg_manager.get_session() as session:
        stmt = select(Series).where(
            or_(
                Series.id == series_id,
                Series.id == clean_id,
                Series.slug == series_id,
                Series.slug == clean_id,
            )
        )
        res = await session.execute(stmt)
        series = res.scalar_one_or_none()

        if not series:
            raise HTTPException(status_code=404, detail="Serie no encontrada")

        from sqlalchemy import update

        if "name" in data:
            series.name = str(data["name"]).strip()
            if series.name:
                await session.execute(
                    update(Book)
                    .where(Book.series_id == series.id)
                    .values(romaji_title=series.name)
                )
        if "series_english" in data or "name_english" in data:
            val = data.get("series_english", data.get("name_english"))
            series.name_english = str(val).strip() if val else None
            if series.name_english:
                await session.execute(
                    update(Book)
                    .where(Book.series_id == series.id)
                    .values(series_english=series.name_english, english_title=series.name_english)
                )
        if "series_spanish" in data or "name_spanish" in data:
            val = data.get("series_spanish", data.get("name_spanish"))
            series.name_spanish = str(val).strip() if val else None
            if series.name_spanish:
                await session.execute(
                    update(Book)
                    .where(Book.series_id == series.id)
                    .values(series_spanish=series.name_spanish, spanish_title=series.name_spanish)
                )
        if "slug" in data:
            raw_slug = data.get("slug")
            series.slug = _sanitize_slug(raw_slug)
        if "author" in data:
            val = data.get("author")
            series.author = str(val).strip() if val else None
        if "author_jap" in data:
            val = data.get("author_jap")
            series.author_jap = str(val).strip() if val else None
        if "illustrator" in data:
            val = data.get("illustrator")
            series.illustrator = str(val).strip() if val else None
        if "illustrator_jap" in data:
            val = data.get("illustrator_jap")
            series.illustrator_jap = str(val).strip() if val else None
        if "description" in data:
            val = data.get("description")
            series.description = str(val).strip() if val else None
        if "publisher" in data:
            val = data.get("publisher")
            series.publisher = str(val).strip() if val else None
        if "cover_url" in data:
            val = data.get("cover_url")
            series.cover_url = str(val).strip() if val else None
        if "book_type" in data:
            val = data.get("book_type")
            series.book_type = str(val).strip() if val else "Novela Ligera"
        if "demographics" in data or "demographics_json" in data:
            val = data.get("demographics") or data.get("demographics_json")
            from utils.metadata_utils import normalize_demographics_list
            series.demographics_json = normalize_demographics_list(val)
        if "tags" in data or "tags_json" in data or "genres" in data:
            val = data.get("tags") or data.get("tags_json") or data.get("genres")
            if isinstance(val, str):
                series.tags_json = [t.strip() for t in val.split(",") if t.strip()]
            elif isinstance(val, list):
                series.tags_json = [str(t).strip() for t in val if str(t).strip()]

        await session.commit()
        await cache_manager.delete_series(series.id)

        return {
            "success": True,
            "message": "Serie actualizada correctamente",
            "series": {
                "id": series.id,
                "name": series.name,
                "series_english": series.name_english or "",
                "series_spanish": series.name_spanish or "",
                "slug": series.slug or "",
                "author": series.author or "",
                "illustrator": series.illustrator or "",
                "book_type": series.book_type or "",
            }
        }


async def handle_admin_update_book_grid(data: dict[str, Any], user_data: dict[str, Any]) -> dict[str, Any]:
    """Actualiza metadatos de un Libro/Volumen individual desde la vista Data Grid."""
    book_id = data.get("book_id") or data.get("id")
    if not book_id:
        raise HTTPException(status_code=400, detail="book_id es requerido")

    async with pg_manager.get_session() as session:
        stmt = select(Book).where(Book.id == book_id)
        res = await session.execute(stmt)
        book = res.scalar_one_or_none()

        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        if "title" in data:
            val = data.get("title")
            if val:
                book.title = str(val).strip()
        if "volume" in data:
            vol_val = data.get("volume")
            try:
                book.volume = float(vol_val) if vol_val not in (None, "") else None
            except (ValueError, TypeError):
                pass
        if "translator" in data:
            val = data.get("translator")
            book.translator = str(val).strip() if val else None
        if "layout_by" in data:
            val = data.get("layout_by")
            book.layout_by = str(val).strip() if val else None
        if "edition" in data:
            val = data.get("edition")
            book.edition = str(val).strip() if val else None
        if "spanish_title" in data:
            val = data.get("spanish_title")
            book.spanish_title = str(val).strip() if val else None
        if "english_title" in data:
            val = data.get("english_title")
            book.english_title = str(val).strip() if val else None
        if "author" in data:
            val = data.get("author")
            book.author = str(val).strip() if val else None
        if "illustrator" in data:
            val = data.get("illustrator")
            book.illustrator = str(val).strip() if val else None
        if "synopsis" in data or "description" in data:
            val = data.get("synopsis") or data.get("description")
            book.description = str(val).strip() if val else None
        if "publisher" in data or "editorial" in data:
            val = data.get("publisher") or data.get("editorial")
            book.publisher = str(val).strip() if val else None

        await session.commit()
        await cache_manager.delete_book(book_id)

        return {
            "success": True,
            "message": "Volumen actualizado correctamente",
            "book": {
                "id": book.id,
                "title": book.title,
                "volume": book.volume,
                "translator": book.translator or "",
                "layout_by": book.layout_by or "",
            }
        }


async def handle_admin_bulk_save_grid(data: dict[str, Any], user_data: dict[str, Any]) -> dict[str, Any]:
    """Guarda múltiples series y libros modificados en una sola transacción atómica."""
    series_updates = data.get("series_updates") or []
    book_updates = data.get("book_updates") or []

    updated_series_count = 0
    updated_books_count = 0

    async with pg_manager.get_session() as session:
        # 1. Procesar actualizaciones de series
        for s_data in series_updates:
            s_id = s_data.get("id") or s_data.get("series_id")
            if not s_id:
                continue
            stmt = select(Series).where(Series.id == s_id)
            res = await session.execute(stmt)
            series = res.scalar_one_or_none()
            if not series:
                continue

            if s_data.get("name"):
                series.name = str(s_data["name"]).strip()
            if "series_english" in s_data or "name_english" in s_data:
                val = s_data.get("series_english", s_data.get("name_english"))
                series.name_english = str(val).strip() if val else None
            if "series_spanish" in s_data or "name_spanish" in s_data:
                val = s_data.get("series_spanish", s_data.get("name_spanish"))
                series.name_spanish = str(val).strip() if val else None
            if "slug" in s_data:
                series.slug = _sanitize_slug(s_data.get("slug"))
            if "author" in s_data:
                val = s_data.get("author")
                series.author = str(val).strip() if val else None
            if "illustrator" in s_data:
                val = s_data.get("illustrator")
                series.illustrator = str(val).strip() if val else None
            if "book_type" in s_data:
                val = s_data.get("book_type")
                series.book_type = str(val).strip() if val else "Novela Ligera"

            await cache_manager.delete_series(s_id)
            updated_series_count += 1

        # 2. Procesar actualizaciones de libros
        for b_data in book_updates:
            b_id = b_data.get("id") or b_data.get("book_id")
            if not b_id:
                continue
            stmt = select(Book).where(Book.id == b_id)
            res = await session.execute(stmt)
            book = res.scalar_one_or_none()
            if not book:
                continue

            if b_data.get("title"):
                book.title = str(b_data["title"]).strip()
            if "volume" in b_data:
                vol_val = b_data.get("volume")
                try:
                    book.volume = float(vol_val) if vol_val not in (None, "") else None
                except (ValueError, TypeError):
                    pass
            if "translator" in b_data:
                val = b_data.get("translator")
                book.translator = str(val).strip() if val else None
            if "layout_by" in b_data:
                val = b_data.get("layout_by")
                book.layout_by = str(val).strip() if val else None

            await cache_manager.delete_book(b_id)
            updated_books_count += 1

        await session.commit()

    return {
        "success": True,
        "message": f"Guardado exitoso: {updated_series_count} series y {updated_books_count} volúmenes actualizados.",
        "updated_series": updated_series_count,
        "updated_books": updated_books_count,
    }


async def handle_admin_recalculate_series_slug(data: dict[str, Any], user_data: dict[str, Any]) -> dict[str, Any]:
    """Genera y actualiza automáticamente el slug canónico para una serie según sus metadatos."""
    series_id = data.get("series_id") or data.get("id")
    if not series_id:
        raise HTTPException(status_code=400, detail="series_id es requerido")

    async with pg_manager.get_session() as session:
        stmt = select(Series).where(Series.id == series_id)
        res = await session.execute(stmt)
        series = res.scalar_one_or_none()

        if not series:
            raise HTTPException(status_code=404, detail="Serie no encontrada")

        meta = {
            "series_english": series.name_english,
            "series_spanish": series.name_spanish,
            "series_name": series.name,
            "name": series.name,
        }
        computed = generar_slug_from_meta(meta)
        formatted_slug = _sanitize_slug(computed)

        series.slug = formatted_slug
        await session.commit()
        await cache_manager.delete_series(series_id)

        return {
            "success": True,
            "slug": formatted_slug,
            "message": f"Slug actualizado a {formatted_slug}"
        }
