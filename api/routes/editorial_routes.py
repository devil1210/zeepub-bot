# api/routes/editorial_routes.py
"""
REST Endpoints para la Consola Editorial y el cliente ZeeTools Desktop.
Provee acceso modular y seguro al catálogo de tomos, series, fansubs,
biblioteca de plantillas, cola/agenda de publicaciones, historial de posts
y publicación enriquecida en canales de Telegram.
"""

import logging
import os
from typing import Any, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from pydantic import BaseModel, Field

from core.db_manager_pg import pg_manager
from models.library import Book, Series, TranslatorsGroup
from services.ai_service import AIService

logger = logging.getLogger(__name__)


# ==========================================
# Pydantic Schemas para Validación de Entrada
# ==========================================

class BookUpdateSchema(BaseModel):
    title: Optional[str] = None
    spanish_title: Optional[str] = None
    english_title: Optional[str] = None
    volume: Optional[float] = None
    edition: Optional[str] = None
    color_mode: Optional[str] = Field(default="bw", description="'bw' o 'color'")
    is_uncensored: Optional[bool] = False
    author: Optional[str] = None
    illustrator: Optional[str] = None
    demography: Optional[str] = None
    translator: Optional[str] = None
    layout_by: Optional[str] = None
    publisher: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None
    synopsis: Optional[str] = None
    isbn: Optional[str] = None
    asin: Optional[str] = None
    uuid: Optional[str] = None
    romaji_title: Optional[str] = None
    series_romaji: Optional[str] = None
    published_date: Optional[str] = None


class SeriesCreateSchema(BaseModel):
    name: str = Field(..., description="Nombre canónico de la serie")
    series_spanish: Optional[str] = None
    series_english: Optional[str] = None
    author: Optional[str] = None
    illustrator: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    book_type: Optional[str] = "Novela Ligera"
    demographics: Optional[list[str]] = None
    tags: Optional[list[str]] = None


class SeriesUpdateSchema(BaseModel):
    name: Optional[str] = None
    series_spanish: Optional[str] = None
    series_english: Optional[str] = None
    author: Optional[str] = None
    illustrator: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    book_type: Optional[str] = None
    demographics: Optional[list[str]] = None
    tags: Optional[list[str]] = None


class AISuggestRequest(BaseModel):
    title: str = Field(..., description="Nombre del archivo o título original del tomo")


class SchedulePostRequest(BaseModel):
    book_hash: str
    channel_id: int
    scheduled_for: str
    template_id: Optional[int] = None
    custom_caption: Optional[str] = None
    send_as_file: Optional[bool] = True


class PublishNowRequest(BaseModel):
    book_hash: str
    channel_id: int
    template_id: Optional[int] = None
    custom_caption: Optional[str] = None
    send_as_file: Optional[bool] = True


class ChannelSaveSchema(BaseModel):
    id: Optional[int] = None
    name: str
    platform: str = "telegram"
    target_id: str
    is_active: bool = True
    is_favorite: bool = False
    config: Optional[dict[str, Any]] = None


class TemplateSaveSchema(BaseModel):
    id: Optional[int] = None
    name: str
    content: str
    platform: str = "telegram"
    is_default: bool = False
    extra_config: Optional[dict[str, Any]] = None


class QueueActionSchema(BaseModel):
    id: int


