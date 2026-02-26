import logging
from typing import Any

from sqlalchemy import select

from config.config_settings import config
from core.db_manager_pg import pg_manager
from core.supabase_manager import supabase_manager
from models.library_models import (
    AILearningFeedback,
    LibrarySource,
    LocalBook,
    MetadataProposal,
    SeriesMetadata,
    TranslatorsGroup,
    UserDownload,
    UserRating,
)

# Optional: imports for specific bidirectional sync logic
# from core.optimized_sync_engine import optimized_sync_engine

logger = logging.getLogger(__name__)


class SyncService:
    """
    Servicio centralizado para la sincronización de datos entre la base de datos local y Supabase.
    """

    @staticmethod
    async def sync_library_to_cloud() -> dict[str, Any]:
        """
        Ejecuta la sincronización completa de la librería (Series, Libros, Ratings, etc.) hacia Supabase.
        """
        if not config.ENABLE_SUPABASE:
            return {
                "success": False,
                "message": "Supabase no está habilitado en la configuración.",
            }

        client = supabase_manager.get_client()
        if not client:
            return {"success": False, "message": "Cliente de Supabase no disponible."}

        stats = {
            "series": 0,
            "ai_proposals": 0,
            "ai_feedback": 0,
            "sources": 0,
            "books": 0,
            "ratings": 0,
            "downloads": 0,
            "groups": 0,
        }

        try:
            async with pg_manager.get_session() as session:
                # 1. Sync SeriesMetadata
                await SyncService._sync_series(session, client, stats)

                # 2. Sync AI Learning Feedback
                await SyncService._sync_feedback(session, client, stats)

                # 3. Sync AI Proposals
                await SyncService._sync_proposals(session, client, stats)

                # 4. Sync Library Sources
                await SyncService._sync_sources(session, client, stats)

                # 5. Sync Translators Groups
                await SyncService._sync_groups(session, client, stats)

                # 6. Sync Local Books
                await SyncService._sync_books(session, client, stats)

                # 7. Sync User Ratings
                await SyncService._sync_ratings(session, client, stats)

                # 8. Sync User Downloads
                await SyncService._sync_downloads(session, client, stats)

                # 9. Bidirectional Pull (Keep local up to date)
                await SyncService._pull_updates(session)

            return {
                "success": True,
                "message": "Sincronización con la nube completada exitosamente.",
                "stats": stats,
            }

        except Exception as e:
            logger.error(
                f"Error crítico en SyncService.sync_library_to_cloud: {e}",
                exc_info=True,
            )
            return {"success": False, "message": str(e)}

    # --- Private Helper Methods per Table ---

    @staticmethod
    async def _sync_series(session, client, stats):
        try:
            res = await session.execute(select(SeriesMetadata))
            series_list = res.scalars().all()
            if not series_list:
                return

            logger.info(f"Sincronizando {len(series_list)} series a Supabase...")

            # Force schema cache refresh to avoid stale column errors (PGRST204)
            try:
                client.rpc("reload_schema_cache").execute()
            except Exception:
                # Fallback: simple query to wake up connection or ignore if RPC not found
                pass

            # Upsert in small batches to avoid payload limits
            batch_size = 50
            for i in range(0, len(series_list), batch_size):
                chunk = series_list[i : i + batch_size]
                data = []
                for s in chunk:
                    data.append(
                        {
                            "series_hash": s.series_hash,
                            "series_name": s.series_name,
                            "series_spanish": s.series_spanish,
                            "author": s.author,
                            "description": s.description,
                            "tags": s.tags,
                            "demographics": s.demographics,
                            "cover_url": s.cover_url,
                            "book_type": s.book_type,
                            "publisher": s.publisher,
                            "author_jap": s.author_jap,
                            "rating_average": float(s.rating_average) if s.rating_average is not None else 0.0,
                            "rating_count": s.rating_count,
                            "book_count": s.book_count,
                            "slug": s.slug,
                            "series_english": s.series_english,
                        }
                    )
                try:
                    client.table("series_metadata").upsert(data, on_conflict="series_hash").execute()
                    stats["series"] += len(data)
                    print(f"📚 Series sincronizadas: {stats['series']}/{len(series_list)}")
                except Exception as ex:
                    logger.error(f"Error syncing series batch {i}: {ex}")

        except Exception as e:
            logger.error(f"Error en _sync_series: {e}")

    @staticmethod
    async def _sync_feedback(session, client, stats):
        try:
            res = await session.execute(select(AILearningFeedback))
            feedback_list = res.scalars().all()
            if not feedback_list:
                return

            data = [
                {
                    "series_hash": f.series_hash,
                    "original_name": f.original_name,
                    "proposed_name": f.proposed_name,
                    "final_name": f.final_name,
                    "status": f.status,
                    "ai_reason": f.ai_reason,
                    "user_reason": f.user_reason,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                }
                for f in feedback_list
            ]

            for i in range(0, len(data), 50):
                batch = data[i : i + 50]
                try:
                    client.table("ai_learning_feedback").upsert(batch).execute()
                    stats["ai_feedback"] += len(batch)
                except Exception as ex:
                    logger.error(f"Error syncing feedback batch: {ex}")
        except Exception as e:
            logger.error(f"Error en _sync_feedback: {e}")

    @staticmethod
    async def _sync_proposals(session, client, stats):
        try:
            res = await session.execute(select(MetadataProposal))
            proposals = res.scalars().all()
            if not proposals:
                return

            data = [
                {
                    "series_hash": p.series_hash,
                    "proposal_data": p.proposal_data,
                    "status": p.status,
                    "type": p.type,
                    "secondary_hash": p.secondary_hash,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "processed_at": p.processed_at.isoformat() if p.processed_at else None,
                }
                for p in proposals
            ]

            for i in range(0, len(data), 50):
                batch = data[i : i + 50]
                try:
                    client.table("metadata_proposals").upsert(batch).execute()
                    stats["ai_proposals"] += len(batch)
                except Exception as ex:
                    logger.error(f"Error syncing proposals batch: {ex}")
        except Exception as e:
            logger.error(f"Error en _sync_proposals: {e}")

    @staticmethod
    async def _sync_sources(session, client, stats):
        try:
            res = await session.execute(select(LibrarySource))
            sources = res.scalars().all()
            if not sources:
                return

            data = [
                {
                    "id": src.id,
                    "name": src.name,
                    "path": src.path,
                    "last_scanned": src.last_scanned.isoformat() if src.last_scanned else None,
                }
                for src in sources
            ]

            try:
                client.table("library_sources").upsert(data).execute()
                stats["sources"] += len(data)
            except Exception as ex:
                logger.error(f"Error syncing sources: {ex}")
        except Exception as e:
            logger.error(f"Error en _sync_sources: {e}")

    @staticmethod
    async def _sync_groups(session, client, stats):
        try:
            res = await session.execute(select(TranslatorsGroup))
            groups = res.scalars().all()
            if not groups:
                return

            data = [
                {
                    "id": g.id,
                    "name": g.name,
                    "siglas": g.siglas,
                    "type": getattr(g, "type", "fansub"),  # Safe get
                    "website": getattr(g, "website", None),
                }
                for g in groups
            ]

            try:
                # Groups table might be small enough for one batch
                client.table("translators_groups").upsert(data).execute()
                stats["groups"] += len(data)
            except Exception as ex:
                logger.error(f"Error syncing groups: {ex}")
        except Exception as e:
            logger.error(f"Error en _sync_groups: {e}")

    @staticmethod
    async def _sync_books(session, client, stats):
        try:
            res = await session.execute(select(LocalBook))
            books = res.scalars().all()
            if not books:
                return

            logger.info(f"Sincronizando {len(books)} libros...")
            data = []
            for b in books:
                data.append(
                    {
                        "book_hash": b.book_hash,
                        "series_hash": b.series_hash,
                        "title": b.title,
                        "author": b.author,
                        "volume": float(b.volume) if b.volume is not None else 0.0,
                        "book_type": b.book_type,
                        # UI fields
                        "cover_low": b.cover_low,
                        "cover_medium": b.cover_medium,
                        "cover_high": b.cover_high,
                        "cover_original": b.cover_original,
                        # Metrics
                        "rating_average": float(b.rating_average) if b.rating_average is not None else 0.0,
                        "rating_count": b.rating_count,
                        "file_size": b.file_size,
                        # Metadata
                        "description": b.description,
                        "tags": b.tags,
                        "language": b.language,
                        # Tech
                        "source_id": b.source_id,
                        "filepath": b.filepath,
                        "filename": b.filename,
                        # Extra Metadata
                        "isbn": b.isbn,
                        "asin": b.asin,
                        "word_count": b.word_count,
                        "page_count": b.page_count,
                        "reading_time": b.reading_time,
                        "epub_version": b.epub_version,
                        "modified_at_opf": b.modified_at_opf.isoformat()
                        if b.modified_at_opf and hasattr(b.modified_at_opf, "isoformat")
                        else b.modified_at_opf,
                        "layout_by": b.layout_by,
                        "translator": b.translator,
                        "spanish_title": b.spanish_title,
                        "romaji_title": b.romaji_title,
                        "english_title": b.english_title,
                        "is_uncensored": 1 if b.is_uncensored else 0,
                        "color_mode": b.color_mode,
                        "publisher": b.publisher,
                        "short_link": b.short_link,
                    }
                )

            for i in range(0, len(data), 50):
                batch = data[i : i + 50]
                try:
                    client.table("local_books").upsert(batch, on_conflict="book_hash").execute()
                    stats["books"] += len(batch)
                    if i % 250 == 0:
                        print(f"📦 Libros sincronizados: {stats['books']}/{len(data)}")
                except Exception as ex:
                    logger.error(f"Error syncing books batch {i}: {ex}")
                    print(f"❌ Error en lote {i}: {ex}")

        except Exception as e:
            logger.error(f"Error en _sync_books: {e}")

    @staticmethod
    async def _sync_ratings(session, client, stats):
        try:
            res = await session.execute(select(UserRating))
            ratings = res.scalars().all()
            if not ratings:
                return

            data = [
                {
                    "user_id": r.user_id,
                    "book_hash": r.book_hash,
                    "rating": r.rating,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in ratings
            ]

            for i in range(0, len(data), 100):
                batch = data[i : i + 100]
                try:
                    client.table("user_ratings").upsert(batch).execute()
                    stats["ratings"] += len(batch)
                except Exception as ex:
                    logger.error(f"Error syncing ratings batch: {ex}")
        except Exception as e:
            logger.error(f"Error en _sync_ratings: {e}")

    @staticmethod
    async def _sync_downloads(session, client, stats):
        try:
            res = await session.execute(select(UserDownload))
            dls = res.scalars().all()
            if not dls:
                return

            data = [
                {
                    "user_id": d.user_id,
                    "book_hash": d.book_hash,
                    "series_hash": d.series_hash,
                    "title": d.title,
                    "downloaded_at": d.downloaded_at.isoformat() if d.downloaded_at else None,
                }
                for d in dls
            ]

            for i in range(0, len(data), 100):
                batch = data[i : i + 100]
                try:
                    client.table("user_downloads").upsert(batch).execute()
                    stats["downloads"] += len(batch)
                except Exception as ex:
                    logger.error(f"Error syncing downloads batch: {ex}")
        except Exception as e:
            logger.error(f"Error en _sync_downloads: {e}")

    @staticmethod
    async def _pull_updates(session):
        try:
            from core.optimized_sync_engine import optimized_sync_engine

            logger.info("Iniciando Pull Bidireccional (Nube -> Local)...")
            # This triggers the existing optimized engine for the reverse sync
            # Note: Ensure this doesn't cause infinite loops or locks
            await optimized_sync_engine.force_sync_all()
        except ImportError:
            logger.warning("OptimizedSyncEngine not found/imported.")
        except Exception as e:
            logger.error(f"Error en _pull_updates: {e}")
