
import sqlite3
import os

DB_PATH = "data/url_cache.db"

def add_column_if_not_exists(cursor, table, col_name, col_type, default):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} DEFAULT {default}")
        print(f"Added column {col_name} to {table}")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print(f"Column {col_name} already exists in {table}")
        else:
            print(f"Error adding {col_name}: {e}")

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Columns to add to user_levels
    columns = [
        ("background_color", "TEXT", "'#0f172a'"),
        ("card_color", "TEXT", "'#1e293b'"),
        ("banner_content_offset", "INTEGER", "0"),
        ("force_settings", "BOOLEAN", "0"),
        ("ui_primary_color", "TEXT", "'#2b6cee'"),
        ("ui_theme", "TEXT", "'dark'"),
        ("ui_font_size", "INTEGER", "14"),
        ("ui_glass_blur", "INTEGER", "12"),
        ("ui_cover_width", "INTEGER", "120"),
        ("ui_nav_opacity", "REAL", "0.8"),
        ("ui_accent_opacity", "REAL", "0.2"),
        ("panel_transparency", "INTEGER", "60"),
        ("can_download", "BOOLEAN", "1"),
        ("can_read", "BOOLEAN", "1"),
        ("has_library_access", "BOOLEAN", "1"),
        ("can_request_books", "BOOLEAN", "1")
    ]

    print("Updating SQLite schema...")
    for col, dtype, default in columns:
        add_column_if_not_exists(cursor, "user_levels", col, dtype, default)

    conn.commit()
    conn.close()
    print("SQLite schema update complete.")

if __name__ == "__main__":
    main()
