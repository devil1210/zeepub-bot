"""
Script de diagnóstico para verificar qué temas existen en la base de datos
"""

import asyncio
import logging
import sys

# Agregar el path del proyecto
sys.path.append("/app")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config.config_settings import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def diagnose_themes():
    """Diagnostica qué temas existen y cuáles tienen '2'."""

    if not config.ENABLE_POSTGRES_PLUGIN:
        logger.error("PostgreSQL plugin not enabled")
        return

    DATABASE_URL = config.DATABASE_URL
    if not DATABASE_URL:
        logger.error("DATABASE_URL not configured")
        return

    logger.info("=== THEME DIAGNOSTIC ===")

    try:
        engine = create_async_engine(DATABASE_URL, echo=False)

        async with engine.begin() as conn:
            # Obtener todos los temas
            result = await conn.execute(text("SELECT id, name FROM app_themes ORDER BY name"))
            all_themes = result.fetchall()

            logger.info(f"\nTotal themes found: {len(all_themes)}")
            logger.info("=" * 50)

            # Categorizar temas
            themes_ending_2 = []
            themes_containing_2 = []
            other_themes = []

            for theme in all_themes:
                theme_id, name = theme
                if name and name.strip().endswith("2"):
                    themes_ending_2.append(theme)
                elif name and "2" in name:
                    themes_containing_2.append(theme)
                else:
                    other_themes.append(theme)

            # Mostrar resultados
            logger.info(f"\n🎯 THEMES ENDING WITH '2' ({len(themes_ending_2)}):")
            for theme_id, name in themes_ending_2:
                logger.info(f"  - ID: {theme_id}, Name: '{name}'")

            logger.info(
                f"\n🔍 THEMES CONTAINING '2' (but not ending) ({len(themes_containing_2)}):"
            )
            for theme_id, name in themes_containing_2:
                logger.info(f"  - ID: {theme_id}, Name: '{name}'")

            logger.info(f"\n📋 OTHER THEMES ({len(other_themes)}):")
            for theme_id, name in other_themes:
                logger.info(f"  - ID: {theme_id}, Name: '{name}'")

            # Resumen
            logger.info("\n📊 SUMMARY:")
            logger.info(f"  - Total themes: {len(all_themes)}")
            logger.info(f"  - Themes ending with '2': {len(themes_ending_2)}")
            logger.info(f"  - Themes containing '2': {len(themes_containing_2)}")
            logger.info(f"  - Other themes: {len(other_themes)}")

            # Sugerir acción
            if themes_ending_2:
                logger.info(f"\n✅ ACTION: Found {len(themes_ending_2)} themes to rename")
                for theme_id, name in themes_ending_2:
                    base_name = name.replace(" 2", "").strip()
                    logger.info(f"  - '{name}' → '{base_name} Pro' (suggested)")
            else:
                logger.info("\n❌ ACTION: No themes ending with '2' found to rename")

        await engine.dispose()
        logger.info("\n=== DIAGNOSTIC COMPLETE ===")

    except Exception as e:
        logger.error(f"Error in diagnostic: {e}")


if __name__ == "__main__":
    asyncio.run(diagnose_themes())
