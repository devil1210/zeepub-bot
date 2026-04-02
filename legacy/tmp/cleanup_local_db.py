import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL no encontrado")
        return
    
    # Replace +asyncpg with standard driver and db host with localhost
    db_url = db_url.replace("+asyncpg", "").replace("@db:", "@localhost:")
    print("Using DB URL:", db_url)
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        try:
            cur.execute("ALTER TABLE local_books DROP COLUMN IF EXISTS cover_path;")
            print("Dropped cover_path")
        except Exception as e:
            print(f"cover_path error: {e}")
            
        try:
            cur.execute("ALTER TABLE local_books DROP COLUMN IF EXISTS cover_thumb_path;")
            print("Dropped cover_thumb_path")
        except Exception as e:
            print(f"cover_thumb_path error: {e}")
            
        try:
            cur.execute("ALTER TABLE local_books DROP COLUMN IF EXISTS series_spanish CASCADE;")
            print("Dropped series_spanish")
        except Exception as e:
            print(f"series_spanish error: {e}")
            
        try:
            cur.execute("ALTER TABLE local_books DROP COLUMN IF EXISTS series_english CASCADE;")
            print("Dropped series_english")
        except Exception as e:
            print(f"series_english error: {e}")
            
        print("Database cleanup completed locally.")
        cur.close()
        conn.close()
    except Exception as e:
        print("Connection failed:", e)

if __name__ == "__main__":
    main()
