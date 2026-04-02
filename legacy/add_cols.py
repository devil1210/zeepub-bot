import sqlite3
import os

db_path = "data/library.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("ALTER TABLE user_levels ADD COLUMN banner_content_offset INTEGER DEFAULT 0")
    except: pass
    try:
        conn.execute("ALTER TABLE user_levels ADD COLUMN background_color TEXT")
    except: pass
    try:
        conn.execute("ALTER TABLE user_levels ADD COLUMN card_color TEXT")
    except: pass
    try:
        conn.execute("ALTER TABLE user_levels ADD COLUMN has_library_access BOOLEAN DEFAULT 1")
    except: pass
    try:
        conn.execute("ALTER TABLE user_levels ADD COLUMN can_request_books BOOLEAN DEFAULT 1")
    except: pass
    
    conn.commit()
    print("Columns added successfully (or already existed)")
    conn.close()
else:
    print(f"{db_path} not found")
