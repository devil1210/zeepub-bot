import logging
from typing import Any

from sqlalchemy import text

from models.library_models import ArchivedSeries, LocalBook, MetadataProposal, SeriesMetadata
from services.ai_service import AIService
from utils.helpers import generar_slug_from_meta

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
        series = session.query(SeriesMetadata).filter_by(series_hash=book.series_hash).first()

        if not series:
            series = SeriesMetadata(
                series_name=book.series or book.title,
                series_spanish=book.series_spanish,
                series_english=book.series_english,
                slug=generar_slug_from_meta(book.to_dict()),
                series_hash=book.series_hash,
                author=book.author,
                author_jap=book.author_jap,
                description=book.description,
                tags=book.tags or [],
                book_type=book.book_type,
                publisher=book.publisher,
                cover_url=book.cover_low or book.cover_medium,
                book_count=0,
            )
            session.add(series)
            session.flush()
            logger.info(f"🆕 Nueva serie detectada: {series.series_name}")
        else:
            # Sincronizar campos
            if book.author and series.author != book.author:
                series.author = book.author

            if book.description and (not series.description or len(book.description) > len(series.description)):
                series.description = book.description

            # UNIÓN DE TAGS
            if book.tags:
                existing_tags = set(series.tags) if series.tags else set()
                new_tags = set(book.tags)
                if not new_tags.issubset(existing_tags):
                    series.tags = list(existing_tags | new_tags)

            if book.series_spanish and series.series_spanish != book.series_spanish:
                series.series_spanish = book.series_spanish

            if book.series_english and series.series_english != book.series_english:
                series.series_english = book.series_english
                series.slug = generar_slug_from_meta(book.to_dict())

            if book.book_type and series.book_type != book.book_type:
                series.book_type = book.book_type

            if book.publisher and series.publisher != book.publisher:
                series.publisher = book.publisher

            # PORTADA: Usar la del volumen 1
            if book.cover_low or book.cover_medium:
                if book.volume == 1 or not series.cover_url:
                    series.cover_url = book.cover_low or book.cover_medium

        return series

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

        all_tags = set()
        for b in books:
            if b.tags:
                all_tags.update(b.tags)

        if series.tags:
            all_tags.update(series.tags)

        series.tags = list(all_tags)

        if not series.description:
            for b in books:
                if b.description:
                    series.description = b.description
                    break

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
