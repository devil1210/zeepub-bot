import re
from typing import Any

from sqlalchemy import select, text

from models.library_models import ArchivedSeries, LocalBook, MetadataProposal, SeriesMetadata
from services.ai_service import AIService
from utils.helpers import generar_slug_from_meta, parse_metadata_from_title
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
        cls, session: Any, book: LocalBook, identity: dict[str, Any] | None = None, source: Any = None
    ) -> SeriesMetadata:
        """
        Obtiene o crea una entrada en SeriesMetadata para el libro.
        series_spanish y series_english viven en la tabla series; se pasan vía identity
        (extraído del EPUB/nombre de archivo) ya que Book no los almacena.
        """
        extracted = getattr(book, "extracted_data", {})

        # series_spanish/series_english vienen de identity (tabla series), no del book
        series_spanish = (identity or {}).get("series_spanish") if identity else None
        series_english = (identity or {}).get("series_english") if identity else None
        if series_english is None:
            series_english = getattr(book, "english_title", None) or extracted.get("series")

        stmt = select(SeriesMetadata).where(SeriesMetadata.series_hash == book.series_hash)
        result = await session.execute(stmt)
        series = result.scalar_one_or_none()

        if not series:
            # Para creación inicial, preservar caracteres especiales del título original
            book_title = book.title or ""
            extracted_series = extracted.get("series") or series_english or ""

            # Parsear con preservación de caracteres especiales
            parsed = parse_metadata_from_title(book_title, preserve_special_chars=True)
            final_series_name = parsed.get("series") or extracted_series

            # Detectar si el extraído pierde caracteres importantes
            special_chars = [":", "!", "?", "...", "—", "[", "]", "(", ")", "&", "%", "#", "@", "*", "+"]
            book_has_special = any(char in book_title for char in special_chars)
            extracted_has_special = any(char in extracted_series for char in special_chars)

            # Preferir el título original si el extraído pierde caracteres especiales
            if book_has_special and not extracted_has_special:
                final_series_name = book_title
                logger.info(f"🔒 Preservando título original con caracteres especiales: {book_title}")
            else:
                final_series_name = extracted_series
                logger.info(f"📝 Usando título extraído: {extracted_series}")

            series = SeriesMetadata(
                series_name=final_series_name,
                series_spanish=series_spanish,
                series_english=series_english,
                series_hash=book.series_hash,
                author=extracted.get("author") or "",
                author_jap=extracted.get("author_jap"),
                illustrator=extracted.get("illustrator"),
                illustrator_jap=extracted.get("illustrator_jap"),
                description=extracted.get("description"),
                tags=extracted.get("tags") or [],
                demographics=extracted.get("demographics"),
                book_type=extracted.get("book_type"),
                publisher=extracted.get("publisher") or book.publisher,
                cover_url=book.cover_low or book.cover_medium,
                source_id=book.source_id or (source.id if source else None),
                book_count=0,
            )
            # Generar slug usando el objeto recién creado
            generated_slug = generar_slug_from_meta(series.to_dict())

            series.slug = generated_slug
            logger.info(f"📝 Slug inicial generado: {generated_slug}")

            session.add(series)
            await session.flush()

            # Verificación Crítica de ID (v4.3.9)
            if not series.id:
                logger.error(
                    f"❌ ERROR CRÍTICO: El ID de la serie '{series.series_name}' sigue siendo None tras el flush."
                )
                # Generación forzada si falla el default de SQLAlchemy
                import uuid

                series.id = uuid.uuid4()
                await session.flush()
                logger.warning(f"⚠️ ID de serie generado manualmente: {series.id}")

            logger.info(f"🆕 Nueva serie detectada: {series.series_name} [ID: {series.id}]")
        else:
            # Sincronizar campos PERO preservar modificaciones manuales
            current_name = series.series_name or ""
            extracted_name = extracted.get("series") or series_english or book.title

            should_preserve, preserve_reason = SeriesScanner._should_preserve_current_name(current_name, extracted_name)
            should_update_name = not should_preserve

            if should_update_name:
                series.series_name = extracted_name
                logger.info(f"📝 Actualizado series_name ({preserve_reason}): {current_name} → {extracted_name}")
            else:
                logger.info(f"🔒 Preservado series_name manual ({preserve_reason}): {current_name}")

            book_author = extracted.get("author")
            if book_author and series.author != book_author:
                series.author = book_author

            book_desc = extracted.get("description")
            if book_desc and (not series.description or len(book_desc) > len(series.description)):
                series.description = book_desc

            # UNIÓN DE TAGS
            book_tags = extracted.get("tags")
            if book_tags:
                existing_tags = set(series.tags) if series.tags else set()
                new_tags = set(book_tags)
                if not new_tags.issubset(existing_tags):
                    series.tags = list(existing_tags | new_tags)

            if series_spanish is not None and series_spanish and series.series_spanish != series_spanish:
                series.series_spanish = series_spanish

            if series_english is not None and series_english and series.series_english != series_english:
                series.series_english = series_english

            # COMPLETAR ROMAJI_TITLE VACÍOS
            if not book.romaji_title or book.romaji_title.strip() == "":
                title_source = book.title or series_spanish or series_english or ""
                extracted_romaji = SeriesScanner._extract_romaji_from_title(title_source)
                if extracted_romaji:
                    book.romaji_title = extracted_romaji
                    logger.info(f"🔤 Auto-poblado romaji_title vacío: '{title_source}' -> '{extracted_romaji}'")

            # Preservar slug manual vs auto-generado
            current_slug = series.slug or ""
            new_slug = generar_slug_from_meta(series.to_dict())
            cleaned_new_slug = SeriesScanner._clean_slug_special_chars(new_slug)

            has_special_chars_slug = any(char in str(current_slug) for char in "!?#$%^&*()+=[]{}|\\:;\"'<>,/`~")

            should_update_slug = (
                not current_slug
                or len(str(current_slug)) > 40
                or current_slug == str(book.series_hash)[:40]
                or has_special_chars_slug
                or current_slug != cleaned_new_slug
            )

            if should_update_slug:
                final_slug = (
                    cleaned_new_slug if (has_special_chars_slug or current_slug != cleaned_new_slug) else new_slug
                )
                series.slug = final_slug
                logger.info(f"📝 Actualizado slug: {current_slug} → {final_slug}")
            else:
                logger.info(f"🔒 Preservado slug manual: {current_slug}")

            book_type = extracted.get("book_type")
            if book_type and series.book_type != book_type:
                series.book_type = book_type

            book_publisher = extracted.get("publisher") or book.publisher
            if book_publisher and series.publisher != book_publisher:
                series.publisher = book_publisher

            # PORTADA: Usar la del volumen 1 o si no hay ninguna
            if book.cover_low or book.cover_medium:
                if book.volume == 1 or not series.cover_url:
                    series.cover_url = book.cover_low or book.cover_medium

        return series

    @staticmethod
    def _should_preserve_current_name(current_name: str, extracted_name: str) -> tuple[bool, str]:
        if not current_name:
            return False, "vacío"
        if current_name == extracted_name:
            return True, "idéntico"
        special_chars = [":", "!", "?", "...", "—", "[", "]", "(", ")", "&", "%", "#", "@", "*", "+"]
        has_special_current = any(char in current_name for char in special_chars)
        has_special_extracted = any(char in extracted_name for char in special_chars)
        if has_special_current and not has_special_extracted:
            return True, "preservar carácter especial"
        if len(current_name) > len(extracted_name) + 5:
            return True, "preservar título extendido manual"
        return False, "auto-generado o mejorable"

    @staticmethod
    def _extract_romaji_from_title(title: str) -> str:
        if not title:
            return ""
        romaji = re.sub(r"\s+", " ", title).strip()
        return romaji if len(romaji) >= 3 else ""

    @staticmethod
    def _clean_slug_special_chars(slug: str) -> str:
        if not slug:
            return ""
        invalid_chars = "!?#$%^&*()+=[]{}|\\:;\"'<>,/`~"
        cleaned_slug = slug
        for char in invalid_chars:
            cleaned_slug = cleaned_slug.replace(char, "")
        cleaned_slug = re.sub(r"\s+", "_", cleaned_slug)
        cleaned_slug = re.sub(r"_+", "_", cleaned_slug)
        return cleaned_slug.strip("_")

    @classmethod
    async def sync_series_metadata(cls, session: Any, series_hash: str):
        """
        Consolida la metadata de una serie basándose en todos sus volúmenes.
        """
        stmt = select(SeriesMetadata).where(SeriesMetadata.series_hash == series_hash)
        result = await session.execute(stmt)
        series = result.scalar_one_or_none()

        if not series:
            return

        stmt_books = select(LocalBook).where(LocalBook.series_hash == series_hash)
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
                tags=series.tags,
                cover_url=series.cover_url,
                book_type=series.book_type,
                publisher=series.publisher,
                original_series_id=series.id,
            )
            session.add(archived_s)
            await session.delete(series)
            await session.flush()
            return

        for b in books:
            if not series.series_spanish and hasattr(b, "series_spanish") and b.series_spanish:
                series.series_spanish = b.series_spanish
            if not series.series_english and hasattr(b, "series_english") and b.series_english:
                series.series_english = b.series_english

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

        if get_setting("enable_background_ai_scan", "false").lower() != "true":
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
                        select(LocalBook).where(LocalBook.series_hash == s_hash).options(selectinload(LocalBook.series))
                    )
                    res_books = await session.execute(stmt_books)
                    series_books = res_books.scalars().all()

                    if series_books:
                        try:
                            proposal = await AIService.analyze_series_for_updates(
                                s_hash,
                                current_name,
                                [b.to_dict() for b in series_books],
                                current_s.series_spanish if current_s else None,
                            )
                            if proposal:
                                p_obj = MetadataProposal(
                                    series_hash=s_hash,
                                    proposal_data=proposal,
                                    status="pending",
                                )
                                session.add(p_obj)
                                await session.flush()
                                processed_count += 1
                        except Exception as ae:
                            logger.warning(f"Error IA para {s_hash}: {ae}")
        except Exception as e:
            logger.warning(f"Error AI Gardener: {e}")
