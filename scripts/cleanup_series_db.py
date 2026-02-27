import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL no encontrado")
        return

    db_url = db_url.replace("+asyncpg", "").replace("@db:", "@localhost:")
    print("Using DB URL:", db_url)

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()

        try:
            cur.execute("ALTER TABLE series_metadata DROP COLUMN IF EXISTS spanish_title CASCADE;")
            print("Dropped spanish_title from series_metadata")
        except Exception as e:
            print(f"spanish_title (series_metadata) error: {e}")

        try:
            cur.execute("ALTER TABLE archived_series DROP COLUMN IF EXISTS spanish_title CASCADE;")
            print("Dropped spanish_title from archived_series")
        except Exception as e:
            print(f"spanish_title (archived_series) error: {e}")

        print("Database cleanup completed locally.")
        cur.close()
        conn.close()
    except Exception as e:
        print("Connection failed:", e)


if __name__ == "__main__":
    main()
