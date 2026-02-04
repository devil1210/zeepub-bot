"""
Script para restaurar series que fueron renombradas incorrectamente a "sin propuesta"
Versión simplificada con SQL directo
"""

import os
from sqlalchemy import create_engine, text

# Usar DATABASE_URL del entorno o la local por defecto
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/zeepub")

# Convertir a formato sync si es necesario
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
if "+asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+asyncpg", "", 1)

print(f"🔗 Conectando a: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'database'}")

try:
    engine = create_engine(DATABASE_URL, echo=False)

    with engine.connect() as conn:
        # Buscar series con "sin propuesta"
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

        affected_series = conn.execute(query).fetchall()

        if not affected_series:
            print("✅ No se encontraron series con 'sin propuesta'")
            exit(0)

        print(f"\n🔍 Encontradas {len(affected_series)} series afectadas\n")

        for series in affected_series:
            series_id, series_hash, current_name, current_spanish, book_count = series

            print(f"📚 Serie ID: {series_id}")
            print(f"   Hash: {series_hash}")
            print(f"   Nombre actual EN: {current_name}")
            print(f"   Nombre actual ES: {current_spanish}")
            print(f"   Libros: {book_count}")

            # Recuperar nombres desde los libros
            book_query = text("""
                SELECT DISTINCT series, series_spanish, filename
                FROM local_books
                WHERE series_hash = :hash
                LIMIT 5
            """)

            books = conn.execute(book_query, {"hash": series_hash}).fetchall()

            if not books:
                print(f"   ⚠️ No se encontraron libros para esta serie\n")
                continue

            # Buscar nombres válidos
            valid_english = None
            valid_spanish = None

            print(f"\n   📖 Nombres encontrados en los libros:")
            for idx, (series_name, series_spanish, filename) in enumerate(books, 1):
                print(f"      {idx}. EN: {series_name}")
                print(f"         ES: {series_spanish}")
                print(f"         Archivo: {filename[:50]}...")

                if series_name and series_name != "sin propuesta" and not valid_english:
                    valid_english = series_name
                if series_spanish and series_spanish != "sin propuesta" and not valid_spanish:
                    valid_spanish = series_spanish

            # Restaurar si encontramos nombres válidos
            if valid_english or valid_spanish:
                new_english = valid_english or current_name
                new_spanish = valid_spanish or current_spanish

                update_query = text("""
                    UPDATE series_metadata
                    SET series_name = :english,
                        series_spanish = :spanish,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """)

                conn.execute(
                    update_query, {"id": series_id, "english": new_english, "spanish": new_spanish}
                )
                conn.commit()

                print(f"\n   ✅ Serie restaurada:")
                print(f"      EN: {new_english}")
                print(f"      ES: {new_spanish}\n")
            else:
                print(f"   ⚠️ No se pudo recuperar un nombre válido\n")

        print(f"✅ Proceso completado. {len(affected_series)} series procesadas.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
