"""
Script para analizar el formato de rutas existentes en la biblioteca
Ejecutar dentro del contenedor Docker: docker exec -it <container> python scripts/analyze_library_paths.py
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


async def analyze_library_paths():
    """Analiza el formato de rutas existentes en la biblioteca."""

    DATABASE_URL = config.DATABASE_URL
    if not DATABASE_URL:
        logger.error("DATABASE_URL not configured")
        return

    logger.info("=== ANALIZANDO FORMATO DE RUTAS DE BIBLIOTECA ===")

    try:
        engine = create_async_engine(DATABASE_URL, echo=False)

        async with engine.begin() as conn:
            # Obtener todas las rutas de libros
            result = await conn.execute(
                text("""
                SELECT file_path, title, author 
                FROM local_books 
                WHERE file_path IS NOT NULL 
                ORDER BY file_path
                LIMIT 50
            """)
            )
            books = result.fetchall()

            logger.info(f"\n📚 Analizando {len(books)} rutas existentes:")
            logger.info("=" * 60)

            path_patterns = {}
            structure_analysis = {
                "with_author_folder": 0,
                "direct_in_library": 0,
                "category_folders": 0,
                "other": 0,
            }

            for file_path, title, author in books:
                logger.info(f"📄 {file_path}")
                logger.info(f"   📖 Título: {title}")
                logger.info(f"   ✍️ Autor: {author}")

                # Analizar estructura
                if "/" in file_path:
                    parts = file_path.split("/")
                    if len(parts) >= 2:
                        folder = parts[0]
                        parts[1]

                        # Verificar si el folder parece ser un autor
                        if (
                            author
                            and folder.lower() in author.lower()
                            or author.lower() in folder.lower()
                        ):
                            structure_analysis["with_author_folder"] += 1
                            pattern = f"Author/{title}"
                        elif folder.lower() in ["library", "books", "epub", "libros"]:
                            structure_analysis["direct_in_library"] += 1
                            pattern = f"Category/{title}"
                        else:
                            structure_analysis["category_folders"] += 1
                            pattern = f"Category/{title}"
                    else:
                        structure_analysis["direct_in_library"] += 1
                        pattern = "Direct"
                else:
                    structure_analysis["direct_in_library"] += 1
                    pattern = "Direct"

                # Contar patrones
                if pattern not in path_patterns:
                    path_patterns[pattern] = 0
                path_patterns[pattern] += 1

                logger.info(f"   📁 Patrón: {pattern}")
                logger.info("")

            # Resumen de patrones
            logger.info("📊 RESUMEN DE PATRONES ENCONTRADOS:")
            logger.info("=" * 40)
            for pattern, count in sorted(path_patterns.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"   {pattern}: {count} libros")

            logger.info("\n🏗️ ANÁLISIS ESTRUCTURAL:")
            for structure, count in structure_analysis.items():
                logger.info(f"   {structure}: {count}")

            # Mostrar ejemplos del patrón más común
            most_common_pattern = max(path_patterns.keys(), key=path_patterns.get)
            logger.info(f"\n✅ PATRÓN MÁS COMÚN: {most_common_pattern}")

            logger.info(f"\n📋 EJEMPLOS DEL PATRÓN '{most_common_pattern}':")
            count = 0
            for file_path, title, author in books:
                if count >= 5:
                    break

                # Determinar si sigue el patrón más común
                if most_common_pattern == "Author/Title":
                    if "/" in file_path:
                        parts = file_path.split("/")
                        if len(parts) >= 2:
                            folder = parts[0]
                            if author and (
                                folder.lower() in author.lower() or author.lower() in folder.lower()
                            ):
                                logger.info(f"   📁 {file_path}")
                                count += 1
                elif most_common_pattern == "Category/Title":
                    if "/" in file_path:
                        parts = file_path.split("/")
                        if len(parts) >= 2:
                            logger.info(f"   📁 {file_path}")
                            count += 1
                elif most_common_pattern == "Direct":
                    if "/" not in file_path:
                        logger.info(f"   📁 {file_path}")
                        count += 1

        await engine.dispose()
        logger.info("\n=== ANÁLISIS COMPLETADO ===")

    except Exception as e:
        logger.error(f"Error analyzing library paths: {e}")


if __name__ == "__main__":
    asyncio.run(analyze_library_paths())
