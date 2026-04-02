
import os
import sys
from sqlalchemy import text

# Add current dir to path
sys.path.append(os.getcwd())

from utils.library_db import engine

def fix_hashes():
    print("--- FIXING HASH COLUMNS IN POSTGRES ---")
    try:
        with engine.connect() as conn:
            # Table books
            print("Checking table 'books'...")
            conn.execute(text("ALTER TABLE books ADD COLUMN IF NOT EXISTS series_hash VARCHAR(64)"))
            conn.execute(text("ALTER TABLE books ADD COLUMN IF NOT EXISTS book_hash VARCHAR(64)"))
            
            # Table series_metadata
            print("Checking table 'series_metadata'...")
            conn.execute(text("ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS series_hash VARCHAR(64) UNIQUE"))
            
            conn.commit()
            print("✅ Hash columns added/verified.")
            
    except Exception as e:
        print(f"❌ Error during hash fix: {e}")

if __name__ == "__main__":
    fix_hashes()
