import logging
from typing import Any

from sqlalchemy import text

from models.library_models import ArchivedSeries, LocalBook, MetadataProposal, SeriesMetadata
from services.ai_service import AIService
from utils.helpers import generar_slug_from_meta, parse_metadata_from_title

logger = logging.getLogger(__name__)


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
    def get_or_create_series(cls, session: Any, book: LocalBook) -> SeriesMetadata:
        """
        Obtiene o crea una entrada en SeriesMetadata para el libro.
        Normaliza campos comunes de la serie.
        """
        extracted = getattr(book, "extracted_data", {})
        series = session.query(SeriesMetadata).filter_by(series_hash=book.series_hash).first()

        if not series:
            # Para creación inicial, preservar caracteres especiales del título original
            # Usar el título del libro como fallback si el extraído pierde caracteres importantes
            book_title = book.title or ""
            extracted_series = extracted.get("series") or book.series_english or ""

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
                series_spanish=book.series_spanish,
                series_english=book.series_english,
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
                book_count=0,
            )
            # Generar slug usando el objeto recién creado (que ya tiene series_name)
            generated_slug = generar_slug_from_meta(series.to_dict())

            # Preservar slug manual vs auto-generado (aunque sea creación inicial)
            should_preserve_slug, slug_reason = SeriesScanner._should_preserve_current_slug(
                "", generated_slug, book.series_hash
            )

            if should_preserve_slug:
                # Para creación inicial, no hay slug actual, así que usamos el generado
                series.slug = generated_slug
                logger.info(f"📝 Slug inicial generado: {generated_slug}")
            else:
                # Si hubiera existido un slug manual, se preservaría
                series.slug = generated_slug
                logger.info(f"📝 Slug inicial (sin previo): {generated_slug}")

            session.add(series)
            session.flush()
            logger.info(f"🆕 Nueva serie detectada: {series.series_name}")
        else:
            # Sincronizar campos PERO preservar modificaciones manuales del AI Hub
            current_name = series.series_name or ""
            extracted_name = extracted.get("series") or book.series_english or book.title

            # Usar lógica inteligente para decidir si preservar
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

            if book.series_spanish and series.series_spanish != book.series_spanish:
                series.series_spanish = book.series_spanish

            if book.series_english and series.series_english != book.series_english:
                series.series_english = book.series_english

            # Preservar slug manual vs auto-generado
            current_slug = series.slug or ""
            new_slug = generar_slug_from_meta(series.to_dict())

            # Solo actualizar slug si parece auto-generado o está vacío
            should_update_slug = (
                not current_slug  # Vacío
                or len(str(current_slug)) > 40  # Hash residual muy largo
                or current_slug == str(book.series_hash)[:40]  # Igual al hash (auto-gen)
            )

            if should_update_slug:
                series.slug = new_slug
                logger.info(f"📝 Actualizado slug (auto-generado): {current_slug} → {new_slug}")
            else:
                logger.info(f"🔒 Preservado slug manual: {current_slug}")

            book_type = extracted.get("book_type")
            if book_type and series.book_type != book_type:
                series.book_type = book_type

            book_publisher = extracted.get("publisher") or book.publisher
            if book_publisher and series.publisher != book_publisher:
                series.publisher = book_publisher

            # PORTADA: Usar la del volumen 1
            if book.cover_low or book.cover_medium:
                if book.volume == 1 or not series.cover_url:
                    series.cover_url = book.cover_low or book.cover_medium

        return series

    @staticmethod
    def _should_preserve_current_name(current_name: str, extracted_name: str) -> tuple[bool, str]:
        """
        Determina si se debe preservar el nombre actual de la serie.
        Retorna (should_preserve, reason).
        """
        if not current_name:
            return False, "vacío"

        if current_name == extracted_name:
            return True, "idéntico"

        # Preservar si el actual tiene caracteres especiales que el extraído no tiene
        special_chars = [":", "!", "?", "...", "—", "[", "]", "(", ")", "&", "%", "#", "@", "*", "+"]
        has_special_current = any(char in current_name for char in special_chars)
        has_special_extracted = any(char in extracted_name for char in special_chars)

        if has_special_current and not has_special_extracted:
            return True, f"preservar carácter especial: {[c for c in special_chars if c in current_name][0]}"

        # Preservar si el actual es significativamente más largo (edición manual)
        if len(current_name) > len(extracted_name) + 5:
            return True, "preservar título extendido manual"

        # Preservar si el actual tiene formato complejo (mix de mayúsculas/minúsculas, números)
        has_complex_format = (
            any(c.isupper() for c in current_name if c.isalpha())
            and any(c.islower() for c in current_name if c.isalpha())
            and any(c.isdigit() for c in current_name)
        )
        if has_complex_format and not any(c.isupper() for c in extracted_name if c.isalpha()):
            return True, "preservar formato complejo manual"

        return False, "auto-generado o mejorable"

    @staticmethod
    def _should_preserve_current_slug(current_slug: str, new_slug: str, series_hash: str) -> tuple[bool, str]:
        """
        Determina si se debe preservar el slug actual.
        Retorna (should_preserve, reason).
        """
        if not current_slug:
            return False, "vacío"

        if current_slug == new_slug:
            return True, "idéntico"

        # Preservar si el actual no parece auto-generado
        # Los slugs auto-generados suelen ser hashes o muy simples
        is_auto_generated = (
            current_slug == str(series_hash)[:40]  # Igual al hash
            or len(current_slug) > 40  # Hash residual muy largo
            or (len(current_slug) < 5 and current_slug.replace("_", "").isalnum())  # Muy corto y solo alfanumérico
        )

        if not is_auto_generated:
            return True, "slug manual detectado"

        return False, "auto-generado o mejorable"

    @staticmethod
    def sync_series_metadata(session: Any, series_hash: str):
        """
        Consolida la metadata de una serie basándose en todos sus volúmenes.
        """
        series = session.query(SeriesMetadata).filter_by(series_hash=series_hash).first()
        if not series:
            return

        books = session.query(LocalBook).filter_by(series_hash=series_hash).all()
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
            session.delete(series)
            return

        if not series.series_spanish:
            for b in books:
                if hasattr(b, "series_spanish") and b.series_spanish:
                    series.series_spanish = b.series_spanish
                    break

        if not series.series_english:
            for b in books:
                if hasattr(b, "series_english") and b.series_english:
                    series.series_english = b.series_english
                    break

        # Completar o corregir SLUG solo si es nulo o es un hash largo (SHA256 de 64 chars)
        # Una vez que tiene un slug humano (ej: "slayers"), no se toca más.
        if books and (not series.slug or len(str(series.slug)) > 40):
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
                res = session.execute(backlog_query, {"limit": needed})
                for row in res:
                    candidates.append(row[0])

            processed_count = 0
            for s_hash in candidates:
                if processed_count >= SCAN_LIMIT:
                    break

                exists_pending = session.query(MetadataProposal).filter_by(series_hash=s_hash, status="pending").first()
                reviewed = session.execute(
                    text("SELECT 1 FROM ai_learning_feedback WHERE series_hash = :h LIMIT 1"),
                    {"h": s_hash},
                ).first()

                if not exists_pending and not reviewed:
                    current_s = session.query(SeriesMetadata).filter_by(series_hash=s_hash).first()
                    current_name = current_s.series_name if current_s else "Serie Desconocida"
                    series_books = session.query(LocalBook).filter_by(series_hash=s_hash).all()

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
                                session.commit()
                                processed_count += 1
                        except Exception as ae:
                            logger.warning(f"Error IA para {s_hash}: {ae}")
        except Exception as e:
            logger.warning(f"Error AI Gardener: {e}")
