import sqlite3
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_sqlite():
    # Try multiple paths to be sure
    paths = ['data/url_cache.db', 'local_cache.db', 'url_cache.db']
    db_path = None
    for p in paths:
        if os.path.exists(p):
            db_path = p
            break
            
    if not db_path:
        logger.error("Could not find database file")
        return

    logger.info(f"Using database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Check columns in users table
    try:
        cursor.execute("PRAGMA table_info(users)")
        cols = [row[1] for row in cursor.fetchall()]
        
        if not cols:
            logger.error("Table 'users' not found in database")
            return

        # 2. Add 'level' column if not exists
        if 'level' not in cols:
            logger.info("Adding 'level' column to SQLite users table")
            cursor.execute("ALTER TABLE users ADD COLUMN level TEXT DEFAULT 'free'")
        
        # 3. Data migration: Copy 'role' to 'level' if 'level' is default/null
        logger.info("Syncing data from 'role' to 'level' for tiers")
        cursor.execute("UPDATE users SET level = role WHERE level = 'free' OR level IS NULL")
        
        # 4. Sync 'custom_status' to 'role'
        # In the new logic: 'role' column will hold 'Publicador', etc.
        if 'custom_status' in cols:
            logger.info("Copying 'custom_status' to 'role' for functional roles")
            # Only update if current role looks like a tier or is null
            cursor.execute("UPDATE users SET role = custom_status WHERE custom_status IS NOT NULL")
        
        conn.commit()
        logger.info("SQLite migration complete")
    except Exception as e:
        logger.error(f"Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_sqlite()
