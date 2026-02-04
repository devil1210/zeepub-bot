"""
Script para restaurar series que fueron renombradas incorrectamente a "sin propuesta"
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

from sqlalchemy import text

from utils.library_db import get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def restore_sin_propuesta_series():
    """
    Restaura series que fueron incorrectamente renombradas a 'sin propuesta'.
    Intenta recuperar el nombre original desde los libros asociados.
    """

    with get_session() as session:
        # Buscar series con nombre "sin propuesta"
        query = text("""
            SELECT 
                sm.id,
                sm.series_hash,
                sm.series_name,
                sm.series_spanish,
                COUNT(lb.id) as book_count
            FROM series_metadata sm
            LEFT JOIN local_books lb ON lb.series_hash = sm.series_hash
            WHERE sm.series_name = 'sin propuesta' 
               OR sm.series_spanish = 'sin propuesta'
            GROUP BY sm.id, sm.series_hash, sm.series_name, sm.series_spanish
        """)

        affected_series = session.execute(query).fetchall()

        if not affected_series:
            logger.info("✅ No se encontraron series con 'sin propuesta'")
            return

        logger.info(f"🔍 Encontradas {len(affected_series)} series afectadas")

        for series in affected_series:
            series_id, series_hash, current_name, current_spanish, book_count = series

            logger.info(f"\n📚 Serie ID: {series_id}")
            logger.info(f"   Hash: {series_hash}")
            logger.info(f"   Nombre actual: {current_name}")
            logger.info(f"   Español actual: {current_spanish}")
            logger.info(f"   Libros: {book_count}")

            # Intentar recuperar el nombre original desde los libros
            book_query = text("""
                SELECT DISTINCT series, series_spanish, filename
                FROM local_books
                WHERE series_hash = :hash
                LIMIT 5
            """)

            books = session.execute(book_query, {"hash": series_hash}).fetchall()

            if not books:
                logger.warning("   ⚠️ No se encontraron libros para esta serie")
                continue

            # Mostrar opciones de nombres encontrados
            logger.info("\n   📖 Nombres encontrados en los libros:")
            unique_names = {}
            for idx, (series_name, series_spanish, filename) in enumerate(books, 1):
                logger.info(f"      {idx}. EN: {series_name}")
                logger.info(f"         ES: {series_spanish}")
                logger.info(f"         Archivo: {filename}")

                if series_name and series_name != "sin propuesta":
                    unique_names["english"] = series_name
                if series_spanish and series_spanish != "sin propuesta":
                    unique_names["spanish"] = series_spanish

            # Si encontramos nombres válidos, restaurar
            if unique_names:
                new_english = unique_names.get("english", current_name)
                new_spanish = unique_names.get("spanish", current_spanish)

                # Actualizar la serie
                update_query = text("""
                    UPDATE series_metadata
                    SET series_name = :english,
                        series_spanish = :spanish,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """)

                session.execute(
                    update_query, {"id": series_id, "english": new_english, "spanish": new_spanish}
                )
                session.commit()

                logger.info("   ✅ Serie restaurada:")
                logger.info(f"      EN: {new_english}")
                logger.info(f"      ES: {new_spanish}")
            else:
                logger.warning("   ⚠️ No se pudo recuperar un nombre válido para esta serie")

        logger.info(f"\n✅ Proceso completado. {len(affected_series)} series procesadas.")


if __name__ == "__main__":
    try:
        restore_sin_propuesta_series()
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
