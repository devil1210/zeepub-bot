import psycopg2


def verify():
    try:
        conn = psycopg2.connect("postgresql://zeepub:zeepub@localhost:5432/zeepub")
        cur = conn.cursor()

        checks = [
            ("series_metadata", "spanish_title"),
            ("series_metadata", "series_spanish"),
            ("local_books", "spanish_title"),
            ("download_history", "book_id"),
        ]

        for table, col in checks:
            cur.execute(
                f"SELECT 1 FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{col}'"
            )
            if cur.fetchone():
                print(f"✅ {table}.{col}: FOUND")
            else:
                print(f"❌ {table}.{col}: MISSING")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    verify()
