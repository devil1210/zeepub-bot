
import asyncio
import aiosqlite
import logging
import json
from datetime import datetime
from core.supabase_manager import supabase_manager
from config.config_settings import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate():
    if not supabase_manager.is_active:
        logger.error("Supabase is not active. Check credentials in .env/config.")
        return

    db_path = config.URL_CACHE_DB_PATH
    logger.info(f"Starting migration from {db_path} to Supabase...")

    async with aiosqlite.connect(db_path) as sqlite_conn:
        # 1. Migrate user_levels (already seeded but just in case of custom changes)
        # Assuming we keep the default ones for now to avoid ID conflicts.

        # 2. Migrate users
        logger.info("Migrating users...")
        cursor = await sqlite_conn.execute("SELECT * FROM users")
        rows = await cursor.fetchall()
        
        # Get column names
        cursor = await sqlite_conn.execute("PRAGMA table_info(users)")
        cols = [row[1] for row in await cursor.fetchall()]
        
        users_data = []
        for row in rows:
            user = dict(zip(cols, row))
            # Transform settings from string to JSON
            if isinstance(user.get('settings'), str):
                try:
                    user['settings'] = json.loads(user['settings'])
                except:
                    user['settings'] = {}
            # Ensure level_id is correct
            if not user.get('level_id'):
                user['level_id'] = 6
            users_data.append(user)

        if users_data:
            # Upsert in Supabase
            try:
                res = supabase_manager.get_client().table('users').upsert(users_data).execute()
                logger.info(f"Successfully migrated {len(users_data)} users.")
            except Exception as e:
                logger.error(f"Error migrating users: {e}")

        # 3. Migrate admins
        logger.info("Migrating admins...")
        cursor = await sqlite_conn.execute("SELECT * FROM admins")
        admins = await cursor.fetchall()
        if admins:
            admin_data = [{"user_id": r[0], "granted_by": r[1], "granted_at": r[2]} for r in admins]
            try:
                supabase_manager.get_client().table('admins').upsert(admin_data).execute()
                logger.info(f"Successfully migrated {len(admin_data)} admins.")
            except Exception as e:
                logger.error(f"Error migrating admins: {e}")

        # 4. Migrate download_history
        logger.info("Migrating download_history...")
        cursor = await sqlite_conn.execute("SELECT * FROM download_history")
        history_rows = await cursor.fetchall()
        
        cursor = await sqlite_conn.execute("PRAGMA table_info(download_history)")
        h_cols = [row[1] for row in await cursor.fetchall()]

        history_data = []
        for row in history_rows:
            entry = dict(zip(h_cols, row))
            if 'id' in entry: del entry['id'] # Let Supabase handle the serial ID
            history_data.append(entry)

        if history_data:
            # Batch inserts (max 1000 per request usually for better reliability)
            batch_size = 500
            for i in range(0, len(history_data), batch_size):
                batch = history_data[i:i+batch_size]
                try:
                    supabase_manager.get_client().table('download_history').insert(batch).execute()
                except Exception as e:
                    logger.error(f"Error migrating history batch {i}: {e}")
            logger.info(f"Successfully migrated {len(history_data)} download history entries.")

    logger.info("Migration from url_cache.db completed.")

    # 5. Migrate user_metrics.db
    metrics_db_path = os.path.join("data", "user_metrics.db")
    if os.path.exists(metrics_db_path):
        logger.info(f"Starting migration from {metrics_db_path} to Supabase...")
        async with aiosqlite.connect(metrics_db_path) as metrics_conn:
            # Migrate user_downloads
            logger.info("Migrating user_downloads (detailed)...")
            cursor = await metrics_conn.execute("SELECT * FROM user_downloads")
            rows = await cursor.fetchall()
            cursor = await metrics_conn.execute("PRAGMA table_info(user_downloads)")
            cols = [row[1] for row in await cursor.fetchall()]
            
            data = []
            for row in rows:
                entry = dict(zip(cols, row))
                if 'id' in entry: del entry['id']
                data.append(entry)
            
            if data:
                batch_size = 500
                for i in range(0, len(data), batch_size):
                    batch = data[i:i+batch_size]
                    supabase_manager.get_client().table('user_downloads').insert(batch).execute()
                logger.info(f"Successfully migrated {len(data)} detailed downloads.")

            # Migrate user_ratings
            logger.info("Migrating user_ratings...")
            cursor = await metrics_conn.execute("SELECT * FROM user_ratings")
            rows = await cursor.fetchall()
            cursor = await metrics_conn.execute("PRAGMA table_info(user_ratings)")
            cols = [row[1] for row in await cursor.fetchall()]

            data = []
            for row in rows:
                entry = dict(zip(cols, row))
                if 'id' in entry: del entry['id']
                data.append(entry)

            if data:
                supabase_manager.get_client().table('user_ratings').upsert(data).execute()
                logger.info(f"Successfully migrated {len(data)} user ratings.")

    logger.info("Full migration completed.")

if __name__ == "__main__":
    import os
    asyncio.run(migrate())
