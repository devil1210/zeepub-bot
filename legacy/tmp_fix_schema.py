
import os
import sys
from sqlalchemy import text

# Add current dir to path
sys.path.append(os.getcwd())

from utils.library_db import engine

def fix():
    print("--- FIXING POSTGRES SCHEMA ---")
    try:
        with engine.connect() as conn:
            # Add series_id to books
            conn.execute(text("ALTER TABLE books ADD COLUMN IF NOT EXISTS series_id INTEGER"))
            conn.commit()
            print("✅ Column 'series_id' added to 'books'")
            
            # Add series_id to archived_books (just in case)
            conn.execute(text("ALTER TABLE archived_books ADD COLUMN IF NOT EXISTS series_id INTEGER"))
            conn.commit()
            print("✅ Column 'series_id' added to 'archived_books'")
            
    except Exception as e:
        print(f"❌ Error during fix: {e}")

if __name__ == "__main__":
    fix()
