import sqlite3
import os

db_path = "data/library.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("ALTER TABLE user_levels ADD COLUMN force_settings BOOLEAN DEFAULT 0")
    except: pass
    conn.commit()
    print("Column force_settings added successfully")
    conn.close()
else:
    print(f"{db_path} not found")
