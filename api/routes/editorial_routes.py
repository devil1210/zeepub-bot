# api/routes/editorial_routes.py
"""
REST Endpoints para la Consola Editorial y el cliente ZeeTools Desktop.
Provee acceso modular y seguro al catálogo de tomos, series, fansubs,
autocompletado por IA y publicación en canales de Telegram.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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


class PublishNowRequest(BaseModel):
    book_hash: str
    channel_id: int
    template_id: Optional[int] = None


class EditorialRoutes:
    """
    Rutas RESTful dedicadas a la gestión editorial y cliente ZeeTools.
    """

    def __init__(self):
        self.router = APIRouter(prefix="/api/editorial", tags=["Editorial / ZeeTools"])

    def get_router(self) -> APIRouter:
        return self.router

    def register_routes(self):
        # 1. Volúmenes / Tomos
        self.router.add_api_route(
            "/volumes",
            self.get_volumes,
            methods=["GET"],
            summary="Listar tomos con filtros avanzados",
        )
        self.router.add_api_route(
            "/volumes/{book_hash}",
            self.get_volume_detail,
            methods=["GET"],
            summary="Obtener detalle completo de un volumen",
        )
        self.router.add_api_route(
            "/volumes/{book_hash}",
            self.update_volume,
            methods=["PUT", "PATCH"],
            summary="Actualizar metadatos de un volumen",
        )
        self.router.add_api_route(
            "/volumes/{book_hash}/sync_file",
            self.sync_volume_file,
            methods=["POST"],
            summary="Re-escanear metadatos directamente del archivo EPUB físico",
        )

        # 2. Series
        self.router.add_api_route(
            "/series",
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

        # 3. Inteligencia Artificial (Gemini)
        self.router.add_api_route(
            "/ai/suggest",
            self.ai_suggest_metadata,
            methods=["POST"],
            summary="Sugerir metadatos limpios y canónicos con IA",
        )

        # 4. Publicación en Telegram
        self.router.add_api_route(
            "/publisher/schedule",
            self.schedule_publication,
            methods=["POST"],
            summary="Programar publicación de tomo en Telegram",
        )
        self.router.add_api_route(
            "/publisher/publish_now",
            self.publish_now,
            methods=["POST"],
            summary="Publicar tomo inmediatamente en Telegram",
        )

        # 5. Directorio de Fansubs para ZeeTools
        self.router.add_api_route(
            "/groups",
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
            stmt = select(Book).options(selectinload(Book.series_rel))

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
            stmt = stmt.order_by(Book.updated_at.desc().nullslast(), Book.id.desc()).offset(offset).limit(page_size)
            result = await session.execute(stmt)
            books = result.scalars().all()

            items = []
            for b in books:
                s_rel = b.series_rel
                s_name = (s_rel.name if s_rel else None) or b.series_name or b.series_spanish or b.title
                items.append({
                    "id": b.id,
                    "book_hash": b.id,
                    "title": b.title,
                    "spanish_title": b.spanish_title or (s_rel.series_spanish if s_rel else None) or b.title,
                    "english_title": b.english_title or (s_rel.series_english if s_rel else None) or "",
                    "series_id": b.series_id,
                    "series_name": s_name,
                    "series_spanish": (s_rel.series_spanish if s_rel else None) or b.series_spanish or "",
                    "volume": b.volume,
                    "edition": b.edition or "",
                    "color_mode": b.color_mode or ("color" if "[color]" in (b.filename or "").lower() else "bw"),
                    "is_uncensored": bool(b.is_uncensored),
                    "author": b.author or (s_rel.author if s_rel else None) or "",
                    "illustrator": b.illustrator or (s_rel.illustrator if s_rel else None) or "",
                    "translator": b.translator or "",
                    "layout_by": b.layout_by or "",
                    "publisher": b.publisher or (s_rel.publisher if s_rel else None) or "",
                    "description": b.description or (s_rel.description if s_rel else None) or "",
                    "cover_url": b.cover_high or b.cover_medium or b.cover_low or "",
                    "filepath": b.filepath or "",
                    "filename": b.filename or "",
                    "file_size": b.file_size or 0,
                    "updated_at": b.updated_at.isoformat() if b.updated_at else None,
                })

            return {
                "success": True,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 1,
                "items": items,
            }

    async def get_volume_detail(self, book_hash: str):
        """Retorna el detalle completo de un volumen individual."""
        from sqlalchemy import or_, select
        from sqlalchemy.orm import selectinload

        clean_hash = book_hash.strip()
        async with pg_manager.get_session() as session:
            stmt = select(Book).options(selectinload(Book.series_rel)).where(
                or_(
                    Book.id == clean_hash,
                    Book.hash_md5 == clean_hash,
                    Book.short_link == clean_hash,
                )
            )
            res = await session.execute(stmt)
            b = res.scalar_one_or_none()

            if not b:
                raise HTTPException(status_code=404, detail="Volumen no encontrado")

            s_rel = b.series_rel
            return {
                "success": True,
                "book": {
                    "id": b.id,
                    "book_hash": b.id,
                    "title": b.title,
                    "spanish_title": b.spanish_title or (s_rel.series_spanish if s_rel else None) or b.title,
                    "english_title": b.english_title or (s_rel.series_english if s_rel else None) or "",
                    "series_id": b.series_id,
                    "series_name": (s_rel.name if s_rel else None) or b.series_name or b.title,
                    "series_spanish": (s_rel.series_spanish if s_rel else None) or b.series_spanish or "",
                    "volume": b.volume,
                    "edition": b.edition or "",
                    "color_mode": b.color_mode or ("color" if "[color]" in (b.filename or "").lower() else "bw"),
                    "is_uncensored": bool(b.is_uncensored),
                    "author": b.author or (s_rel.author if s_rel else None) or "",
                    "illustrator": b.illustrator or (s_rel.illustrator if s_rel else None) or "",
                    "demography": getattr(b, "demography", None) or "",
                    "translator": b.translator or "",
                    "layout_by": b.layout_by or "",
                    "publisher": b.publisher or (s_rel.publisher if s_rel else None) or "",
                    "description": b.description or (s_rel.description if s_rel else None) or "",
                    "cover_url": b.cover_high or b.cover_medium or b.cover_low or "",
                    "filepath": b.filepath or "",
                    "filename": b.filename or "",
                    "file_size": b.file_size or 0,
                    "has_bad_metadata": (
                        b.volume is None
                        or not (b.spanish_title or (s_rel.series_spanish if s_rel else None))
                        or not b.publisher
                        or not b.translator
                    ),
                }
            }

    async def update_volume(self, book_hash: str, payload: BookUpdateSchema):
        """Actualiza los metadatos de un volumen."""
        from sqlalchemy import or_, select
        from core.cache_manager import cache_manager

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

            await session.commit()
            await cache_manager.delete_book(b.id)

            return {
                "success": True,
                "message": "Metadatos del volumen actualizados correctamente",
                "book_id": b.id,
            }

    async def sync_volume_file(self, book_hash: str):
        """Re-escanea metadatos directamente del archivo físico EPUB en disco."""
        from api.handlers.admin.grid_handlers import handle_admin_sync_books
        res = await handle_admin_sync_books({"book_ids": [book_hash]}, {"is_admin": True})
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

            return {
                "success": True,
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": items,
            }

    async def get_series_detail(self, series_id: str):
        """Obtiene una serie con todos sus tomos asociados."""
        from api.handlers.admin.library_handlers import handle_admin_get_series_detail
        res = await handle_admin_get_series_detail({"series_id": series_id}, {"is_admin": True})
        return res

    async def update_series(self, series_id: str, payload: SeriesUpdateSchema):
        """Actualiza los metadatos canónicos de una serie."""
        from sqlalchemy import or_, select
        clean_id = series_id.replace("series_", "").strip()

        async with pg_manager.get_session() as session:
            stmt = select(Series).where(or_(Series.id == series_id, Series.id == clean_id, Series.slug == clean_id))
            res = await session.execute(stmt)
            s = res.scalar_one_or_none()

            if not s:
                raise HTTPException(status_code=404, detail="Serie no encontrada")

            if payload.name is not None:
                s.name = payload.name.strip()
            if payload.series_spanish is not None:
                s.name_spanish = payload.series_spanish.strip() if payload.series_spanish else None
            if payload.series_english is not None:
                s.name_english = payload.series_english.strip() if payload.series_english else None
            if payload.author is not None:
                s.author = payload.author.strip() if payload.author else None
            if payload.illustrator is not None:
                s.illustrator = payload.illustrator.strip() if payload.illustrator else None
            if payload.publisher is not None:
                s.publisher = payload.publisher.strip() if payload.publisher else None
            if payload.description is not None:
                s.description = payload.description.strip() if payload.description else None
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

    async def schedule_publication(self, payload: SchedulePostRequest):
        """Programa publicación en canal de Telegram."""
        from api.handlers.publisher import handle_pub_schedule
        return await handle_pub_schedule(payload.model_dump(), {"is_admin": True})

    async def publish_now(self, payload: PublishNowRequest):
        """Publica inmediatamente en canal de Telegram."""
        from api.handlers.publisher import handle_pub_quick_post
        return await handle_pub_quick_post(payload.model_dump(), {"is_admin": True})

    async def get_groups_directory(self):
        """Directorio público de grupos/fansubs para ZeeTools."""
        from api.routes.legacy_routes import LegacyRoutes
        lr = LegacyRoutes()
        return await lr.get_public_workgroups()
