#!/usr/bin/env python3
"""
Migración: Agregar campo romaji_title a series_metadata

Esta migración agrega el campo romaji_title a la tabla series_metadata
para que el frontend pueda acceder al título en romaji de las series.
"""

import asyncio
import os
import sys

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from utils.db import get_pg_manager


async def add_romaji_title_column():
    """Agrega la columna romaji_title a series_metadata si no existe."""

    pg_manager = get_pg_manager()

    try:
        async with pg_manager.get_session() as session:
            # Verificar si la columna ya existe
            check_query = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'series_metadata'
                AND column_name = 'romaji_title'
            """)

            result = await session.execute(check_query)
            column_exists = result.fetchone() is not None

            if not column_exists:
                print("🔧 Agregando columna romaji_title a series_metadata...")

                # Agregar la columna
                alter_query = text("""
                    ALTER TABLE series_metadata
                    ADD COLUMN romaji_title VARCHAR(512)
                """)

                await session.execute(alter_query)
                await session.commit()

                print("✅ Columna romaji_title agregada exitosamente")

                # Opcional: Copiar datos existentes desde local_books si se desea
                # Esto podría hacerse en una migración separada si es necesario
                print("ℹ️  Nota: Los datos de romaji_title deberían copiarse desde local_books si es necesario")

            else:
                print("✅ La columna romaji_title ya existe en series_metadata")

    except Exception as e:
        print(f"❌ Error en migración: {e}")
        raise
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(add_romaji_title_column())
