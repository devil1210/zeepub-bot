import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select, text
from sqlalchemy.orm import selectinload

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, MetadataProposal, SeriesMetadata, TranslatorsGroup, UserDownload
from repositories.book_repository import book_repo
from repositories.series_repository import series_repo
from schemas.library_schemas import BookDTO, CoverUrlDTO, SeriesDTO

logger = logging.getLogger(__name__)


class LibraryService:
    _is_ai_scanning = False

    @staticmethod
    async def search_books(
        query: str,
        page: int = 1,
        items_per_page: int = 10,
        search_type: str = "all",
        source_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Realiza una búsqueda de libros delegando al repositorio.
        """
        return await book_repo.search_books(
            query=query,
            page=page,
            items_per_page=items_per_page,
            search_type=search_type,
            source_id=source_id,
        )

    @staticmethod
    async def search_series(
        query: str,
        page: int = 1,
        items_per_page: int = 20,
        source_id: int | None = None,
        search_type: str = "todos",
        sort_by: str = "a-z",
    ) -> dict[str, Any]:
        """
        Búsqueda agrupada por series. Retorna DTOs de Series.
        """
        # 1. Ejecutar búsqueda en el repositorio
        search_results = await series_repo.search_series(
            query=query,
            page=page,
            items_per_page=items_per_page,
            source_id=source_id,
            search_type=search_type,
            sort_by=sort_by,
        )

        series_list = search_results.get("results", [])

        # 2. Mapeo a DTOs (con pre-carga de libros representativos si es necesario)
        async with pg_manager.get_session() as session:
            series_hashes = [s.series_hash for s in series_list]
            rep_books_map = {}
            if series_hashes:
                # Subconsulta para obtener el ID del primer libro por serie
                subq = (
                    select(LocalBook.series_hash, func.min(LocalBook.id).label("min_id"))
                    .where(LocalBook.series_hash.in_(series_hashes))
                    .group_by(LocalBook.series_hash)
                    .subquery()
                )
                rep_stmt = select(LocalBook).join(subq, LocalBook.id == subq.c.min_id)
                rep_res = await session.execute(rep_stmt)
                for b in rep_res.scalars().all():
                    rep_books_map[b.series_hash] = b

            results = []
            for s in series_list:
                rep = rep_books_map.get(s.series_hash)
                results.append(LibraryService._map_series_entity_to_dto(s, rep))

            return {
                "results": results,
                "currentPage": page,
                "totalPages": search_results.get("totalPages", 0),
                "totalItems": search_results.get("totalItems", 0),
            }

    @staticmethod
    def _map_series_entity_to_dto(s: SeriesMetadata, rep: Any | None) -> dict[str, Any]:
        """Mapea una entidad SeriesMetadata y un libro representativo a un DTO de serie."""
        display_cover = s.cover_url or (rep.cover_low if rep else None) or (rep.cover_high if rep else None)

        dto = SeriesDTO(
            id=f"series_{s.series_hash}",
            series_hash=s.series_hash,
            title=s.series_name,
            series=s.series_name,
            series_spanish=s.series_spanish,
            series_english=s.series_english,
            author=s.author,
            description=s.description,
            cover=display_cover,
            coverUrl=CoverUrlDTO(
                cover_low=display_cover,
                cover_medium=display_cover.replace("_low.jpg", "_medium.jpg")
                if display_cover and "_low.jpg" in display_cover
                else display_cover,
                cover_high=display_cover.replace("_low.jpg", "_high.jpg")
                if display_cover and "_low.jpg" in display_cover
                else display_cover,
                cover_original=display_cover.replace("_low.jpg", "_original.jpg")
                if display_cover and "_low.jpg" in display_cover
                else display_cover,
            ),
            numBooks=s.book_count,
            book_count=s.book_count,
            book_type=getattr(s, "book_type", "Novela"),
            tag_list=s.tags if s.tags else [],
            rating_average=s.rating_average,
            rating_count=s.rating_count,
            download_count=getattr(s, "download_count", 0),
            illustrator=s.illustrator,
            translator=(rep.translator if rep else None),
            layout_by=(rep.layout_by if rep else None),
            lastUpdated=s.updated_at.isoformat() if s.updated_at else None,
        )
        return dto.model_dump()

    @staticmethod
    async def get_series_by_hash_dto(series_hash: str) -> dict[str, Any] | None:
        """Obtiene el DTO de una serie por su hash, incluyendo un libro representativo."""
        async with pg_manager.get_session() as session:
            s = await series_repo.get_by_hash(series_hash)
            if not s:
                return None

            # Buscar libro representativo para la portada
            rep_stmt = select(LocalBook).where(LocalBook.series_hash == series_hash).limit(1)
            res = await session.execute(rep_stmt)
            rep = res.scalars().first()

            return LibraryService._map_series_entity_to_dto(s, rep)

    @staticmethod
    async def get_translator_siglas_map() -> dict[str, str]:
        """Obtiene un mapa de nombre_traductor -> siglas."""
        async with pg_manager.get_session() as session:
            try:
                stmt = select(TranslatorsGroup.name, TranslatorsGroup.siglas)
                res = await session.execute(stmt)
                return {row[0].lower(): row[1] for row in res.all() if row[0] and row[1]}
            except Exception as e:
                logger.error(f"Error fetching translator siglas: {e}")
                return {}

    @staticmethod
    async def get_series_volumes(series_hash: str, limit: int | None = None, offset: int = 0) -> list[dict[str, Any]]:
        """Retorna los volúmenes de una serie agrupada (Async). Validado con Pydantic."""
        async with pg_manager.get_session() as session:
            try:
                # Use correlated subquery for download counts to avoid grouping issues with selectinload
                dl_subquery = (
                    select(func.count(UserDownload.id))
                    .where(UserDownload.book_hash == LocalBook.book_hash)
                    .correlate(LocalBook)
                    .scalar_subquery()
                )

                stmt = (
                    select(LocalBook, dl_subquery.label("download_count"))
                    .options(selectinload(LocalBook.series))
                    .where(LocalBook.series_hash == series_hash)
                    .order_by(LocalBook.volume.asc(), LocalBook.id.asc())
                )

                if limit:
                    stmt = stmt.offset(offset).limit(limit)

                res = await session.execute(stmt)
                rows = res.all()

                # Get translator siglas mapping
                sigla_map = await LibraryService.get_translator_siglas_map()

                results = []
                for row in rows:
                    b = row[0]
                    dl_count = row[1] or 0

                    b_dict = b.to_dict()
                    # Ensure series name is present for DTO consistency
                    if not b_dict.get("series"):
                        b_dict["series"] = b_dict.get("title")

                    # Add translator siglas if available
                    tr = b_dict.get("translator")
                    if tr:
                        b_dict["translator_siglas"] = sigla_map.get(tr.lower())

                    dto = BookDTO(**b_dict, download_count=dl_count, coverUrl=b.cover_medium or b.cover_low)
                    results.append(dto.model_dump())

                return results
            except Exception as e:
                logger.error(f"[LibraryService.get_series_volumes] Error: {e}", exc_info=True)
                return []

    @staticmethod
    async def get_series_metadata(series_hash: str) -> SeriesMetadata | None:
        """Obtiene la metadata de una serie por su hash (Async)."""
        return await series_repo.get_by_hash(series_hash)

    @staticmethod
    async def get_series_total_downloads(series_hash: str) -> int:
        """Calcula el total de descargas de todos los libros de una serie."""
        if not series_hash:
            return 0
        async with pg_manager.get_session() as session:
            try:
                # Use series_hash column directly if it exists, fallback to book counts if not
                if hasattr(UserDownload, "series_hash"):
                    stmt = select(func.count(UserDownload.id)).where(UserDownload.series_hash == series_hash)
                else:
                    # Fallback: Count by book hashes if series_hash is missing from model
                    # This is a safer backup
                    stmt = select(func.count(UserDownload.id)).where(
                        UserDownload.book_hash.in_(
                            select(LocalBook.book_hash).where(LocalBook.series_hash == series_hash)
                        )
                    )

                res = await session.execute(stmt)
                return res.scalar() or 0
            except Exception as e:
                logger.error(f"Error calculating total downloads for series {series_hash}: {e}")
                return 0

    @staticmethod
    async def get_book_by_id(book_id: int) -> dict[str, Any] | None:
        """Busca un libro por su ID delegando al repositorio."""
        book = await book_repo.get_by_id(book_id)
        if not book:
            return None

        # Conteo de descargas se puede añadir al DTO si es necesario
        cover_url = book.cover_medium or book.cover_low or book.cover_original
        b_dict = book.to_dict()

        dto = BookDTO(**b_dict, download_count=0, coverUrl=cover_url)
        return dto.model_dump()

    @staticmethod
    async def update_book_metadata(book_id: int, updates: dict[str, Any]) -> bool:
        """Actualiza metadatos de un libro y recalcula el hash de serie."""
        async with pg_manager.get_session() as session:
            try:
                stmt = select(LocalBook).options(selectinload(LocalBook.series)).where(LocalBook.id == book_id)
                result = await session.execute(stmt)
                book = result.scalar_one_or_none()

                if not book:
                    return False

                # Update allowed fields
                # Metadata updates that now live in SeriesMetadata are handled via series_hash re-calculation
                # title, volume, romaji_title, english_title, book_hash are still in LocalBook
                if "title" in updates:
                    book.title = updates["title"]
                if "volume" in updates:
                    try:
                        book.volume = float(updates["volume"])
                    except (ValueError, TypeError):
                        pass
                if "romaji_title" in updates:
                    book.romaji_title = updates["romaji_title"]
                if "english_title" in updates:
                    book.english_title = updates["english_title"]
                if "isbn" in updates:
                    book.isbn = updates["isbn"]

                # Recalculate Series Hash to regroup
                from utils.helpers import generate_series_hash

                series_name = updates.get("series") or (book.series.series_name if book.series else book.title)
                author_val = updates.get("author") or (book.series.author if book.series else "Unknown")
                bt_val = updates.get("book_type") or (book.series.book_type if book.series else "Light Novel")

                book.series_hash = generate_series_hash(series=series_name, author=author_val, book_type=bt_val)

                await session.commit()
                return True
            except Exception as e:
                logger.error(f"[LibraryService.update_book_metadata] Error: {e}")
                return False

    @staticmethod
    async def get_regroup_suggestions(threshold: float = 0.8) -> list[dict[str, Any]]:
        """
        Analiza libros sin serie o con series diferentes y sugiere agrupaciones
        basadas en similitud de títulos y autor.
        """
        async with pg_manager.get_session() as session:
            try:
                # 1. Obtener libros sospechosos (sin series o series con 1 solo volumen)
                # Esta consulta simplificada obtiene libros sin serie asignda explícitamente
                stmt = (
                    select(LocalBook)
                    .options(selectinload(LocalBook.series))
                    .outerjoin(SeriesMetadata, LocalBook.series_metadata_id == SeriesMetadata.id)
                    .where(LocalBook.series_metadata_id.is_(None))
                    .order_by(LocalBook.title)
                )

                result = await session.execute(stmt)
                books = result.scalars().all()

                # 2. Agrupamiento lógico simple en memoria (Python)
                from difflib import SequenceMatcher

                groups = []
                used_ids = set()

                for i, book_a in enumerate(books):
                    if book_a.id in used_ids:
                        continue

                    current_group = [book_a]
                    used_ids.add(book_a.id)

                    for _j, book_b in enumerate(books[i + 1 :], start=i + 1):
                        if book_b.id in used_ids:
                            continue

                        # Mismo autor es un requisito fuerte
                        author_a = book_a.series.author if book_a.series else None
                        author_b = book_b.series.author if book_b.series else None
                        if author_a and author_b and author_a.lower() != author_b.lower():
                            continue

                        # Similitud de título
                        similarity = SequenceMatcher(None, book_a.title, book_b.title).ratio()
                        if similarity >= threshold:
                            current_group.append(book_b)
                            used_ids.add(book_b.id)

                    if len(current_group) > 1:
                        # Sugerencia encontrada
                        common_title = current_group[0].title
                        # Intentar extraer parte común
                        match = SequenceMatcher(
                            None, current_group[0].title, current_group[1].title
                        ).find_longest_match(
                            0,
                            len(current_group[0].title),
                            0,
                            len(current_group[1].title),
                        )
                        suggested_name = current_group[0].title[match.a : match.a + match.size].strip(" -:volume")

                        groups.append(
                            {
                                "suggested_series": suggested_name or common_title,
                                "confidence": "high",
                                "books": [b.to_dict() for b in current_group],
                            }
                        )

                return groups
            except Exception as e:
                logger.error(f"[LibraryService.get_regroup_suggestions] Error: {e}")
                return []

    @staticmethod
    async def get_books_without_series(limit: int = 100) -> list[dict[str, Any]]:
        """Retorna una lista simple de libros que no tienen serie asignada."""
        async with pg_manager.get_session() as session:
            try:
                stmt = (
                    select(LocalBook)
                    .options(selectinload(LocalBook.series))
                    .where(LocalBook.series_metadata_id.is_(None))
                    .order_by(LocalBook.indexed_at.desc())
                    .limit(limit)
                )

                result = await session.execute(stmt)
                books = result.scalars().all()
                return [b.to_dict() for b in books]
            except Exception as e:
                logger.error(f"Error fetching orphaned books: {e}")
                return []

    @staticmethod
    async def get_recent_books(page: int = 1, items_per_page: int = 10) -> dict[str, Any]:
        """
        Obtiene los libros añadidos recientemente delegando al repositorio.
        """
        return await book_repo.get_recent_books(page=page, items_per_page=items_per_page)

    @staticmethod
    async def get_catalog(
        source_id: int | None = None,
        folder: str | None = None,
        series_hash: str | None = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "alpha",
        use_random_covers: bool = True,
    ) -> dict[str, Any]:
        """
        Navega por el catálogo agrupando por series_hash o mostrando volúmenes (Async).
        """
        async with pg_manager.get_session() as session:
            try:
                if series_hash:
                    stmt = (
                        select(LocalBook)
                        .options(selectinload(LocalBook.series))
                        .where(LocalBook.series_hash == series_hash)
                        .order_by(LocalBook.volume.asc())
                    )
                    res = await session.execute(stmt)
                    books = res.scalars().all()
                    items = [b.to_dict() for b in books]
                    return {"items": items, "total": len(items), "type": "volumes"}

                # Root or folder navigation: Use SeriesMetadata with download count
                dl_subquery = (
                    select(func.count(UserDownload.id))
                    .where(UserDownload.series_hash == SeriesMetadata.series_hash)
                    .correlate(SeriesMetadata)
                    .scalar_subquery()
                )

                stmt = select(SeriesMetadata, dl_subquery.label("download_count"))

                if source_id:
                    stmt = stmt.join(LocalBook).where(LocalBook.source_id == source_id).distinct()

                # Case-insensitive sort for series name
                stmt = stmt.order_by(func.lower(SeriesMetadata.series_name).asc())

                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_items = (await session.execute(count_stmt)).scalar() or 0

                start = (page - 1) * page_size
                stmt = stmt.offset(start).limit(page_size)

                res = await session.execute(stmt)
                rows = res.all()

                items = []
                for row in rows:
                    s = row[0]
                    dl_count = row[1] or 0

                    items.append(
                        {
                            "id": f"series_{s.series_hash}",
                            "title": s.series_name,
                            "series_name": s.series_name,
                            "series_spanish": s.series_spanish,
                            "series_english": s.series_english,
                            "is_folder": True,
                            "numBooks": s.book_count,
                            "book_count": s.book_count,
                            "book_type": s.book_type,
                            "download_count": dl_count,
                            "cover": s.cover_url or "/book-placeholder.jpg",
                            "series_hash": s.series_hash,
                        }
                    )

                return {
                    "items": items,
                    "total": total_items,
                    "page": page,
                    "totalPages": (total_items + page_size - 1) // page_size,
                    "type": "series",
                }

            except Exception as e:
                logger.error(f"[LibraryService.get_catalog] Error: {e}")
                return {"items": [], "total": 0}

    @staticmethod
    async def get_genres() -> list[str]:
        """Obtiene la lista de géneros únicos (procedente de la columna tags)."""
        async with pg_manager.get_session() as session:
            try:
                # Usamos SQL puro con cast explícito para máxima compatibilidad
                stmt = text(
                    "SELECT DISTINCT jsonb_array_elements_text(tags::jsonb) FROM series WHERE tags IS NOT NULL ORDER BY 1"
                )
                res = await session.execute(stmt)
                return [r[0] for r in res.all() if r[0]]
            except Exception as e:
                logger.error(f"Error fetching genres: {e}")
                return []

    @staticmethod
    async def get_authors(page: int = 1, page_size: int = 10) -> dict[str, Any]:
        """Obtiene la lista de autores únicos paginada."""
        async with pg_manager.get_session() as session:
            try:
                # Count total authors
                count_stmt = select(func.count(func.distinct(SeriesMetadata.author))).where(SeriesMetadata.author != "")
                total = (await session.execute(count_stmt)).scalar() or 0

                # Fetch paginated authors
                stmt = (
                    select(func.distinct(SeriesMetadata.author))
                    .where(SeriesMetadata.author != "")
                    .order_by(SeriesMetadata.author.asc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
                res = await session.execute(stmt)
                authors = [r[0] for r in res.all() if r[0]]

                return {"items": authors, "total": total}
            except Exception as e:
                logger.error(f"Error fetching authors: {e}")
                return {"items": [], "total": 0}

    @staticmethod
    async def get_series_by_tag(tag: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        """Obtiene series filtradas por un tag específico."""
        async with pg_manager.get_session() as session:
            try:
                stmt = select(SeriesMetadata).where(SeriesMetadata.tags.contains([tag]))

                count_stmt = select(func.count()).select_from(stmt.subquery())
                total = (await session.execute(count_stmt)).scalar() or 0

                stmt = stmt.order_by(SeriesMetadata.series_name.asc()).offset((page - 1) * page_size).limit(page_size)
                res = await session.execute(stmt)
                series = res.scalars().all()

                items = []
                for s in series:
                    items.append(
                        {
                            "id": f"series_{s.series_hash}",
                            "title": s.series_name,
                            "series_hash": s.series_hash,
                            "is_folder": True,
                            "cover": s.cover_url,
                        }
                    )

                return {"items": items, "total": total}
            except Exception as e:
                logger.error(f"Error filtering series by tag: {e}")
                return {"items": [], "total": 0}

    @staticmethod
    async def get_series_by_author(author: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        """Obtiene series filtradas por autor."""
        async with pg_manager.get_session() as session:
            try:
                stmt = select(SeriesMetadata).where(SeriesMetadata.author.ilike(f"%{author}%"))

                count_stmt = select(func.count()).select_from(stmt.subquery())
                total = (await session.execute(count_stmt)).scalar() or 0

                stmt = stmt.order_by(SeriesMetadata.series_name.asc()).offset((page - 1) * page_size).limit(page_size)
                res = await session.execute(stmt)
                series = res.scalars().all()

                items = []
                for s in series:
                    items.append(
                        {
                            "id": f"series_{s.series_hash}",
                            "title": s.series_name,
                            "series_hash": s.series_hash,
                            "is_folder": True,
                            "cover": s.cover_url,
                        }
                    )

                return {"items": items, "total": total}
            except Exception as e:
                logger.error(f"Error filtering series by author: {e}")
                return {"items": [], "total": 0}

    @staticmethod
    async def find_ai_series_duplicates() -> list[dict[str, Any]]:
        """
        Escanea la biblioteca en busca de series con nombres similares (English/Spanish)
        pero con hashes distintos, indicando posibles duplicados.
        Utiliza procesamiento paralelo para evitar timeouts HTTP.
        """
        async with pg_manager.get_session() as session:
            try:
                # 1. Obtener todas las series
                stmt = select(SeriesMetadata).order_by(SeriesMetadata.author, SeriesMetadata.series_name)
                res = await session.execute(stmt)
                series_list = res.scalars().all()

                import asyncio
                from difflib import SequenceMatcher

                from services.ai_service import AIService

                suggestions = []
                # Pares de candidatos (s1, s2)
                candidates = []
                processed_pairs = set()

                # Agrupar por autor para optimizar
                author_map: dict[str, list[SeriesMetadata]] = {}
                for s in series_list:
                    auth = (s.author or "Unknown").lower().strip()
                    if auth not in author_map:
                        author_map[auth] = []
                    author_map[auth].append(s)

                logger.info(f"🔍 Identificando candidatos de duplicados entre {len(series_list)} series.")

                for _auth, group in author_map.items():
                    if len(group) < 2:
                        continue

                    for i, s1 in enumerate(group):
                        for s2 in group[i + 1 :]:
                            pair_id = tuple(sorted([s1.series_hash, s2.series_hash]))
                            if pair_id in processed_pairs:
                                continue
                            processed_pairs.add(pair_id)

                            # Heurística inicial (SequenceMatcher)
                            n1_en = (s1.series_english or s1.series_name or "").lower()
                            n1_es = (s1.series_spanish or "").lower()
                            n2_en = (s2.series_english or s2.series_name or "").lower()
                            n2_es = (s2.series_spanish or "").lower()

                            similarities = [
                                SequenceMatcher(None, n1_en, n2_en).ratio(),
                                SequenceMatcher(None, n1_es, n2_es).ratio() if n1_es and n2_es else 0,
                                SequenceMatcher(None, n1_en, n2_es).ratio() if n1_en and n2_es else 0,
                                SequenceMatcher(None, n1_es, n2_en).ratio() if n1_es and n2_en else 0,
                            ]
                            max_sim = max(similarities)

                            if max_sim > 0.7:
                                candidates.append((s1, s2, max_sim))

                if not candidates:
                    return []

                # Ordenar candidatos por similitud para procesar los más probables primero
                candidates.sort(key=lambda x: x[2], reverse=True)

                # 2. Procesar candidatos con IA en paralelo (con límite de concurrencia)
                # Limitamos a 8 llamadas simultáneas para no saturar cuota/memoria
                semaphore = asyncio.Semaphore(8)
                max_ai_calls = 100
                candidates_to_process = candidates[:max_ai_calls]

                logger.info(
                    f"🤖 Procesando {len(candidates_to_process)} candidatos con IA en paralelo (Threshold: 0.7, Max Calls: {max_ai_calls})..."
                )

                async def check_pair(s1, s2, sim):
                    async with semaphore:
                        try:
                            # Timeout individual de 30s para evitar bloqueos
                            async with asyncio.timeout(30):
                                logger.debug(
                                    f"IA analizando: '{s1.series_name}' vs '{s2.series_name}' (sim: {sim:.2f})"
                                )
                                ai_result = await AIService.analyze_potential_merge(s1.to_dict(), s2.to_dict())
                            if ai_result and ai_result.get("is_same"):
                                logger.info(
                                    f"✅ IA confirmó duplicado: '{s1.series_name}' == '{s2.series_name}' (Conf: {ai_result.get('confidence')})"
                                )
                                return {
                                    "series_a": {
                                        "hash": s1.series_hash,
                                        "name": s1.series_name,
                                        "english": s1.series_english,
                                        "spanish": s1.series_spanish,
                                        "author": s1.author,
                                        "count": s1.book_count,
                                    },
                                    "series_b": {
                                        "hash": s2.series_hash,
                                        "name": s2.series_name,
                                        "english": s2.series_english,
                                        "spanish": s2.series_spanish,
                                        "author": s2.author,
                                        "count": s2.book_count,
                                    },
                                    "reason": ai_result.get("reason"),
                                    "confidence": ai_result.get("confidence"),
                                    "suggested_name": ai_result.get("suggested_main_name"),
                                }
                        except asyncio.TimeoutError:
                            logger.warning(f"⏰ Timeout IA para: '{s1.series_name}' vs '{s2.series_name}'")
                        except Exception as inner_e:
                            logger.error(f"Error checking pair {s1.series_name}/{s2.series_name}: {inner_e}")
                        return None

                tasks = [check_pair(c[0], c[1], c[2]) for c in candidates_to_process]
                results = await asyncio.gather(*tasks)

                # Filtrar resultados válidos
                suggestions = [r for r in results if r is not None]

                # 3. Persistir propuestas en la base de datos
                if suggestions:
                    for sug in suggestions:
                        hash_a = sug["series_a"]["hash"]
                        hash_b = sug["series_b"]["hash"]

                        # Crear objeto de propuesta compatible con handle_ai_apply_merge
                        proposal_data = {
                            "series_a": sug["series_a"],
                            "series_b": sug["series_b"],
                            "reason": sug["reason"],
                            "confidence": sug["confidence"],
                            "suggested_main_name": sug["suggested_name"],
                            "suggested_spanish_name": sug["suggested_name"],  # Fallback
                        }

                        # Verificar si ya existe una propuesta pendiente para este par
                        exists_stmt = select(MetadataProposal).where(
                            and_(
                                MetadataProposal.series_hash == hash_a,
                                MetadataProposal.secondary_hash == hash_b,
                                MetadataProposal.status == "pending",
                                MetadataProposal.type == "merge",
                            )
                        )
                        existing_res = await session.execute(exists_stmt)
                        if not existing_res.scalar():
                            new_prop = MetadataProposal(
                                series_hash=hash_a,
                                secondary_hash=hash_b,
                                proposal_data=proposal_data,
                                type="merge",
                                status="pending",
                                created_at=datetime.utcnow(),
                            )
                            session.add(new_prop)

                    await session.commit()
                    logger.info(f"✅ Se guardaron {len(suggestions)} propuestas de fusión en la base de datos.")

                logger.info(f"🏁 Escaneo finalizado. Encontradas {len(suggestions)} sugerencias.")
                return suggestions

            except Exception as e:
                logger.error(f"[LibraryService.find_ai_series_duplicates] Error: {e}", exc_info=True)
                return []

    @staticmethod
    async def merge_series(target_hash: str, source_hash: str, new_name: str = None) -> bool:
        """Fusiona source_hash dentro de target_hash."""
        async with pg_manager.get_session() as session:
            try:
                # 1. Actualizar libros
                stmt_books = text("UPDATE books SET series_hash = :t WHERE series_hash = :s")
                await session.execute(stmt_books, {"t": target_hash, "s": source_hash, "n": new_name})

                # 2. Borrar metadata vieja de source
                stmt_del = text("DELETE FROM series WHERE series_hash = :s")
                await session.execute(stmt_del, {"s": source_hash})

                # 3. Actualizar nombre de target
                if new_name:
                    stmt_upd = text("UPDATE series SET title_raw = :n WHERE series_hash = :h")
                    await session.execute(stmt_upd, {"n": new_name, "h": target_hash})

                await session.commit()
                return True
            except Exception as e:
                logger.error(f"Error merging series: {e}")
                return False
