import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, update, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from config.config_settings import config
from core.db_manager_pg import pg_manager
from core.supabase_manager import supabase_manager
from models.user_models import User, UserUISettings, UserLevel

logger = logging.getLogger(__name__)

class SyncEngine:
    """
    Handles synchronization between Local Postgres and Remote Supabase.
    Strategy: "Offline-First" (eventually), currently "Master-Replica" for Users.
    """
    
    def __init__(self):
        self.running = False
        self.sync_interval = 60 # Seconds
        self.last_sync_time = datetime.min

    async def start(self):
        """Starts the background sync loop."""
        if self.running: return
        self.running = True
        asyncio.create_task(self._sync_loop())
        logger.info("Sync Engine started.")

    async def _sync_loop(self):
        while self.running:
            try:
                if config.ENABLE_SUPABASE and config.ENABLE_POSTGRES_PLUGIN:
                    await self.sync_users_down()
            except Exception as e:
                logger.error(f"Error in Sync Loop: {e}")
            
            await asyncio.sleep(self.sync_interval)

    async def sync_users_down(self):
        """
        Pulls updated users from Supabase -> Local Postgres.
        Uses 'updated_at' timestamp to only fetch changes.
        """
        if not supabase_manager.is_active: 
            return

        try:
            # 1. Get max updated_at from local DB to know where to resume
            # For now, simplistic approach: Sync all modified in last X time or generic
            # Proper way: SELECT MAX(updated_at) FROM users
            
            # Fetch from Supabase (Users modified recently)
            # Note: storing last_sync_time in memory is risky on restart, 
            # ideally should be stored in a 'sync_state' table. Used simplified memory for now.
            
            # Fetch users updated since last check
            # supabase-py doesn't strictly support gt on timestamp easily without formatting, 
            # so we fetch a batch or all for safety in this MVP phase.
            
            # Optimization: Fetch users where updated_at > self.last_sync_time
            # For robustness in alpha, let's fetch the last 100 modified users.
            
            res = supabase_manager.get_client().table('users').select("*").order('updated_at', desc=True).limit(50).execute()
            users_data = res.data
            
            if not users_data:
                return

            async with pg_manager.get_session() as session:
                for u in users_data:
                    # Map Supabase JSON to Model
                    user_data = {
                        "telegram_id": u['telegram_id'],
                        "username": u.get('username'),
                        "name": u.get('name'),
                        "nickname": u.get('nickname'),
                        "level_id": u.get('level_id', 6),
                        "role": u.get('role', 'user'),
                        "total_downloads": u.get('total_downloads', 0),
                        "insignias": u.get('insignias', []),
                        "settings": u.get('settings', {}),
                        "expires_at": u.get('expires_at'),
                        # "updated_at": u.get('updated_at') # Let Postgres handle its own updated_at or sync it? Sync it.
                    }
                    
                    # Upsert User
                    stmt = pg_insert(User).values(**user_data).on_conflict_do_update(
                        index_elements=['telegram_id'],
                        set_=user_data
                    )
                    await session.execute(stmt)
                    
                    # Sync UI Settings (Separate table in Supabase)
                
                await session.commit()
                
            self.last_sync_time = datetime.utcnow()
            # logger.info(f" synced {len(users_data)} users from Supabase.")

        except Exception as e:
            logger.error(f"Failed to sync users down: {e}")

sync_engine = SyncEngine()
