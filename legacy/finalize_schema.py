
import os
import sys
from sqlalchemy import text

# Add current dir to path
sys.path.append(os.getcwd())

from utils.library_db import engine

def finalize_schema():
    print("--- FINALIZING HASH COLUMN NAMES ---")
    try:
        with engine.connect() as conn:
            # Table series_metadata
            # The code expects series_hash
            print("Fixing series_metadata...")
            conn.execute(text("ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS series_hash VARCHAR(64)"))
            # Ensure it's not null and unique if possible, but let's just make it exist
            
            # Table books
            print("Fixing books...")
            conn.execute(text("ALTER TABLE books ADD COLUMN IF NOT EXISTS series_hash VARCHAR(64)"))
            conn.execute(text("ALTER TABLE books ADD COLUMN IF NOT EXISTS book_hash VARCHAR(64)"))
            
            conn.commit()
            print("✅ All required hash columns are present.")
            
    except Exception as e:
        print(f"❌ Error finalizing schema: {e}")

if __name__ == "__main__":
    finalize_schema()
