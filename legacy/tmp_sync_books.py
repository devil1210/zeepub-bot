
import os
import sys
from sqlalchemy import text, inspect

# Add current dir to path
sys.path.append(os.getcwd())

from utils.library_db import engine
from models.library_models import Book

def get_col_type(sa_type):
    # Mapping simple types for migration
    name = str(sa_type).upper()
    if "VARCHAR" in name: return "VARCHAR(1024)"
    if "INTEGER" in name: return "INTEGER"
    if "FLOAT" in name: return "FLOAT"
    if "BOOLEAN" in name: return "BOOLEAN"
    if "DATETIME" in name: return "TIMESTAMP"
    if "TIMESTAMP" in name: return "TIMESTAMP"
    if "TEXT" in name: return "TEXT"
    if "JSON" in name: return "JSONB"
    if "UUID" in name: return "UUID"
    return "VARCHAR(255)"

def sync_schema():
    print("--- SYNCING BOOKS SCHEMA ---")
    try:
        with engine.connect() as conn:
            # 1. Get current columns in DB
            res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'books'"))
            db_cols = {r[0].lower() for r in res}
            
            # 2. Get columns from Model
            mapper = inspect(Book)
            for column in mapper.columns:
                col_name = column.key.lower()
                if col_name not in db_cols:
                    col_type = get_col_type(column.type)
                    print(f"➕ Adding missing column: {col_name} ({col_type})")
                    try:
                        conn.execute(text(f"ALTER TABLE books ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                    except Exception as e:
                        print(f"⚠️ Could not add {col_name}: {e}")
                        conn.rollback()
            
            print("✅ Schema sync completed.")
            
    except Exception as e:
        print(f"❌ Error during sync: {e}")

if __name__ == "__main__":
    sync_schema()