class EditorialRoutes:
    """
    Rutas RESTful dedicadas a la gestión editorial y cliente ZeeTools.
    """

    def __init__(self):
        self.router = APIRouter(prefix="/api/editorial", tags=["Editorial / ZeeTools"])

    def get_router(self) -> APIRouter:
        return self.router

    def register_routes(self):
        # 1. Volúmenes / Tomos (Soporte para singular /volume y plural /volumes)
        for prefix in ["/volumes", "/volume"]:
            self.router.add_api_route(
                prefix,
                self.get_volumes,
                methods=["GET"],
                summary="Listar tomos con filtros avanzados",
            )
            self.router.add_api_route(
                prefix,
                self.create_volume,
                methods=["POST"],
                summary="Crear o registrar un nuevo volumen en el catálogo",
            )
            self.router.add_api_route(
                f"{prefix}/{{book_hash}}",
                self.get_volume_detail,
                methods=["GET"],
                summary="Obtener detalle completo de un volumen",
            )
            self.router.add_api_route(
                f"{prefix}/{{book_hash}}",
                self.update_volume,
                methods=["PUT", "PATCH", "POST"],
                summary="Actualizar metadatos de un volumen",
            )
            for sync_suffix in ["/sync_file", "/sync-file"]:
                self.router.add_api_route(
                    f"{prefix}/{{book_hash}}{sync_suffix}",
                    self.sync_volume_file,
                    methods=["POST", "GET"],
                    summary="Re-escanear metadatos directamente del archivo EPUB físico",
                )
            self.router.add_api_route(
                f"{prefix}/{{book_hash}}/cover",
                self.upload_volume_cover,
                methods=["POST"],
                summary="Subir nueva portada de tomo",
            )

        # 2. Series (Soporte para /series, /series/grid, /grid y /library/series)
        for s_path in ["/series", "/series/grid", "/grid", "/library/series"]:
            self.router.add_api_route(
                s_path,
                self.get_series_list,
                methods=["GET"],
                summary="Listar todas las series del catálogo",
            )
        self.router.add_api_route(
            "/series/{series_id}",
            self.get_series_detail,
            methods=["GET"],
            summary="Obtener serie con sus tomos asociados",
        )
        self.router.add_api_route(
            "/series/{series_id}",
            self.update_series,
            methods=["PUT", "PATCH"],
            summary="Actualizar metadatos canónicos de una serie",
        )
        for s_post in ["/series", "/library/series"]:
            self.router.add_api_route(
                s_post,
                self.create_series,
                methods=["POST"],
                summary="Crear nueva serie en el catálogo",
            )

        # 3. Inteligencia Artificial (Gemini)
        self.router.add_api_route(
            "/ai/suggest",
            self.ai_suggest_metadata,
            methods=["POST"],
            summary="Sugerir metadatos limpios y canónicos con IA",
        )

        # 4. Publicación en Telegram y Redes
        for sched_path in ["/publisher/schedule", "/publish/schedule", "/schedule"]:
            self.router.add_api_route(
                sched_path,
                self.schedule_publication,
                methods=["POST"],
                summary="Programar publicación de tomo en Telegram",
            )
        for pub_path in ["/publisher/publish_now", "/publish/now", "/publish_now"]:
            self.router.add_api_route(
                pub_path,
                self.publish_now,
                methods=["POST"],
                summary="Publicar tomo inmediatamente en Telegram",
            )

        # 5. Canales, Plantillas, Agenda y Publicaciones
        for p, h, m in [
            ("/channels", self.get_channels, ["GET"]),
            ("/channels", self.save_channel, ["POST"]),
            ("/channels/{channel_id}", self.delete_channel, ["DELETE"]),
            ("/templates", self.get_templates, ["GET"]),
            ("/templates", self.save_template, ["POST"]),
            ("/templates/{template_id}", self.delete_template, ["DELETE"]),
            ("/templates/restore", self.restore_templates, ["POST"]),
            ("/queue", self.get_queue, ["GET"]),
            ("/queue/cancel", self.cancel_queue_item, ["POST"]),
            ("/queue/retry", self.retry_queue_item, ["POST"]),
            ("/queue/update", self.update_queue_item, ["POST"]),
            ("/posts", self.get_posts_history, ["GET"]),
        ]:
            self.router.add_api_route(p, h, methods=m)

        # 9. Directorio de Fansubs para ZeeTools
        for wg_path in ["/workgroups", "/groups"]:
            self.router.add_api_route(
                wg_path,
                self.get_groups_directory,
                methods=["GET"],
                summary="Directorio oficial de Fansubs y enlaces para ZeeTools",
            )

    # ==========================================
    # Controladores de Rutas
    # ==========================================

    async def get_volumes(
        self,
        query: Optional[str] = Query(None, description="Búsqueda por título, serie, autor o traductor"),
        series_id: Optional[str] = Query(None, description="Filtrar por ID o slug de serie"),
        workgroup_id: Optional[int] = Query(None, description="Filtrar por grupo traductor"),
        edition: Optional[str] = Query(None, description="Filtrar por edición"),
        color_mode: Optional[str] = Query(None, description="Filtrar por modo color ('bw' o 'color')"),
        is_uncensored: Optional[bool] = Query(None, description="Filtrar por versión sin censura"),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=200),
    ):
        """Retorna lista paginada de volúmenes con metadatos completos y estado de consistencia."""
        from sqlalchemy import func, or_, select
        from sqlalchemy.orm import selectinload

        offset = (page - 1) * page_size

        async with pg_manager.get_session() as session:
            stmt = select(Book).options(selectinload(Book.series_info))

            if series_id:
                clean_sid = series_id.replace("series_", "")
                stmt = stmt.where(
                    or_(
                        Book.series_id == clean_sid,
                        Book.series_id == series_id,
                        Book.series_hash == clean_sid,
                    )
                )

            if workgroup_id:
                stmt = stmt.where(Book.workgroup_id == workgroup_id)

            if color_mode:
                if color_mode == "color":
                    stmt = stmt.where(
                        or_(
                            Book.color_mode == "color",
                            Book.edition.ilike("%color%"),
                            Book.filename.ilike("%[color]%"),
                        )
                    )
                else:
                    stmt = stmt.where(
                        or_(
                            Book.color_mode == "bw",
                            Book.color_mode.is_(None),
                        )
                    )

            if is_uncensored is not None:
                stmt = stmt.where(Book.is_uncensored.is_(is_uncensored))

            if query:
                q_clean = f"%{query.strip()}%"
                stmt = stmt.where(
                    or_(
                        Book.title.ilike(q_clean),
                        Book.spanish_title.ilike(q_clean),
                        Book.english_title.ilike(q_clean),
                        Book.author.ilike(q_clean),
                        Book.translator.ilike(q_clean),
                        Book.publisher.ilike(q_clean),
                        Book.filename.ilike(q_clean),
                    )
                )

            # Total Count
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_count = (await session.execute(count_stmt)).scalar() or 0

            # Fetch page
            stmt = stmt.order_by(Book.indexed_at.desc().nullslast(), Book.id.desc()).offset(offset).limit(page_size)
            result = await session.execute(stmt)
            books = result.scalars().all()

            items = [self._serialize_book(b, b.series_info) for b in books]

            return {
                "success": True,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 1,
                "items": items,
            }

    @staticmethod
    def _serialize_book(b: Book, s_rel: Series | None = None) -> dict[str, Any]:
        """Serializa metadatos normalizados de un libro/volumen para ZeeTools y web."""
        s_name = (s_rel.name if s_rel else None) or b.series_name or b.series_spanish or b.title
        return {
            "id": b.id,
            "book_hash": b.id,
            "title": b.title,
            "spanish_title": b.spanish_title or (s_rel.series_spanish if s_rel else None) or b.title,
            "english_title": b.english_title or (s_rel.series_english if s_rel else None) or "",
            "romaji_title": b.romaji_title or "",
            "japanese_title": getattr(b, "japanese_title", None) or getattr(s_rel, "name_japanese", None) or "",
            "series_id": b.series_id,
            "series_name": s_name,
            "series_spanish": (s_rel.series_spanish if s_rel else None) or b.series_spanish or "",
            "series_english": (s_rel.series_english if s_rel else None) or b.english_title or "",
            "series_romaji": (s_rel.name if s_rel else None) or "",
            "volume": b.volume,
            "edition": b.edition or "",
            "color_mode": b.color_mode or ("color" if "[color]" in (b.filename or "").lower() else "bw"),
            "is_uncensored": bool(b.is_uncensored),
            "author": b.author or (s_rel.author if s_rel else None) or "",
            "author_jap": b.author_jap or (s_rel.author_jap if s_rel else None) or "",
            "illustrator": b.illustrator or (s_rel.illustrator if s_rel else None) or "",
            "illustrator_jap": b.illustrator_jap or (s_rel.illustrator_jap if s_rel else None) or "",
            "demography": getattr(b, "demography", None) or "",
            "demographics": b.demographics_json or (s_rel.demographics_json if s_rel else None) or [],
            "tags": b.tags_json or (s_rel.tags_json if s_rel else None) or [],
            "translator": b.translator or "",
            "layout_by": b.layout_by or "",
            "publisher": b.publisher or (s_rel.publisher if s_rel else None) or "",
            "description": b.description or (s_rel.description if s_rel else None) or "",
            "cover_url": b.cover_high or b.cover_medium or b.cover_low or "",
            "filepath": b.filepath or "",
            "filename": b.filename or "",
            "file_size": b.file_size or 0,
            "isbn": b.isbn or "",
            "asin": b.asin or "",
            "uuid": b.uuid or "",
            "epub_version": b.epub_version or "v3.0",
            "word_count": b.word_count,
            "page_count": b.page_count,
            "reading_time": b.reading_time,
            "published_at": b.published_at.isoformat() if b.published_at else None,
            "published_date": b.published_at.strftime("%Y-%m-%d") if b.published_at else "",
            "updated_at": (b.indexed_at or b.created_at).isoformat() if (b.indexed_at or b.created_at) else None,
            "indexed_at": b.indexed_at.isoformat() if b.indexed_at else None,
            "has_bad_metadata": (
                b.volume is None
                or not (b.spanish_title or (s_rel.series_spanish if s_rel else None))
                or not b.publisher
                or not b.translator
            ),
        }

    async def get_volume_detail(self, book_hash: str):
        """Retorna el detalle completo de un volumen individual."""
        from sqlalchemy import or_, select
        from sqlalchemy.orm import selectinload

        clean_hash = book_hash.strip()
        async with pg_manager.get_session() as session:
            stmt = select(Book).options(selectinload(Book.series_info)).where(
                or_(
                    Book.id == clean_hash,
                    Book.id.startswith(clean_hash),
                    Book.hash_md5 == clean_hash,
                    Book.hash_md5.startswith(clean_hash),
                    Book.short_link == clean_hash,
                )
            )
            res = await session.execute(stmt)
            b = res.scalar_one_or_none()

            if not b:
                raise HTTPException(status_code=404, detail="Volumen no encontrado")

            return {
                "success": True,
                "book": self._serialize_book(b, b.series_info)
            }

    async def create_volume(self, payload: dict = Body(...)):
        """Crea o registra un volumen en el catálogo."""
        import hashlib
        from sqlalchemy import or_, select
        from services.cache_service import cache_manager

        sid = payload.get("series_id")
        if not sid:
            raise HTTPException(status_code=400, detail="series_id es obligatorio")

        title = payload.get("title") or payload.get("english_title") or "Sin título"
        vol = payload.get("volume")
        if vol is not None:
            try:
                vol = float(vol)
            except (ValueError, TypeError):
                vol = None

        raw_id = payload.get("book_hash") or payload.get("id") or payload.get("uuid")
        if not raw_id:
            raw_id = hashlib.sha256(f"{sid}_{vol}_{title}".encode()).hexdigest()

        async with pg_manager.get_session() as session:
            stmt = select(Book).where(or_(Book.id == raw_id, Book.hash_md5 == raw_id))
            res = await session.execute(stmt)
            b = res.scalar_one_or_none()
            is_new = False
            if not b:
                is_new = True
                b = Book(
                    id=raw_id,
                    series_id=sid,
                    source_id=1,
                    filepath=payload.get("filepath") or f"/library/manual/{raw_id}.epub",
                    filename=payload.get("filename") or f"{raw_id}.epub",
                    file_size=int(payload.get("file_size") or 0),
                    title=title,
                )
                session.add(b)

            b.series_id = sid
            b.title = title
            b.volume = vol
            if payload.get("spanish_title"):
                b.spanish_title = payload.get("spanish_title").strip()
            if payload.get("english_title"):
                b.english_title = payload.get("english_title").strip()
            if payload.get("romaji_title"):
                b.romaji_title = payload.get("romaji_title").strip()
            if payload.get("author"):
                b.author = payload.get("author").strip()
            if payload.get("illustrator"):
                b.illustrator = payload.get("illustrator").strip()
            if payload.get("translator"):
                b.translator = payload.get("translator").strip()
            if payload.get("layout_by"):
                b.layout_by = payload.get("layout_by").strip()
            if payload.get("publisher"):
                b.publisher = payload.get("publisher").strip()
            if payload.get("description"):
                b.description = payload.get("description").strip()
            if payload.get("isbn"):
                b.isbn = payload.get("isbn").strip()
            if payload.get("asin"):
                b.asin = payload.get("asin").strip()
            if payload.get("uuid"):
                b.uuid = payload.get("uuid").strip()
            if payload.get("color_mode"):
                b.color_mode = payload.get("color_mode").strip()
            if payload.get("published_date"):
                try:
                    from datetime import datetime
                    c_date = str(payload.get("published_date")).strip().split("T")[0]
                    b.published_at = datetime.fromisoformat(c_date)
                except (ValueError, TypeError):
                    pass

            await session.commit()
            await cache_manager.delete_book(b.id)

            return {
                "success": True,
                "message": "Volumen registrado correctamente" if is_new else "Volumen actualizado correctamente",
                "book_id": b.id,
                "book": self._serialize_book(b, b.series_info),
            }

    async def update_volume(self, book_hash: str, payload: BookUpdateSchema):
        """Actualiza los metadatos de un volumen."""
        from sqlalchemy import or_, select

        from services.cache_service import cache_manager

        clean_hash = book_hash.strip()
        async with pg_manager.get_session() as session:
            stmt = select(Book).where(or_(Book.id == clean_hash, Book.hash_md5 == clean_hash))
            res = await session.execute(stmt)
            b = res.scalar_one_or_none()

            if not b:
                raise HTTPException(status_code=404, detail="Volumen no encontrado")

            if payload.title is not None:
                b.title = payload.title.strip()
            if payload.spanish_title is not None:
                b.spanish_title = payload.spanish_title.strip() if payload.spanish_title else None
            if payload.english_title is not None:
                b.english_title = payload.english_title.strip() if payload.english_title else None
            if payload.volume is not None:
                b.volume = payload.volume
            if payload.edition is not None:
                b.edition = payload.edition.strip() if payload.edition else None
            if payload.color_mode is not None:
                b.color_mode = payload.color_mode.strip()
            if payload.is_uncensored is not None:
                b.is_uncensored = payload.is_uncensored
            if payload.author is not None:
                b.author = payload.author.strip() if payload.author else None
            if payload.illustrator is not None:
                b.illustrator = payload.illustrator.strip() if payload.illustrator else None
            if payload.translator is not None:
                b.translator = payload.translator.strip() if payload.translator else None
            if payload.layout_by is not None:
                b.layout_by = payload.layout_by.strip() if payload.layout_by else None
            if payload.publisher is not None:
                b.publisher = payload.publisher.strip() if payload.publisher else None
            if payload.cover_url is not None:
                b.cover_high = payload.cover_url.strip() if payload.cover_url else None
                b.cover_medium = payload.cover_url.strip() if payload.cover_url else None
                b.cover_low = payload.cover_url.strip() if payload.cover_url else None
            if payload.description is not None:
                b.description = payload.description.strip() if payload.description else None
            elif payload.synopsis is not None:
                b.description = payload.synopsis.strip() if payload.synopsis else None
            if payload.isbn is not None:
                b.isbn = payload.isbn.strip() if payload.isbn else None
            if payload.asin is not None:
                b.asin = payload.asin.strip() if payload.asin else None
            if payload.uuid is not None:
                b.uuid = payload.uuid.strip() if payload.uuid else None
            if payload.romaji_title is not None:
                b.romaji_title = payload.romaji_title.strip() if payload.romaji_title else None
            if payload.published_date is not None:
                if payload.published_date.strip():
                    try:
                        from datetime import datetime
                        cleaned_date = payload.published_date.strip().split("T")[0]
                        b.published_at = datetime.fromisoformat(cleaned_date)
                    except (ValueError, TypeError) as date_err:
                        logger.warning(f"Error parseando published_date '{payload.published_date}': {date_err}")
                else:
                    b.published_at = None

            await session.commit()
            await cache_manager.delete_book(b.id)

            return {
                "success": True,
                "message": "Metadatos del volumen actualizados correctamente",
                "book_id": b.id,
            }

    async def upload_volume_cover(
        self,
        book_hash: str,
        file: UploadFile = File(...),
    ):
        """Sube una nueva portada personalizada para el tomo."""
        import hashlib

        from sqlalchemy import or_, select

        from core.db_manager_pg import pg_manager
        from models.library import Book
        from services.cache_service import cache_manager
        from utils.library_db import COVERS_DIR

        os.makedirs(COVERS_DIR, exist_ok=True)
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Archivo de imagen vacío")

        ext = os.path.splitext(file.filename or "")[1] or ".jpg"
        cover_filename = f"custom_{book_hash[:16]}_{hashlib.md5(content).hexdigest()[:8]}{ext}"
        cover_path = os.path.join(COVERS_DIR, cover_filename)
        with open(cover_path, "wb") as f:
            f.write(content)

        cover_url = f"/api/library/covers/{cover_filename}"

        async with pg_manager.get_session() as session:
            stmt = select(Book).where(
                or_(Book.hash_md5 == book_hash, Book.id == book_hash)
            )
            res = await session.execute(stmt)
            b = res.scalar_one_or_none()
            if not b:
                raise HTTPException(status_code=404, detail="Tomo no encontrado")

            b.cover_url = cover_url
            await session.commit()
            await cache_manager.delete_book(b.id)

        return {
            "success": True,
            "message": "Portada actualizada correctamente",
            "cover_url": cover_url,
        }

    async def sync_volume_file(self, book_hash: str):
        """Re-escanea metadatos directamente del archivo físico EPUB en disco."""
        from api.handlers.admin.grid_handlers import handle_admin_sync_books
        res = await handle_admin_sync_books(
            {"book_ids": [book_hash], "book_hash": book_hash},
            {"level": "admin", "is_admin": True, "is_real_admin": True},
        )
        return res

    async def get_series_list(
        self,
        query: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=100),
    ):
        """Retorna lista de series registradas."""
        from sqlalchemy import func, or_, select
        from sqlalchemy.orm import selectinload

        offset = (page - 1) * page_size
        async with pg_manager.get_session() as session:
            stmt = select(Series).options(selectinload(Series.books))

            if query:
                q_clean = f"%{query.strip()}%"
                stmt = stmt.where(
                    or_(
                        Series.name.ilike(q_clean),
                        Series.name_spanish.ilike(q_clean),
                        Series.name_english.ilike(q_clean),
                        Series.author.ilike(q_clean),
                        Series.publisher.ilike(q_clean),
                        Series.slug.ilike(q_clean),
                    )
                )

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = (await session.execute(count_stmt)).scalar() or 0

            if total > 0:
                stmt = stmt.order_by(Series.name.asc()).offset(offset).limit(page_size)
                result = await session.execute(stmt)
                series_list = result.scalars().all()

                items = [
                    {
                        "id": s.id,
                        "series_hash": s.id,
                        "name": s.name,
                        "series_spanish": s.series_spanish or getattr(s, "name_spanish", "") or "",
                        "series_english": s.series_english or getattr(s, "name_english", "") or "",
                        "slug": s.slug or "",
                        "author": s.author or "",
                        "illustrator": s.illustrator or "",
                        "publisher": s.publisher or "",
                        "book_count": len(s.books or []),
                        "cover_url": s.cover_url or "",
                    }
                    for s in series_list
                ]
            else:
                # Fallback resiliente: Agrupar desde la tabla Book si la tabla Series está vacía
                fallback_stmt = select(Book).options(selectinload(Book.series_info))
                if query:
                    q_clean = f"%{query.strip()}%"
                    fallback_stmt = fallback_stmt.where(
                        or_(
                            Book.title.ilike(q_clean),
                            Book.spanish_title.ilike(q_clean),
                            Book.english_title.ilike(q_clean),
                            Book.author.ilike(q_clean),
                            Book.translator.ilike(q_clean),
                        )
                    )
                b_res = await session.execute(fallback_stmt)
                all_books = b_res.scalars().all()
                grouped: dict[str, dict[str, Any]] = {}
                for b in all_books:
                    s_name = (
                        b.spanish_title
                        or (b.series_info.name if b.series_info else None)
                        or (b.series_info.series_spanish if b.series_info else None)
                        or b.series_name
                        or b.title
                    )
                    s_name = (s_name or "Serie Desconocida").strip()
                    if s_name not in grouped:
                        grouped[s_name] = {
                            "id": b.series_id or f"series_{abs(hash(s_name))}",
                            "series_hash": b.series_id or f"series_{abs(hash(s_name))}",
                            "name": s_name,
                            "series_spanish": b.spanish_title or s_name,
                            "series_english": b.english_title or "",
                            "slug": "",
                            "author": b.author or "",
                            "illustrator": b.illustrator or "",
                            "publisher": b.publisher or "",
                            "book_count": 0,
                            "cover_url": b.cover_high or b.cover_medium or b.cover_low or "",
                        }
                    grouped[s_name]["book_count"] += 1

                aggregated_items = sorted(grouped.values(), key=lambda x: x["name"])
                total = len(aggregated_items)
                items = aggregated_items[offset : offset + page_size]

            return {
                "success": True,
                "total": total,
                "total_series": total,
                "totalItems": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
                "items": items,
                "series": items,
                "results": items,
            }

    async def get_series_detail(self, series_id: str):
        """Retorna el detalle completo de una serie con sus tomos asociados."""
        from sqlalchemy import or_, select
        from sqlalchemy.orm import selectinload

        clean_id = series_id.strip()
        async with pg_manager.get_session() as session:
            stmt = select(Series).options(selectinload(Series.books)).where(
                or_(
                    Series.id == clean_id,
                    Series.slug == clean_id,
                )
            )
            res = await session.execute(stmt)
            s = res.scalar_one_or_none()

            if not s:
                raise HTTPException(status_code=404, detail="Serie no encontrada")

            return {
                "success": True,
                "series": {
                    "id": s.id,
                    "name": s.name,
                    "series_spanish": s.series_spanish or getattr(s, "name_spanish", "") or "",
                    "series_english": s.series_english or getattr(s, "name_english", "") or "",
                    "slug": s.slug or "",
                    "author": s.author or "",
                    "illustrator": s.illustrator or "",
                    "publisher": s.publisher or "",
                    "description": s.description or "",
                    "cover_url": s.cover_url or "",
                    "books": [
                        {
                            "id": b.id,
                            "title": b.title,
                            "volume": b.volume,
                            "cover_url": b.cover_high or b.cover_medium or b.cover_low or "",
                            "color_mode": b.color_mode or "bw",
                            "is_uncensored": bool(b.is_uncensored),
                            "translator": b.translator or "",
                        }
                        for b in (s.books or [])
                    ],
                }
            }

    async def update_series(self, series_id: str, payload: SeriesUpdateSchema):
        """Actualiza metadatos canónicos de una serie."""
        from sqlalchemy import or_, select

        clean_id = series_id.strip()
        async with pg_manager.get_session() as session:
            stmt = select(Series).where(or_(Series.id == clean_id, Series.slug == clean_id))
            res = await session.execute(stmt)
            s = res.scalar_one_or_none()

            if not s:
                raise HTTPException(status_code=404, detail="Serie no encontrada")

            if payload.name is not None:
                s.name = payload.name.strip()
            if payload.series_spanish is not None:
                s.series_spanish = payload.series_spanish.strip()
            if payload.series_english is not None:
                s.series_english = payload.series_english.strip()
            if payload.author is not None:
                s.author = payload.author.strip()
            if payload.illustrator is not None:
                s.illustrator = payload.illustrator.strip()
            if payload.publisher is not None:
                s.publisher = payload.publisher.strip()
            if payload.description is not None:
                s.description = payload.description.strip()
            if payload.book_type is not None:
                s.book_type = payload.book_type.strip()
            if payload.demographics is not None:
                s.demographics_json = payload.demographics
            if payload.tags is not None:
                s.tags_json = payload.tags

            await session.commit()
            return {
                "success": True,
                "message": "Serie actualizada correctamente",
                "series_id": s.id,
            }

    async def create_series(self, payload: SeriesCreateSchema):
        """Crea una nueva serie en el catálogo editorial."""
        import hashlib

        from slugify import slugify
        from sqlalchemy import or_, select

        clean_name = payload.name.strip()
        series_id = hashlib.sha256(clean_name.lower().encode("utf-8")).hexdigest()[:16]
        slug = slugify(clean_name)

        async with pg_manager.get_session() as session:
            stmt = select(Series).where(or_(Series.id == series_id, Series.name == clean_name))
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()

            if existing:
                return {
                    "success": True,
                    "message": "La serie ya existe en el catálogo",
                    "series_id": existing.id,
                    "id": existing.id,
                }

            new_series = Series(
                id=series_id,
                name=clean_name,
                name_spanish=payload.series_spanish or clean_name,
                name_english=payload.series_english,
                slug=slug,
                author=payload.author,
                illustrator=payload.illustrator,
                publisher=payload.publisher,
                description=payload.description,
                book_type=payload.book_type or "Novela Ligera",
            )
            session.add(new_series)
            await session.commit()

            return {
                "success": True,
                "message": "Serie creada exitosamente",
                "series_id": series_id,
                "id": series_id,
            }

    async def ai_suggest_metadata(self, request: AISuggestRequest):
        """Endpoint de sugerencia inteligente de metadatos con Gemini."""
        prompt = f"""
        Eres un bibliotecario y catalogador experto de novelas ligeras y manga en español.
        Dado el siguiente nombre o título de archivo EPUB:
        "{request.title}"

        Analiza y extrae/sugiere los metadatos más limpios y canónicos:
        1. spanish_title: Título oficial o más conocido en español (sin número de volumen ni extensiones).
        2. english_title: Título oficial en inglés / internacional.
        3. author: Nombre del autor.
        4. volume: Número del volumen (ej: 1, 2, 4.5) como número flotante o entero, o null si no se identifica.
        5. demography: Shonen, Shojo, Seinen, Josei o General.

        Responde ÚNICAMENTE un objeto JSON válido con los campos: spanish_title, english_title, author, volume, demography.
        """
        try:
            import json
            response_text = await AIService._call_ai(prompt, json_mode=True)
            if not response_text:
                return {"success": False, "message": "No se recibió respuesta de IA"}
            cleaned_json = AIService._extract_json_from_text(response_text)
            metadata = json.loads(cleaned_json)
            return {"success": True, "metadata": metadata}
        except Exception as e:
            logger.error(f"Error sugiriendo metadatos con IA: {e}")
            return {"success": False, "message": str(e)}

    # ==========================================
    # Publisher / Canales / Plantillas / Cola
    # ==========================================

    async def get_channels(self):
        from api.handlers.publisher import handle_pub_get_channels
        return await handle_pub_get_channels({}, {"level": "admin", "is_admin": True, "is_real_admin": True})

    async def save_channel(self, payload: ChannelSaveSchema):
        from api.handlers.publisher import handle_pub_save_channel
        return await handle_pub_save_channel(payload.model_dump(), {"level": "admin", "is_admin": True, "is_real_admin": True})

    async def delete_channel(self, channel_id: int):
        from api.handlers.publisher import handle_pub_delete_channel
        return await handle_pub_delete_channel({"id": channel_id}, {"level": "admin", "is_admin": True, "is_real_admin": True})

    async def get_templates(self, platform: Optional[str] = Query(None)):
        from api.handlers.publisher import handle_pub_get_templates
        return await handle_pub_get_templates({"platform": platform}, {"level": "admin", "is_admin": True, "is_real_admin": True})

    async def save_template(self, payload: TemplateSaveSchema):
        from api.handlers.publisher import handle_pub_save_template
        return await handle_pub_save_template(payload.model_dump(), {"level": "admin", "is_admin": True, "is_real_admin": True})

    async def delete_template(self, template_id: int):
        from api.handlers.publisher import handle_pub_delete_template
        return await handle_pub_delete_template({"id": template_id}, {"level": "admin", "is_admin": True, "is_real_admin": True})

    async def restore_templates(self):
        from api.handlers.publisher import handle_pub_restore_templates
        return await handle_pub_restore_templates({}, {"level": "admin", "is_admin": True, "is_real_admin": True})

    async def get_queue(self, status: Optional[str] = Query(None), limit: int = Query(100)):
        from api.handlers.publisher import handle_pub_get_queue
        return await handle_pub_get_queue({"status": status, "limit": limit}, {"level": "admin", "is_admin": True, "is_real_admin": True})

    async def cancel_queue_item(self, payload: QueueActionSchema):
        from api.handlers.publisher import handle_pub_cancel
        return await handle_pub_cancel({"queue_id": payload.id}, {"level": "admin", "is_admin": True, "is_real_admin": True})

    async def retry_queue_item(self, payload: QueueActionSchema):
        from api.handlers.publisher import handle_pub_retry
        return await handle_pub_retry({"queue_id": payload.id}, {"level": "admin", "is_admin": True, "is_real_admin": True})

    async def update_queue_item(self, payload: dict = Body(...)):
        from api.handlers.publisher import handle_pub_update_queue_item
        return await handle_pub_update_queue_item(payload, {"level": "admin", "is_admin": True, "is_real_admin": True})

    async def get_posts_history(self, limit: int = Query(100)):
        from api.handlers.publisher import handle_pub_get_queue
        return await handle_pub_get_queue({"status": "sent", "limit": limit}, {"level": "admin", "is_admin": True, "is_real_admin": True})

    async def schedule_publication(self, payload: SchedulePostRequest):
        from api.handlers.publisher import handle_pub_schedule
        return await handle_pub_schedule(
            {"book_id": payload.book_hash, "book_hash": payload.book_hash, "channel_id": payload.channel_id, "scheduled_for": payload.scheduled_for, "template_id": payload.template_id, "caption": payload.custom_caption, "send_as_file": payload.send_as_file},
            {"level": "admin", "is_admin": True, "is_real_admin": True},
        )

    async def publish_now(self, payload: PublishNowRequest):
        from api.handlers.publisher import handle_pub_quick_post
        return await handle_pub_quick_post(
            {"book_id": payload.book_hash, "book_hash": payload.book_hash, "channel_id": payload.channel_id, "template_id": payload.template_id, "caption": payload.custom_caption, "send_as_file": payload.send_as_file},
            {"level": "admin", "is_admin": True, "is_real_admin": True},
        )

    async def get_groups_directory(self):
        """Directorio público de grupos/fansubs para ZeeTools."""
        from api.routes.legacy_routes import LegacyRoutes
        lr = LegacyRoutes()
        return await lr.get_public_workgroups()
