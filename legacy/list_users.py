import sqlite3
import os

if os.path.exists('users.db'):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, nickname FROM users")
        rows = cursor.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, Username: {row[1]}, Nickname: {row[2]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print("users.db not found")
