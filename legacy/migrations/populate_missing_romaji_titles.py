#!/usr/bin/env python3
"""
Migración: Poblar campos romaji_title vacíos en LocalBook

Este script extrae el romaji del título principal y lo guarda
en el campo romaji_title de todos los registros que estén vacíos.
"""

import asyncio
import os
import re
import sys

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from utils.db import get_pg_manager


def extract_romaji_from_title(title: str) -> str:
    """
    Extrae caracteres romaji (latinos) de un título mixto.
    """
    if not title:
        return ""

    # Patrones para extraer romaji de títulos japoneses
    # Ej: "Kagurabachi 幽玄の間" -> "Kagurabachi"
    # Ej: "Kagurabachi: Yuugen no Ma" -> "Kagurabachi: Yuugen no Ma"

    # 1. Extraer solo caracteres latinos y espacios básicos
    latin_chars = re.sub(r"[^\w\s\-\:]", "", title)

    # 2. Limpiar espacios múltiples
    romaji = re.sub(r"\s+", " ", latin_chars).strip()

    # 3. Validar que sea romaji válido (mínimo 3 caracteres)
    if len(romaji) >= 3:
        return romaji

    return ""


async def populate_missing_romaji_titles():
    """Poblar campos romaji_title vacíos en LocalBook."""

    pg_manager = get_pg_manager()

    try:
        async with pg_manager.get_session() as session:
            print("🔍 Buscando LocalBook con romaji_title vacío...")

            # Buscar libros con romaji_title vacío o nulo
            query = text("""
                SELECT id, title, series_spanish, series_english, volume, series_hash
                FROM local_books
                WHERE (romaji_title IS NULL OR romaji_title = '' OR romaji_title = 'None')
                AND title IS NOT NULL
                AND length(title) > 0
                LIMIT 1000
            """)

            result = await session.execute(query)
            books_to_update = result.fetchall()

            if not books_to_update:
                print("✅ No se encontraron libros con romaji_title vacío")
                return

            print(f"📊 Se encontraron {len(books_to_update)} libros para actualizar")

            updated_count = 0

            for book_id, title, _, _, _, _ in books_to_update:
                # Extraer romaji del título
                extracted_romaji = extract_romaji_from_title(title)

                if extracted_romaji:
                    # Actualizar el campo romaji_title
                    update_query = text("""
                        UPDATE local_books
                        SET romaji_title = :romaji_title
                        WHERE id = :book_id
                    """)

                    await session.execute(update_query, {"romaji_title": extracted_romaji, "book_id": book_id})

                    updated_count += 1
                    print(f"✅ Actualizado libro ID {book_id}: '{title}' -> '{extracted_romaji}'")
                else:
                    print(f"⚠️  No se pudo extraer romaji de: '{title}' (ID: {book_id})")

            # Commit de todos los cambios
            await session.commit()

            print(f"🎉 Proceso completado. Se actualizaron {updated_count} registros de romaji_title")

    except Exception as e:
        print(f"❌ Error en migración: {e}")
        raise
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(populate_missing_romaji_titles())
