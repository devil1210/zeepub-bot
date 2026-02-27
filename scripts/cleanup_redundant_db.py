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

    columns_to_drop = [
        "series",
        "author",
        "author_jap",
        "illustrator",
        "illustrator_jap",
        "description",
        "demographics",
        "tags",
        "book_type",
    ]

    tables_to_clean = ["local_books", "upload_books", "archived_books"]

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()

        for table in tables_to_clean:
            for col in columns_to_drop:
                try:
                    query = f"ALTER TABLE {table} DROP COLUMN IF EXISTS {col} CASCADE;"
                    cur.execute(query)
                    print(f"Dropped {col} from {table}")
                except Exception as e:
                    print(f"Error dropping {col} from {table}: {e}")

        print("Database redundant columns cleanup completed locally.")
        cur.close()
        conn.close()
    except Exception as e:
        print("Connection failed:", e)


if __name__ == "__main__":
    main()
