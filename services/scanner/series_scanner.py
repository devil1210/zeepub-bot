from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from models.library import ArchivedSeries, Demographic, Genre, LocalBook, MetadataProposal, SeriesMetadata
from services.ai_service import AIService
from services.scanner.scanner_helpers import ScannerHelpers
from utils.helpers import generar_slug_from_meta
from utils.logger import logger


class SeriesScanner:
    """
    Lógica especializada en la gestión de metadatos de series,
    consolidación de tags y generación de propuestas por IA.
    """

    # Géneros que son "rasgos" de edición y deben bueblear a la serie si algún volumen los tiene
    TRAIT_TAGS = {
        "Sin Censura",
        "Ilustraciones a Color",
        "Mature",
        "One-shot",
        "Spin-off",
        "Anthology",
    }

    @classmethod
    async def get_or_create_series(cls, session: Any, book: LocalBook, skip_ai: bool = False) -> SeriesMetadata:
        """
        Obtiene o crea una entrada en SeriesMetadata para el libro.
        Usa los datos pre-extraídos de 'book.extracted_data'.
        """
        identity = getattr(book, "extracted_data", {})
        series_hash = book.series_hash

        stmt = (
            select(SeriesMetadata)
            .options(
                selectinload(SeriesMetadata.genres),
                selectinload(SeriesMetadata.demographics_list),
            )
            .where(SeriesMetadata.series_hash == series_hash)
        )
        result = await session.execute(stmt)
        series = result.scalar_one_or_none()

        from services.scanner.slug_manager import SlugManager

        if not series:
            series_name = identity.get("series") or "Unknown"

            series = SeriesMetadata(
                series_name=series_name,
                series_english=series_name,
                series_spanish=None,
                series_hash=series_hash,
                author=identity.get("author") or "Unknown",
                author_jap=identity.get("author_jap"),
                illustrator=identity.get("illustrator"),
                illustrator_jap=identity.get("illustrator_jap"),
                description=identity.get("description"),
                tags_json=identity.get("tags") or [],
                demographics_json=identity.get("demographics") or [],
                book_type=identity.get("book_type") or "Light Novel",
                publisher=identity.get("publisher") or book.publisher,
                cover_url=book.cover_low or book.cover_medium,
                book_count=0,
            )

            # Relaciones Normalizadas (NUEVO)
            series.genres = await ScannerHelpers.sync_taxonomy(session, Genre, identity.get("tags") or [])
            series.demographics_list = await ScannerHelpers.sync_taxonomy(
                session, Demographic, identity.get("demographics") or []
            )

            series.slug = SlugManager.generate_valid_slug(series)
            logger.info(f"🆕 Nueva serie detectada: {series.series_name} [{series.slug}]")
            session.add(series)
            await session.flush()
        else:
            # ACTUALIZACIÓN DE SERIE EXISTENTE
            if not series.series_english:
                series.series_english = series.series_name

            # Mantenimiento de Slug
            SlugManager.update_slug_safely(series, book)

            # Actualizar campos básicos si están vacíos
            if not series.author or series.author == "Unknown":
                series.author = identity.get("author") or series.author

            if identity.get("author_jap") and not series.author_jap:
                series.author_jap = identity.get("author_jap")

            if identity.get("description") and (
                not series.description or len(identity["description"]) > len(series.description)
            ):
                series.description = identity["description"]

            # Fusión de Tags y Demographics
            if identity.get("tags"):
                existing = set(series.tags_json or [])
                incoming = set(identity["tags"])
                if not incoming.issubset(existing):
                    series.tags_json = list(existing.union(incoming))
                    # Actualizar Relación
                    series.genres = await ScannerHelpers.sync_taxonomy(session, Genre, series.tags_json)

            if identity.get("demographics"):
                existing_demo = set(series.demographics_json or [])
                incoming_demo = set(identity["demographics"])
                if not incoming_demo.issubset(existing_demo):
                    series.demographics_json = list(existing_demo.union(incoming_demo))
                    # Actualizar Relación
                    series.demographics_list = await ScannerHelpers.sync_taxonomy(
                        session, Demographic, series.demographics_json
                    )

            # Gestión de Portada (Preferir Volumen 1)
            if book.volume == 1 and book.cover_low:
                series.cover_url = book.cover_low

        # Romaji Title Preservation/Update
        if identity.get("romaji_title") and (not book.romaji_title or book.romaji_title == "Unknown"):
            book.romaji_title = identity["romaji_title"]

        # Enriquecimiento (Spanish title, etc)
        if not series.series_spanish and not skip_ai:
            await cls.enrich_series_metadata(session, series, skip_ai=skip_ai)

        await session.flush()
        return series

    @classmethod
    async def enrich_series_metadata(cls, session: Any, series: SeriesMetadata, skip_ai: bool = False):
        """
        Enriquece una serie buscando metadatos en español y otros campos.
        Usa Google Books API y/o IA como fallback.
        """
        if series.series_spanish:
            return

        from utils.helpers import get_series_spanish_from_api

        # 1. Intentar vía Google Books (Heurística rápida)
        try:
            spanish_title = await get_series_spanish_from_api(series.series_name, series.author)
            if spanish_title:
                series.series_spanish = spanish_title
                logger.info(f"✨ Enriquecido (API): {series.series_name} -> {spanish_title}")
                return
        except Exception as e:
            logger.debug(f"API Enrichment failed for {series.series_name}: {e}")

        # 2. IA Fallback (Solo si lo anterior falla, tenemos API Key y NO saltamos IA)
        if skip_ai:
            return

        try:
            from services.ai_service import AIService

            ai_service = AIService()
            prompt = f"""
            Identifica el título oficial en español de esta serie de Novela Ligera/Manga.
            Nombre: {series.series_name}
            Autor: {series.author}

            Si no hay un título oficial diferente al inglés, responde el mismo nombre.
            Responde SOLO con el nombre en un JSON:
            {{ "series_spanish": "string" }}
            """
            res = await ai_service._call_ai(prompt, json_mode=True)
            if res:
                import json

                from services.ai_service import AIService as AI

                data = json.loads(AI._extract_json_from_text(res))
                series.series_spanish = data.get("series_spanish")
                logger.info(f"🤖 Enriquecido (IA): {series.series_name} -> {series.series_spanish}")
        except Exception:
            pass

    @classmethod
    async def sync_series_metadata(cls, session: Any, series_hash: str):
        """
        Consolida la metadata de una serie basándose en todos sus volúmenes.
        """
        stmt = (
            select(SeriesMetadata)
            .options(
                selectinload(SeriesMetadata.genres),
                selectinload(SeriesMetadata.demographics_list),
            )
            .where(SeriesMetadata.series_hash == series_hash)
        )
        result = await session.execute(stmt)
        series = result.scalar_one_or_none()

        if not series:
            return

        stmt_books = (
            select(LocalBook)
            .options(
                selectinload(LocalBook.genres),
                selectinload(LocalBook.demographics_list),
            )
            .where(LocalBook.series_hash == series_hash)
        )
        res_books = await session.execute(stmt_books)
        books = res_books.scalars().all()

        if not books:
            logger.info(f"Archivando serie vacía: {series.series_name}")
            archived_s = ArchivedSeries(
                series_name=series.series_name,
                series_spanish=series.series_spanish,
                series_english=series.series_english,
                series_hash=series.series_hash,
                author=series.author,
                description=series.description,
                tags=series.tags_json,
                cover_url=series.cover_url,
                book_type=series.book_type,
                publisher=series.publisher,
                original_series_id=None,
                slug=series.slug,
            )
            session.add(archived_s)
            await session.delete(series)
            await session.flush()
            return

        # CONSOLIDAR DEMOGRAFÍA
        all_demographics = set()
        all_genres = set()
        for b in books:
            if b.demographics_list:
                for d in b.demographics_list:
                    all_demographics.add(d.name)
            if b.genres:
                for g in b.genres:
                    all_genres.add(g.name)

        if all_demographics:
            series.demographics_json = list(all_demographics)
            series.demographics_list = await ScannerHelpers.sync_taxonomy(session, Demographic, list(all_demographics))
            logger.info(f"🧬 Auto-poblada demografía para {series.series_name}: {series.demographics_json}")

        if all_genres:
            series.tags_json = list(all_genres)
            series.genres = await ScannerHelpers.sync_taxonomy(session, Genre, list(all_genres))
            logger.info(f"🏷️ Auto-poblados géneros para {series.series_name}: {series.tags_json}")

        if not series.slug or len(str(series.slug)) > 40:
            series.slug = generar_slug_from_meta(series.to_dict())

        if not series.cover_url or "_low.jpg" not in series.cover_url:
            for b in books:
                if b.cover_low:
                    series.cover_url = b.cover_low
                    break
                elif b.cover_medium:
                    series.cover_url = b.cover_medium
                    break

        series.book_count = len(books)
        ratings = [b.rating_average for b in books if b.rating_count > 0]
        if ratings:
            series.rating_average = sum(ratings) / len(ratings)
        series.rating_count = sum(b.rating_count for b in books)
        await session.flush()

    @classmethod
    async def run_ai_gardener(cls, session: Any, touched_hashes: set):
        """
        Busca series candidatas y genera propuestas de metadatos vía IA.
        """
        from services.settings_service import get_setting

        if get_setting("ai_background_maintenance", "false").lower() != "true":
            return

        try:
            candidates = list(touched_hashes)
            SCAN_LIMIT = 5

            if len(candidates) < SCAN_LIMIT:
                needed = SCAN_LIMIT - len(candidates)
                backlog_query = text("""
                    SELECT lb.series_hash
                    FROM local_books lb
                    WHERE lb.series_hash NOT IN (SELECT series_hash FROM ai_learning_feedback)
                      AND lb.series_hash NOT IN (SELECT series_hash FROM metadata_proposals WHERE status='pending')
                      AND lb.series_hash IS NOT NULL
                    GROUP BY lb.series_hash
                    HAVING COUNT(*) >= 2
                    LIMIT :limit
                """)
                res = await session.execute(backlog_query, {"limit": needed})
                for row in res:
                    candidates.append(row[0])

            processed_count = 0
            for s_hash in candidates:
                if processed_count >= SCAN_LIMIT:
                    break

                exists_pending_stmt = select(MetadataProposal).where(
                    MetadataProposal.series_hash == s_hash, MetadataProposal.status == "pending"
                )
                exists_pending_res = await session.execute(exists_pending_stmt)
                exists_pending = exists_pending_res.scalar_one_or_none()

                reviewed_res = await session.execute(
                    text("SELECT 1 FROM ai_learning_feedback WHERE series_hash = :h LIMIT 1"),
                    {"h": s_hash},
                )
                reviewed = reviewed_res.first()

                if not exists_pending and not reviewed:
                    stmt_s = select(SeriesMetadata).where(SeriesMetadata.series_hash == s_hash)
                    res_s = await session.execute(stmt_s)
                    current_s = res_s.scalar_one_or_none()

                    current_name = current_s.series_name if current_s else "Serie Desconocida"

                    from sqlalchemy.orm import selectinload

                    stmt_books = (
                        select(LocalBook)
                        .where(LocalBook.series_hash == s_hash)
                        .options(selectinload(LocalBook.series_info))
                    )
                    res_books = await session.execute(stmt_books)
                    series_books = res_books.scalars().all()

                    if series_books:
                        try:
                            ai_service = AIService()
                            proposal = await ai_service.analyze_series(
                                s_hash,
                                current_name,
                                [b.to_dict() for b in series_books],
                            )
                            if proposal:
                                p_obj = MetadataProposal(
                                    series_hash=s_hash,
                                    proposal_data=proposal,
                                    status="pending",
                                )
                                session.add(p_obj)
                                await session.commit()
                                processed_count += 1
                        except Exception as ae:
                            logger.warning(f"Error IA para {s_hash}: {ae}")
        except Exception as e:
            logger.warning(f"Error AI Gardener: {e}")
