import psycopg2


def fix():
    try:
        # Intenta conectar localmente
        conn = psycopg2.connect("postgresql://zeepub:zeepub@localhost:5432/zeepub")
        conn.autocommit = True
        cur = conn.cursor()

        print("Añadiendo columna spanish_title a series_metadata...")
        cur.execute(
            "ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS spanish_title VARCHAR(255);"
        )

        print("Añadiendo columna series_spanish a series_metadata...")
        cur.execute(
            "ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS series_spanish VARCHAR(255);"
        )

        print("Añadiendo columna spanish_title a local_books...")
        cur.execute("ALTER TABLE local_books ADD COLUMN IF NOT EXISTS spanish_title VARCHAR(255);")

        print("Añadiendo columna book_id a download_history...")
        cur.execute("ALTER TABLE download_history ADD COLUMN IF NOT EXISTS book_id INTEGER;")

        print("✅ Columnas añadidas con éxito via puerto 5432!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error conectando o ejecutando: {e}")


if __name__ == "__main__":
    fix()
