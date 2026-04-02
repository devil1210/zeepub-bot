#!/usr/bin/env python3
"""
Migración para corregir títulos de series que faltan signos de interrogación
Ejecutar en VPS via Docker: docker exec zeepub-api python migrations/fix_question_marks.py
"""

import asyncio
import logging

from sqlalchemy import text

from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_question_marks():
    """Corrige títulos de series que deberían tener signos de interrogación"""

    async with pg_manager.get_session() as session:
        # Buscar series específicas que necesitan corrección
        query = text("""
            SELECT id, series_name, series_hash
            FROM series_metadata
            WHERE (
                (series_name ILIKE '%Aren%t Too Sweet Salt-God Sato-San%' AND NOT series_name LIKE '%?')
                OR
                (series_name ILIKE '%Why%Raelia%' AND NOT series_name LIKE '%?')
                OR
                (series_name ILIKE '%What%Happened%' AND NOT series_name LIKE '%?')
            )
        """)

        result = await session.execute(query)
        series_to_fix = result.fetchall()

        if not series_to_fix:
            logger.info("No se encontraron series para corregir")
            return

        logger.info(f"Se encontraron {len(series_to_fix)} series para corregir")

        for series_id, series_name, _ in series_to_fix:
            new_name = series_name + "?"

            logger.info(f"Corrigiendo ID={series_id}: '{series_name}' -> '{new_name}'")

            # Actualizar el título
            update_query = text("""
                UPDATE series_metadata
                SET series_name = :new_name
                WHERE id = :series_id
            """)

            await session.execute(update_query, {"new_name": new_name, "series_id": series_id})

        await session.commit()
        logger.info(f"Se corrigieron {len(series_to_fix)} series exitosamente")


if __name__ == "__main__":
    asyncio.run(fix_question_marks())
