import asyncio
import sqlite3
import json
import logging
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from core.db_manager_pg import pg_manager
from sqlalchemy import insert, text
from models.user_models import User, UserLevel
from models.library_models import LocalBook, LibrarySource, UserRating

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQLITE_USERS_PATH = "users.db"
SQLITE_LIBRARY_PATH = "data/library/library.db"

async def migrate_users():
    logger.info(f"Migrating Users from {SQLITE_USERS_PATH}...")
    if not os.path.exists(SQLITE_USERS_PATH):
        logger.warning(f"{SQLITE_USERS_PATH} not found. Skipping.")
        return

    conn = sqlite3.connect(SQLITE_USERS_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. Migrate Levels
    # Assuming levels might be hardcoded in code or in a table. 
    # Let's check if table exists
    try:
        cursor = conn.execute("SELECT * FROM user_levels")
        levels = cursor.fetchall()
        async with pg_manager.get_session() as session:
            for lvl in levels:
                # Upsert Level
                stmt = insert(UserLevel).values(
                    id=lvl['id'],
                    name=lvl['name'],
                    priority=lvl['priority'],
                    ui_theme=lvl.get('ui_theme', 'dark'),
                    can_download=lvl.get('can_download', 1)
                ).on_conflict_do_nothing()
                await session.execute(stmt)
            await session.commit()
            logger.info(f"Migrated {len(levels)} levels.")
    except Exception as e:
        logger.warning(f"Could not migrate levels (might not exist): {e}")

    # 2. Migrate Users
    cursor = conn.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    async with pg_manager.get_session() as session:
        count = 0
        for u in users:
            # Helper to parse JSON safely
            def parse_json(val):
                if not val: return {}
                try: return json.loads(val)
                except: return {}

            settings = parse_json(u['settings']) if 'settings' in u.keys() else {}
            insignias = parse_json(u['insignias']) if 'insignias' in u.keys() else []
            
            # Map Row to Model
            user_data = {
                "telegram_id": u['telegram_id'],
                "username": u['username'],
                "name": u['name'],
                "level_id": u.get('level_id', 6), # Default to Free
                "role": u.get('role', 'user'),
                "total_downloads": u.get('total_downloads', 0),
                "settings": settings,
                "insignias": insignias,
                # Add other fields as necessary
            }
            
            stmt = insert(User).values(**user_data)
            # Postgres upsert usually:
            stmt = stmt.on_conflict_do_update(
                index_elements=['telegram_id'],
                set_=user_data
            )
            await session.execute(stmt)
            count += 1
            if count % 100 == 0:
                await session.commit()
                logger.info(f"Migrated {count} users...")
        
        await session.commit()
        logger.info(f"Total Users Migrated: {count}")
    conn.close()

async def migrate_library():
    logger.info(f"Migrating Library from {SQLITE_LIBRARY_PATH}...")
    if not os.path.exists(SQLITE_LIBRARY_PATH):
        logger.warning(f"{SQLITE_LIBRARY_PATH} not found. Skipping.")
        return

    conn = sqlite3.connect(SQLITE_LIBRARY_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. Sources
    cursor = conn.execute("SELECT * FROM library_sources")
    sources = cursor.fetchall()
    
    async with pg_manager.get_session() as session:
        for s in sources:
            stmt = insert(LibrarySource).values(
                id=s['id'],
                name=s['name'],
                path=s['path']
            ).on_conflict_do_nothing()
            await session.execute(stmt)
        await session.commit()

    # 2. Books
    cursor = conn.execute("SELECT * FROM local_books")
    books = cursor.fetchall()
    
    async with pg_manager.get_session() as session:
        count = 0
        for b in books:
            # Map `content_hash` -> `book_hash`
            b_hash = b['content_hash'] # Old column
            if not b_hash and 'book_hash' in b.keys():
                b_hash = b['book_hash']
            
            book_data = {
                "id": b['id'],
                "source_id": b['source_id'],
                "filepath": b['filepath'],
                "filename": b['filename'],
                "title": b['title'],
                "book_hash": b_hash, # MAPPED
                "series_hash": b['series_hash'],
                "series": b['series'],
                "volume": b['volume'],
                "author": b.get('author'),
                # ... map other fields
            }
            
            stmt = insert(LocalBook).values(**book_data).on_conflict_do_update(
                index_elements=['filepath'], # Filepath is unique
                set_=book_data
            )
            await session.execute(stmt)
            count += 1
        await session.commit()
        logger.info(f"Migrated {count} books.")

    conn.close()

async def main():
    await pg_manager.initialize()
    
    # Run Orchestrator first to ensure tables exist
    from core.schema_orchestrator import schema_orchestrator
    await schema_orchestrator.initialize_schema()
    
    await migrate_users()
    await migrate_library()
    
    await pg_manager.close()
    logger.info("Migration Completed.")

if __name__ == "__main__":
    asyncio.run(main())
