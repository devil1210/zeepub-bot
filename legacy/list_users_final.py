import sqlite3
import os

db = 'data/url_cache.db'
if os.path.exists(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT telegram_id, nickname, username, level_id FROM users")
        rows = cursor.fetchall()
        print("--- USERS ---")
        for row in rows:
            print(f"ID: {row[0]}, Nickname: {row[1]}, Username: {row[2]}, Level: {row[3]}")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
