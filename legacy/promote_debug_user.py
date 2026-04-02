import sqlite3
import os

db = 'data/url_cache.db'
if os.path.exists(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    try:
        uid = 133994080
        # Ensure level 1 is Admin
        cursor.execute("SELECT name FROM user_levels WHERE id=1")
        row = cursor.fetchone()
        if not row:
            print("Level 1 not found, creating it...")
            cursor.execute("INSERT OR REPLACE INTO user_levels (id, name, priority, color, has_mini_app_access) VALUES (1, 'Administrador', 10, '#FF6B6B', 1)")
        
        cursor.execute("INSERT OR IGNORE INTO users (telegram_id, level_id, role) VALUES (?, 1, 'admin')", (uid,))
        cursor.execute("UPDATE users SET level_id=1, role='admin' WHERE telegram_id=?", (uid,))
        cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (uid,))
        conn.commit()
        print(f"User {uid} promoted to admin in {db}")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
