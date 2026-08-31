import re
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import selectinload

from models.library import (
    ArchivedSeries,
    Demographic,
    Genre,
    LocalBook,
    MetadataProposal,
    SeriesAlias,
    SeriesMetadata,
)
from services.ai_service import AIService
from services.scanner.scanner_helpers import ScannerHelpers
from utils.helpers import generar_slug_from_meta, normalize_demographics_list
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
    async def get_or_create_series(
        cls, session: Any, book: LocalBook, skip_ai: bool = False
    ) -> SeriesMetadata:
        """
        Obtiene o crea una entrada en SeriesMetadata para el libro.
        Usa los datos pre-extraídos de 'book.extracted_data'.
        """
        identity = getattr(book, "extracted_data", {})
        series_hash = (
            identity.get("series_hash")
            or getattr(book, "series_id", None)
            or cls.generate_series_hash(
                series_name=identity.get("series") or "Unknown",
                author=identity.get("author") or "Unknown",
                book_type=identity.get("book_type") or "Light Novel",
            )
        )

        # 1. Búsqueda por Hash directo
        stmt = (
            select(SeriesMetadata)
            .options(
                selectinload(SeriesMetadata.genres),
                selectinload(SeriesMetadata.demographics),
                selectinload(SeriesMetadata.aliases),
            )
            .where(SeriesMetadata.series_hash == series_hash)
        )
        result = await session.execute(stmt)
        series = result.scalars().first()

        candidate_titles = {
            t.strip()
            for t in [
                identity.get("series"),
                identity.get("series_spanish"),
                identity.get("series_english"),
                identity.get("romaji_title"),
                book.series_spanish,
                book.series_english,
                book.romaji_title,
            ]
            if t and isinstance(t, str) and len(t.strip()) > 1
        }

        # 2. Búsqueda por Tabla de Alias (series_aliases)
        if not series and candidate_titles:
            alias_stmt = (
                select(SeriesMetadata)
                .options(
                    selectinload(SeriesMetadata.genres),
                    selectinload(SeriesMetadata.demographics),
                    selectinload(SeriesMetadata.aliases),
                )
                .join(SeriesAlias, SeriesMetadata.id == SeriesAlias.series_id)
                .where(
                    func.lower(SeriesAlias.alias).in_(
                        [t.lower() for t in candidate_titles]
                    )
                )
                .limit(1)
            )
            alias_res = await session.execute(alias_stmt)
            series = alias_res.scalars().first()

        # 3. Búsqueda por Coincidencia de Slug Normalizado
        if not series and candidate_titles:
            candidate_slugs = {
                generar_slug_from_meta({"series": t}) for t in candidate_titles if t
            }
            candidate_slugs.discard("")
            if candidate_slugs:
                slug_stmt = (
                    select(SeriesMetadata)
                    .options(
                        selectinload(SeriesMetadata.genres),
                        selectinload(SeriesMetadata.demographics),
                        selectinload(SeriesMetadata.aliases),
                    )
                    .where(SeriesMetadata.slug.in_(list(candidate_slugs)))
                    .limit(1)
                )
                slug_res = await session.execute(slug_stmt)
                series = slug_res.scalars().first()

        from services.scanner.slug_manager import SlugManager

        if not series:
            series_name = identity.get("series") or "Unknown"
            if series_name.strip().lower() in ("volumen único", "volumen unico", "volumen_unico", "unknown", ""):
                series_name = (
                    identity.get("series_spanish")
                    or identity.get("series_english")
                    or identity.get("title")
                    or "Unknown"
                )

            # Limpiar sufijos de volumen del nombre de la serie
            series_name = re.sub(r"\s*[-–—]\s*Volumen\s*[Úu]nico\s*$", "", series_name, flags=re.IGNORECASE).strip()

            romaji_val = identity.get("romaji_title") or series_name
            if romaji_val.strip().lower() in ("volumen único", "volumen unico", "volumen_unico"):
                romaji_val = series_name

            series = SeriesMetadata(
                id=series_hash,
                series_name=series_name,
                series_spanish=identity.get("series_spanish") or series_name,
                series_english=identity.get("series_english") or series_name,
                name=romaji_val,
                author=identity.get("author") or "Unknown",
                author_jap=identity.get("author_jap"),
                illustrator=identity.get("illustrator"),
                illustrator_jap=identity.get("illustrator_jap"),
                description=identity.get("description"),
                tags_json=identity.get("tags") or [],
                demographics_json=normalize_demographics_list(
                    identity.get("demographics") or []
                ),
                book_type=identity.get("book_type") or "Light Novel",
                publisher=identity.get("publisher") or book.publisher,
                cover_url=book.cover_low or book.cover_medium,
                book_count=0,
                rating_average=0.0,
                rating_count=0,
                genres=[],
                demographics=[],
                aliases=[],
            )
            session.add(series)

            # Relaciones Normalizadas (NUEVO)
            series.genres = await ScannerHelpers.sync_taxonomy(
                session, Genre, identity.get("tags") or []
            )
            series.demographics = await ScannerHelpers.sync_taxonomy(
                session, Demographic, series.demographics_json
            )

            series.slug = SlugManager.generate_valid_slug(series)
            logger.info(
                f"🆕 Nueva serie creada desde metadatos EPUB: {series.series_name}\n"
                f"   ├─ Español: {series.series_spanish}\n"
                f"   ├─ Inglés:  {series.series_english}\n"
                f"   └─ Romaji:  {series.name} [{series.slug}]"
            )

        else:
            # ACTUALIZACIÓN DE SERIE EXISTENTE
            if identity.get("series_spanish") and (
                not series.series_spanish or series.series_spanish == series.series_name
            ):
                series.series_spanish = identity["series_spanish"]
            if identity.get("series_english") and (
                not series.series_english or series.series_english == series.series_name
            ):
                series.series_english = identity["series_english"]
            if identity.get("romaji_title") and (
                not series.name or series.name == series.series_name
            ):
                series.name = identity["romaji_title"]

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
                not series.description
                or len(identity["description"]) > len(series.description)
            ):
                series.description = identity["description"]

            # Fusión de Tags y Demographics
            if identity.get("tags"):
                existing = set(series.tags_json or [])
                incoming = set(identity["tags"])
                if not incoming.issubset(existing):
                    series.tags_json = list(existing.union(incoming))
                    # Actualizar Relación
                    series.genres = await ScannerHelpers.sync_taxonomy(
                        session, Genre, series.tags_json
                    )

            if identity.get("demographics"):
                incoming_demo = normalize_demographics_list(identity["demographics"])
                if incoming_demo and (
                    not series.demographics_json
                    or series.demographics_json != incoming_demo
                ):
                    series.demographics_json = incoming_demo
                    # Actualizar Relación
                    series.demographics = await ScannerHelpers.sync_taxonomy(
                        session, Demographic, series.demographics_json
                    )

            # Gestión de Portada (Preferir Volumen 1)
            if book.volume == 1 and book.cover_low:
                series.cover_url = book.cover_low

        # Romaji Title Preservation/Update
        if identity.get("romaji_title") and (
            not book.romaji_title or book.romaji_title == "Unknown"
        ):
            book.romaji_title = identity["romaji_title"]

        # Enriquecimiento completo de metadatos (Spanish, English y Romaji titles)
        # Omitimos la IA proactivamente si los metadatos nativos limpios ya están completamente poblados
        has_full_native_titles = (
            series.series_spanish
            and series.series_spanish != "Unknown"
            and series.series_english
            and series.series_english != "Unknown"
            and series.name
            and series.name != "Unknown"
        )
        needs_enrichment = (
            not series.series_spanish
            or not series.series_english
            or series.series_english == series.series_name
        ) and not has_full_native_titles

        if needs_enrichment and not skip_ai:
            await cls.enrich_series_metadata(session, series, skip_ai=skip_ai)

        # Auto-registro de alias para evitar futuras duplicaciones
        await cls.sync_series_aliases(session, series, candidate_titles)

        logger.debug(f"💾 Persistiendo serie: {series.series_name} (ID: {series.id})")
        await session.flush()
        return series

    @classmethod
    async def sync_series_aliases(
        cls, session: Any, series: SeriesMetadata, candidate_titles: set[str]
    ):
        """
        Sincroniza y registra automáticamente títulos alternativos como alias de la serie.
        """
        if not candidate_titles or not series or not series.id:
            return

        all_titles = set(candidate_titles)
        if series.name:
            all_titles.add(series.name.strip())
        if series.series_spanish:
            all_titles.add(series.series_spanish.strip())
        if series.series_english:
            all_titles.add(series.series_english.strip())

        for t in all_titles:
            if not t or len(t.strip()) <= 1 or t.lower() == "unknown":
                continue

            clean_t = t.strip()
            # Verificar si ya está registrado en esta serie o en otra
            stmt = select(SeriesAlias).where(
                func.lower(SeriesAlias.alias) == clean_t.lower()
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()

            if not existing:
                alias_obj = SeriesAlias(series_id=series.id, alias=clean_t)
                session.add(alias_obj)

    @classmethod
    async def enrich_series_metadata(
        cls, session: Any, series: SeriesMetadata, skip_ai: bool = False
    ):
        """
        Enriquece una serie buscando metadatos en español, inglés y romaji/japonés.
        Usa IA avanzada de Gemini para una precisión absoluta de base de datos corporativa.
        """
        if skip_ai:
            return

        try:
            from services.ai_service import AIService

            ai_service = AIService()
            prompt = f"""
            Analiza la siguiente serie de Novela Ligera, Novela Web o Manga y proporciona sus títulos oficiales en español, inglés y romaji:

            - Título original detectado: {series.series_name}
            - Autor: {series.author or "Desconocido"}

            Necesitamos que identifiques con la mayor precisión posible:
            1. **series_spanish**: El título oficial o más popular en español (por ejemplo, "Bajo un Mismo Techo, Me Enamoré de la Prometida de Mi Difunto Hermano"). Si no existe traducción en español, pon el mismo que en inglés.
            2. **series_english**: El título oficial en inglés (por ejemplo, "Living Under the Same Roof, I Fell in Love with My Deceased Brother's Fiancée").
            3. **romaji_title**: El título original transliterado en Romaji (por ejemplo, "Ani no Konyakusha to Kurashite Iru."). Si ya está en romaji o inglés de origen, úsalo.

            Responde estrictamente en formato JSON con la siguiente estructura:
            {{
                "series_spanish": "título en español",
                "series_english": "título en inglés",
                "romaji_title": "título en romaji"
            }}
            """

            res = await ai_service._call_ai(prompt, json_mode=True)
            if res:
                import json

                from services.ai_service import AIService as AI

                raw_json = AI._extract_json_from_text(res)
                data = json.loads(raw_json)

                spanish = data.get("series_spanish")
                english = data.get("series_english")
                romaji = data.get("romaji_title")

                if spanish:
                    series.series_spanish = spanish
                if english:
                    series.series_english = english
                if romaji:
                    series.name = romaji

                # Regenerar el slug e indicar el enriquecimiento en los logs
                from services.scanner.slug_manager import SlugManager

                series.slug = SlugManager.generate_valid_slug(series)

                logger.info(
                    f"🤖 Serie Enriquecida por IA: {series.series_name}\n"
                    f"   ├─ Español: {series.series_spanish}\n"
                    f"   ├─ Inglés:  {series.series_english}\n"
                    f"   └─ Romaji:  {series.name} [{series.slug}]"
                )
        except Exception as e:
            logger.error(f"❌ Error en enrich_series_metadata: {e}")

    @classmethod
    async def sync_series_metadata(cls, session: Any, series_hash: str):
        """
        Consolida la metadata de una serie basándose en todos sus volúmenes.
        """
        stmt = (
            select(SeriesMetadata)
            .options(
                selectinload(SeriesMetadata.genres),
                selectinload(SeriesMetadata.demographics),
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
                selectinload(LocalBook.demographics),
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
        all_demographics = []
        all_genres = set()
        for b in books:
            if b.demographics:
                for d in b.demographics:
                    all_demographics.append(d.name)
            elif b.demographics_json:
                all_demographics.extend(b.demographics_json)
            if b.genres:
                for g in b.genres:
                    all_genres.add(g.name)
            elif b.tags_json:
                all_genres.update(b.tags_json)

        canonical_demo = normalize_demographics_list(
            all_demographics or series.demographics_json
        )
        if canonical_demo:
            series.demographics_json = canonical_demo
            # Sincronizar (Flush incluido)
            series.demographics = await ScannerHelpers.sync_taxonomy(
                session, Demographic, canonical_demo
            )
            logger.info(
                f"🧬 Auto-poblada demografía para {series.series_name}: {series.demographics_json}"
            )

        if all_genres:
            series.tags_json = list(all_genres)
            series.genres = await ScannerHelpers.sync_taxonomy(
                session, Genre, list(all_genres)
            )
            logger.info(
                f"🏷️ Auto-poblados géneros para {series.series_name}: {series.tags_json}"
            )

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
                    SELECT b.series_id
                    FROM books b
                    WHERE b.series_id NOT IN (SELECT series_hash FROM ai_learning_feedback)
                      AND b.series_id NOT IN (SELECT series_hash FROM metadata_proposals WHERE status='pending')
                      AND b.series_id IS NOT NULL
                    GROUP BY b.series_id
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
                    MetadataProposal.series_hash == s_hash,
                    MetadataProposal.status == "pending",
                )
                exists_pending_res = await session.execute(exists_pending_stmt)
                exists_pending = exists_pending_res.scalar_one_or_none()

                reviewed_res = await session.execute(
                    text(
                        "SELECT 1 FROM ai_learning_feedback WHERE series_hash = :h LIMIT 1"
                    ),
                    {"h": s_hash},
                )
                reviewed = reviewed_res.first()

                if not exists_pending and not reviewed:
                    stmt_s = select(SeriesMetadata).where(
                        SeriesMetadata.series_hash == s_hash
                    )
                    res_s = await session.execute(stmt_s)
                    current_s = res_s.scalar_one_or_none()

                    current_name = (
                        current_s.series_name if current_s else "Serie Desconocida"
                    )

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
