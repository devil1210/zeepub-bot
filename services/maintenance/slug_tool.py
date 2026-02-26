import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import SeriesMetadata
from services.maintenance.base import MaintenanceTool
from utils.helpers import generar_slug_from_meta

logger = logging.getLogger(__name__)


class SlugRecalculateTool(MaintenanceTool):
    @property
    def name(self) -> str:
        return "Recalcular Slugs"

    @property
    def description(self) -> str:
        return "Recalcula todos los slugs de las series basándose en su nombre canónico."

    async def run(self, progress_callback=None, **kwargs) -> dict[str, Any]:
        clear_current = kwargs.get("clear_current", False)
        
        from config.config_settings import config

        updated_count = 0
        total_processed = 0

        # Supabase client setup
        supabase_client = None
        if config.ENABLE_SUPABASE:
            try:
                from core.supabase_manager import supabase_manager

                supabase_client = supabase_manager.get_client()
            except Exception as e:
                logger.warning(f"No se pudo conectar con Supabase para sincronización masiva: {e}")

        try:
            async with pg_manager.get_session() as session:
                stmt = select(SeriesMetadata)
                result = await session.execute(stmt)
                series_list = result.scalars().all()
                total = len(series_list)

                logger.info(f"Starting slug recalculation for {total} series (clear_current={clear_current})")

                for i, series in enumerate(series_list):
                    total_processed += 1
                    old_slug = series.slug
                    # Use a dictionary representation for generating the slug correctly per priority rules
                    new_slug = generar_slug_from_meta(series.to_dict() if hasattr(series, "to_dict") else {"series_name": series.series_name, "series_english": series.series_english, "series": series.series_name})
                    
                    if clear_current or old_slug != new_slug:
                        series.slug = new_slug
                        updated_count += 1
                        logger.debug(f"Slug updated for {series.series_name}: {old_slug} -> {new_slug}")

                        # Sync with Supabase
                        if supabase_client:
                            try:
                                supabase_client.table("series_metadata").update({"slug": new_slug}).eq(
                                    "series_hash", series.series_hash
                                ).execute()
                            except Exception as se:
                                logger.error(f"Error synchronization slug to cloud: {se}")

                    if progress_callback:
                        await progress_callback(total_processed, total, f"Actualizando {series.series_name}")

                    if total_processed % 50 == 0:
                        await session.commit()

                    await asyncio.sleep(0.001)

                await session.commit()

            return {
                "success": True,
                "processed": total_processed,
                "updated": updated_count,
                "finished_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error in SlugRecalculateTool: {e}")
            return {"success": False, "error": str(e)}
