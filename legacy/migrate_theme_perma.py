import sqlite3
import os

db_path = "data/library.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    # Try to add column to users
    try:
        conn.execute("ALTER TABLE users ADD COLUMN allow_theme_templates BOOLEAN DEFAULT 0")
        conn.commit()
        print("Column allow_theme_templates added to users")
    except Exception as e:
        print(f"Error adding to users: {e}")
        
    # Try to add column to user_levels (if missing)
    try:
        conn.execute("ALTER TABLE user_levels ADD COLUMN allow_theme_templates BOOLEAN DEFAULT 0")
        conn.commit()
        print("Column allow_theme_templates added to user_levels")
    except Exception as e:
        print(f"Error adding to user_levels: {e}")
        
    conn.close()
else:
    print(f"{db_path} not found")
