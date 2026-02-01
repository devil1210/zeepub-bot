import asyncio
import logging
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert

from config.config_settings import config
from core.db_manager_pg import pg_manager
from core.supabase_manager import supabase_manager
from models.user_models import AppTheme, User, UserLevel, UserUISettings

logger = logging.getLogger(__name__)


class SyncEngine:
    """
    Handles synchronization between Local Postgres and Remote Supabase.
    Strategy: "Offline-First" (eventually), currently "Master-Replica" for Users.
    """

    def __init__(self):
        self.running = False
        self.sync_interval = 60  # Seconds
        self.last_sync_time = datetime.min

    async def start(self):
        """Starts the background sync loop."""
        if self.running:
            return
        self.running = True

        # Run first sync immediately
        asyncio.create_task(self.sync_down_all())

        asyncio.create_task(self._sync_loop())
        logger.info("Sync Engine started.")

    async def _sync_loop(self):
        while self.running:
            await asyncio.sleep(
                self.sync_interval
            )  # Wait first, as start() already triggered one
            try:
                if config.ENABLE_SUPABASE and config.ENABLE_POSTGRES_PLUGIN:
                    await self.sync_down_all()
            except Exception as e:
                logger.error(f"Error in Sync Loop: {e}")

    async def sync_down_all(self):
        """Orchestrates all downward sync operations."""
        if not supabase_manager.is_active:
            return

        logger.info("Starting full sync down from Supabase...")
        await self.sync_levels_down()
        await self.sync_themes_down()
        await self.sync_users_down()
        await self.sync_ui_settings_down()
        await self.sync_bot_settings_down()

        self.last_sync_time = datetime.utcnow()
        logger.info("Sync down from Supabase completed.")

    async def sync_levels_down(self):
        """Syncs user_levels from Supabase -> local."""
        try:
            res = (
                supabase_manager.get_client().table("user_levels").select("*").execute()
            )
            if not res.data:
                return

            async with pg_manager.get_session() as session:
                for lvl in res.data:
                    # Comprehensive full mapping
                    lvl_data = {
                        "id": lvl["id"],
                        "name": lvl["name"],
                        "priority": lvl.get("priority", 0),
                        "color": lvl.get("color", "#607D8B"),
                        "ui_theme": lvl.get("ui_theme", "dark"),
                        "ui_primary_color": lvl.get("ui_primary_color", "#3b82f6"),
                        "ui_font_size": lvl.get("ui_font_size", 14),
                        "ui_nav_opacity": lvl.get("ui_nav_opacity", 80),
                        "ui_glass_blur": lvl.get("ui_glass_blur", 12),
                        "ui_cover_width": lvl.get("ui_cover_width", 120),
                        "ui_accent_opacity": lvl.get("ui_accent_opacity", 20),
                        "panel_transparency": lvl.get("panel_transparency", 60),
                        "background_color": lvl.get("background_color", "#0f172a"),
                        "card_color": lvl.get("card_color", "#1e293b"),
                        "banner_content_offset": lvl.get("banner_content_offset", 0),
                        "force_settings": lvl.get("force_settings", False),
                        "price": lvl.get("price", 0.0),
                        "can_download": lvl.get("can_download", True),
                        "can_read": lvl.get("can_read", True),
                        "daily_downloads": lvl.get("daily_downloads", 5),
                        "has_mini_app_access": lvl.get("has_mini_app_access", True),
                        "has_library_access": lvl.get("has_library_access", True),
                        "can_request_books": lvl.get("can_request_books", True),
                        "can_upload_epub": lvl.get("can_upload_epub", False),
                        "early_access": lvl.get("early_access", False),
                        "custom_themes": lvl.get("custom_themes", False),
                        "allow_theme_templates": lvl.get(
                            "allow_theme_templates", False
                        ),
                        "show_recommendations": lvl.get("show_recommendations", True),
                    }
                    stmt = (
                        pg_insert(UserLevel)
                        .values(**lvl_data)
                        .on_conflict_do_update(index_elements=["id"], set_=lvl_data)
                    )
                    await session.execute(stmt)
                await session.commit()
        except Exception as e:
            logger.error(f"Error syncing levels down: {e}")

    async def sync_themes_down(self):
        """Syncs app_themes from Supabase -> local."""
        try:
            res = (
                supabase_manager.get_client().table("app_themes").select("*").execute()
            )
            if not res.data:
                return

            async with pg_manager.get_session() as session:
                for t in res.data:
                    # Omit internal IDs if necessary, but here we sync IDs too
                    t_data = {
                        k: v
                        for k, v in t.items()
                        if k not in ["created_at", "updated_at"]
                    }
                    stmt = (
                        pg_insert(AppTheme)
                        .values(**t_data)
                        .on_conflict_do_update(index_elements=["id"], set_=t_data)
                    )
                    await session.execute(stmt)
                await session.commit()
        except Exception as e:
            logger.error(f"Error syncing themes down: {e}")

    async def sync_users_down(self):
        """Pulls updated users from Supabase -> Local Postgres."""
        try:
            # Fetch last 100 modified users for robustness
            res = (
                supabase_manager.get_client()
                .table("users")
                .select("*")
                .order("updated_at", desc=True)
                .limit(100)
                .execute()
            )
            users_data = res.data
            if not users_data:
                return

            async with pg_manager.get_session() as session:
                for u in users_data:
                    user_data = {
                        "telegram_id": u["telegram_id"],
                        "username": u.get("username"),
                        "name": u.get("name"),
                        "nickname": u.get("nickname"),
                        "photo_url": u.get("photo_url"),
                        "level_id": u.get("level_id", 6),
                        "role": u.get("role", "user"),
                        "beta_tester": u.get("beta_tester", False),
                        "has_library_access": u.get("has_library_access", True),
                        "can_request_books": u.get("can_request_books", True),
                        "can_upload_epub": u.get("can_upload_epub", False),
                        "total_downloads": u.get("total_downloads", 0),
                        "insignias": u.get("insignias", []),
                        "settings": u.get("settings", {}),
                        "expires_at": datetime.fromisoformat(
                            u["expires_at"].replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                        if u.get("expires_at")
                        else None,
                    }
                    stmt = (
                        pg_insert(User)
                        .values(**user_data)
                        .on_conflict_do_update(
                            index_elements=["telegram_id"], set_=user_data
                        )
                    )
                    await session.execute(stmt)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to sync users down: {e}")

    async def sync_ui_settings_down(self):
        """Syncs user_ui_settings from Supabase -> local."""
        try:
            res = (
                supabase_manager.get_client()
                .table("user_ui_settings")
                .select("*")
                .execute()
            )
            if not res.data:
                return

            async with pg_manager.get_session() as session:
                for s in res.data:
                    s_data = {k: v for k, v in s.items()}
                    stmt = (
                        pg_insert(UserUISettings)
                        .values(**s_data)
                        .on_conflict_do_update(index_elements=["user_id"], set_=s_data)
                    )
                    await session.execute(stmt)
                await session.commit()
        except Exception as e:
            logger.error(f"Error syncing UI settings down: {e}")

    async def sync_bot_settings_down(self):
        """Syncs bot_settings from Supabase -> local."""
        try:
            from sqlalchemy import text

            res = (
                supabase_manager.get_client()
                .table("bot_settings")
                .select("*")
                .execute()
            )
            if not res.data:
                return

            async with pg_manager.get_session() as session:
                for s in res.data:
                    # raw SQL for bot_settings since it might not have a full model yet or is key-value
                    # but we can try to use text() or just check if table exists
                    stmt = text(
                        "INSERT INTO bot_settings (key, value) VALUES (:key, :value) ON CONFLICT (key) DO UPDATE SET value = :value"
                    )
                    await session.execute(stmt, {"key": s["key"], "value": s["value"]})
                await session.commit()
        except Exception as e:
            logger.debug(
                f"Bot settings sync skipped (table might not exist locally yet): {e}"
            )


sync_engine = SyncEngine()
