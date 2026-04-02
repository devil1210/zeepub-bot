#!/usr/bin/env python3
"""
Actualización masiva de metadatos existentes sin re-escanear archivos
Ejecutar en VPS: docker exec zeepub-api python migrations/update_existing_metadata.py
"""

import asyncio
import logging

from sqlalchemy import text

from core.db_manager_pg import pg_manager
from utils.helpers import parse_metadata_from_title

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_existing_metadata():
    """Actualiza metadatos de series existentes usando el código corregido"""

    logger.info("🔄 Iniciando actualización de metadatos existentes...")

    async with pg_manager.get_session() as session:
        # 1. Actualizar series_name usando parse_metadata_from_title corregido
        logger.info("📝 Actualizando títulos de series...")

        # Obtener todas las series que podrían necesitar corrección
        series_query = text("""
            SELECT id, series_name, series_hash
            FROM series_metadata
            WHERE series_name IS NOT NULL
            AND LENGTH(series_name) > 0
        """)

        result = await session.execute(series_query)
        all_series = result.fetchall()

        updated_series = 0

        for series_id, current_name, _ in all_series:
            # Reprocesar el título con el código corregido
            parsed = parse_metadata_from_title(current_name, preserve_special_chars=True)
            new_name = parsed.get("series") or current_name

            # Solo actualizar si hay cambios
            if new_name != current_name:
                update_query = text("""
                    UPDATE series_metadata
                    SET series_name = :new_name
                    WHERE id = :series_id
                """)

                await session.execute(update_query, {"new_name": new_name, "series_id": series_id})

                updated_series += 1

                if updated_series <= 10:  # Log primeros 10 cambios
                    logger.info(f"✏️ Series {series_id}: '{current_name}' -> '{new_name}'")

        logger.info(f"✅ Se actualizaron {updated_series} títulos de series")

        # 2. Actualizar slugs si es necesario (manteniendo hashtags funcionales)
        logger.info("🔗 Verificando slugs...")

        slug_query = text("""
            SELECT id, series_name, slug
            FROM series_metadata
            WHERE series_name IS NOT NULL
        """)

        slug_result = await session.execute(slug_query)
        series_for_slug = slug_result.fetchall()

        from utils.helpers import generar_slug_from_meta

        updated_slugs = 0

        for series_id, series_name, current_slug in series_for_slug:
            meta_dict = {"series_name": series_name}
            new_slug = generar_slug_from_meta(meta_dict)

            if new_slug != current_slug:
                slug_update = text("""
                    UPDATE series_metadata
                    SET slug = :new_slug
                    WHERE id = :series_id
                """)

                await session.execute(slug_update, {"new_slug": new_slug, "series_id": series_id})

                updated_slugs += 1

        logger.info(f"🔗 Se actualizaron {updated_slugs} slugs")

        # 3. Confirmar cambios
        await session.commit()

        logger.info("✅ Actualización de metadatos completada")
        logger.info("📊 Los títulos ahora preservan signos de interrogación")
        logger.info("🔗 Los slugs mantienen compatibilidad con hashtags de Telegram")


if __name__ == "__main__":
    asyncio.run(update_existing_metadata())
