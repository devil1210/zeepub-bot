import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, text

from config.config_settings import config
from core.db_manager_pg import pg_manager
from core.supabase_manager import supabase_manager
from models.user_models import UserLevel
from services.cache_service import cache_manager

logger = logging.getLogger(__name__)


class OptimizedSyncEngine:
    """
    Optimized synchronization engine that drastically reduces Supabase requests.

    Strategy:
    - Event-driven instead of time-based polling (simulated via pending_changes)
    - Batch processing for massive operations
    - Intelligent caching to reduce redundant queries
    - Change detection via timestamps
    """

    def __init__(self):
        self.running = False
        self.last_sync_times: dict[str, datetime] = {
            "users": datetime.min,
            "user_levels": datetime.min,
            "admins": datetime.min,
            "series_metadata": datetime.min,
        }
        self.pending_changes: dict[str, set[Any]] = {
            "users": set(),
            "user_levels": set(),
            "admins": set(),
            "series_metadata": set(),
        }
        self.sync_intervals = {
            "users": 86400,
            "user_levels": 86400,
            "admins": 86400,
            "series_metadata": 3600,  # 1 hour check
        }
        self.force_next_run = False

    async def start(self):
        """Starts the optimized synchronization engine."""
        if self.running:
            return

        self.running = True
        logger.info("[SYNC_ENGINE] Optimized Sync Engine started (Adaptive Polling mode)")

        # Start background tasks
        asyncio.create_task(self._sync_loop())
        asyncio.create_task(self._change_detector_loop())

    async def stop(self):
        """Stops the synchronization engine."""
        self.running = False
        logger.info("[SYNC_ENGINE] Optimized Sync Engine stopped")

    async def _sync_loop(self):
        """Main optimized synchronization loop."""
        while self.running:
            try:
                if config.ENABLE_SUPABASE and config.ENABLE_POSTGRES_PLUGIN:
                    # Sync only if there are pending changes or interval expired
                    await self._sync_if_changed("users")
                    await self._sync_if_changed("user_levels")
                    await self._sync_if_changed("admins")
                    await self._sync_if_changed("series_metadata")

            except Exception as e:
                logger.error(f"[SYNC_ENGINE] Error in optimized sync loop: {e}", exc_info=True)

            # Adaptive wait (1 hour between passive sync checks)
            # If a run was forced, we wait shortly; otherwise, we wait the long interval.
            await asyncio.sleep(60 if self.force_next_run else 3600)
            self.force_next_run = False

    async def _change_detector_loop(self):
        """Change detection loop."""
        while self.running:
            try:
                await self._detect_changes()
            except Exception as e:
                logger.error(f"[SYNC_ENGINE] Error in change detector loop: {e}")

            await asyncio.sleep(3600)  # Check for remote changes every hour

    async def _detect_changes(self):
        """Detects changes in Supabase without constant polling."""
        if not supabase_manager.is_active:
            return

        try:
            # Detect user changes
            await self._detect_user_changes()

            # Detect level changes (less frequent)
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            if now_utc - self.last_sync_times["user_levels"] > timedelta(hours=1):
                await self._detect_level_changes()

        except Exception as e:
            logger.error(f"[SYNC_ENGINE] Error detecting changes: {e}")

    async def _detect_user_changes(self):
        """Detects changes in Supabase users."""
        try:
            # Use timestamp differential query
            last_check = self.last_sync_times["users"]

            # Optimized query to get only modified users
            result = (
                supabase_manager.get_client()
                .table("users")
                .select("telegram_id, updated_at")
                .gte("updated_at", last_check.isoformat())
                .limit(100)
                .execute()
            )

            if result and result.data:
                changed_users = {item["telegram_id"] for item in result.data}
                self.pending_changes["users"].update(changed_users)

                if changed_users:
                    logger.info(f"[SYNC] Detected {len(changed_users)} user changes in Supabase")

        except Exception as e:
            logger.error(f"[SYNC_ENGINE] Error detecting user changes: {e}")

    async def _detect_level_changes(self):
        """Detects changes in user levels."""
        try:
            result = supabase_manager.get_client().table("user_levels").select("id, updated_at").execute()

            if result and result.data:
                # Compare with local version
                local_levels = await self._get_local_level_ids()
                remote_levels = {item["id"] for item in result.data}

                if local_levels != remote_levels:
                    self.pending_changes["user_levels"].add("all")
                    logger.info("[SYNC_ENGINE] Detected user_levels changes in Supabase")

        except Exception as e:
            logger.error(f"[SYNC_ENGINE] Error detecting level changes: {e}")

    async def _get_local_level_ids(self) -> set[int]:
        """Gets local level IDs."""
        try:
            async with pg_manager.get_session() as session:
                result = await session.execute(select(UserLevel.id))
                return {row[0] for row in result.fetchall()}
        except Exception as e:
            logger.error(f"[SYNC_ENGINE] Error getting local level IDs: {e}")
            return set()

    async def _sync_if_changed(self, table_name: str):
        """Syncs table only if there are pending changes or interval has passed."""
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

        has_pending = bool(self.pending_changes[table_name])
        time_since_last = now_utc - self.last_sync_times[table_name]
        interval_expired = time_since_last >= timedelta(seconds=self.sync_intervals[table_name])

        if not has_pending and not interval_expired:
            return

        reason = "pending changes" if has_pending else "interval expired"
        logger.info(f"[SYNC_ENGINE] Syncing {table_name} ({reason})")

        try:
            if table_name == "users":
                await self._sync_users_optimized()
            elif table_name == "user_levels":
                await self._sync_user_levels_optimized()
            elif table_name == "admins":
                await self._sync_admins_optimized()
            elif table_name == "series_metadata":
                await self._sync_series_from_cloud()

            # Update last sync time and clear pending
            self.last_sync_times[table_name] = now_utc
            self.pending_changes[table_name].clear()

        except Exception as e:
            logger.error(f"[SYNC_ENGINE] Error during {table_name} sync: {e}")

    async def _sync_users_optimized(self):
        """Optimized user synchronization."""
        if not supabase_manager.is_active:
            return

        try:
            last_sync = self.last_sync_times["users"]

            try:
                # Attempt 1: Filter by updated_at (efficient)
                query = supabase_manager.get_client().table("users").select("*")
                if last_sync > datetime.min:
                    query = query.gte("updated_at", last_sync.isoformat())

                result = query.order("updated_at", desc=True).limit(200).execute()
            except Exception as query_e:
                # Log only the error message to avoid flooding
                if "column" in str(query_e) and "updated_at" in str(query_e):
                    logger.warning("[SYNC_ENGINE] Supabase schema missing 'updated_at'. Falling back to full fetch.")
                    result = supabase_manager.get_client().table("users").select("*").limit(500).execute()
                else:
                    raise query_e

            if not result or not result.data:
                return

            # Batch update local
            await self._batch_update_users(result.data)

            # Invalidate affected users cache
            for user_data in result.data:
                try:
                    await cache_manager.invalidate_user(user_data["telegram_id"])
                except Exception:
                    pass

            logger.info(f"[SYNC_ENGINE] Successfully synced {len(result.data)} users")

        except Exception as e:
            logger.error(f"[SYNC_ENGINE] Error in optimized users sync: {e}")

    async def _batch_update_users(self, users_data: list[dict[str, Any]]):
        """Batch update users in local database."""
        try:
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            async with pg_manager.get_session() as session:
                for user_data in users_data:
                    # Map Supabase data to local model
                    mapped_data = {
                        "telegram_id": user_data["telegram_id"],
                        "username": user_data.get("username"),
                        "name": user_data.get("name"),
                        "nickname": user_data.get("nickname"),
                        "photo_url": user_data.get("photo_url"),
                        "level_id": user_data.get("level_id", 6),
                        "role": user_data.get("role", "user"),
                        "beta_tester": user_data.get("beta_tester", False),
                        "has_library_access": user_data.get("has_library_access", True),
                        "can_request_books": user_data.get("can_request_books", True),
                        "can_upload_epub": user_data.get("can_upload_epub", False),
                        "total_downloads": user_data.get("total_downloads", 0),
                        "insignias": json.dumps(user_data.get("insignias", [])),
                        "settings": json.dumps(user_data.get("settings", {})),
                        "expires_at": self._parse_datetime(user_data.get("expires_at")),
                        "created_at": self._parse_datetime(user_data.get("added_at") or user_data.get("created_at")),
                        "updated_at": now_utc,
                    }

                    # Optimized Upsert
                    await session.execute(
                        text("""
                            INSERT INTO users (
                                telegram_id, username, name, nickname, photo_url, level_id, role,
                                beta_tester, has_library_access, can_request_books, can_upload_epub,
                                total_downloads, insignias, settings, expires_at, created_at, updated_at
                            ) VALUES (
                                :telegram_id, :username, :name, :nickname, :photo_url, :level_id, :role,
                                :beta_tester, :has_library_access, :can_request_books, :can_upload_epub,
                                :total_downloads, :insignias, :settings, :expires_at, :created_at, :updated_at
                            )
                            ON CONFLICT (telegram_id) DO UPDATE SET
                                username = EXCLUDED.username,
                                name = EXCLUDED.name,
                                nickname = EXCLUDED.nickname,
                                photo_url = EXCLUDED.photo_url,
                                level_id = EXCLUDED.level_id,
                                role = EXCLUDED.role,
                                beta_tester = EXCLUDED.beta_tester,
                                has_library_access = EXCLUDED.has_library_access,
                                can_request_books = EXCLUDED.can_request_books,
                                can_upload_epub = EXCLUDED.can_upload_epub,
                                total_downloads = EXCLUDED.total_downloads,
                                insignias = EXCLUDED.insignias,
                                settings = EXCLUDED.settings,
                                expires_at = EXCLUDED.expires_at,
                                created_at = EXCLUDED.created_at,
                                updated_at = EXCLUDED.updated_at
                        """),
                        mapped_data,
                    )

                await session.commit()

        except Exception as e:
            logger.error(f"[SYNC_ENGINE] Error in batch user update: {e}")
            raise

    async def _sync_user_levels_optimized(self):
        """Optimized level synchronization."""
        if not supabase_manager.is_active:
            return

        try:
            result = supabase_manager.get_client().table("user_levels").select("*").execute()

            if not result or not result.data:
                return

            await self._batch_update_levels(result.data)
            logger.info(f"[SYNC_ENGINE] Successfully synced {len(result.data)} user levels")

        except Exception as e:
            logger.error(f"[SYNC_ENGINE] Error in user levels sync: {e}")

    async def _batch_update_levels(self, levels_data: list[dict[str, Any]]):
        """Batch update levels in local database."""
        try:
            async with pg_manager.get_session() as session:
                for level_data in levels_data:
                    mapped_data = {
                        "id": level_data["id"],
                        "name": level_data["name"],
                        "priority": level_data.get("priority", 0),
                        "color": level_data.get("color", "#607D8B"),
                        "price": level_data.get("price", 0.0),
                        "can_download": level_data.get("can_download", True),
                        "can_read": level_data.get("can_read", True),
                        "daily_downloads": level_data.get("daily_downloads", 5),
                        "has_mini_app_access": level_data.get("has_mini_app_access", True),
                        "has_library_access": level_data.get("has_library_access", True),
                        "can_request_books": level_data.get("can_request_books", True),
                        "early_access": level_data.get("early_access", False),
                        "custom_themes": level_data.get("custom_themes", False),
                        "allow_theme_templates": level_data.get("allow_theme_templates", False),
                        "show_recommendations": level_data.get("show_recommendations", True),
                        "default_theme_id": level_data.get("default_theme_id"),
                    }

                    # Upsert
                    await session.execute(
                        text("""
                            INSERT INTO user_levels (
                                id, name, priority, color, price, can_download, can_read,
                                daily_downloads, has_mini_app_access, has_library_access,
                                can_request_books, early_access, custom_themes,
                                allow_theme_templates, show_recommendations, default_theme_id
                            ) VALUES (
                                :id, :name, :priority, :color, :price, :can_download, :can_read,
                                :daily_downloads, :has_mini_app_access, :has_library_access,
                                :can_request_books, :early_access, :custom_themes,
                                :allow_theme_templates, :show_recommendations, :default_theme_id
                            )
                            ON CONFLICT (id) DO UPDATE SET
                                name = EXCLUDED.name,
                                priority = EXCLUDED.priority,
                                color = EXCLUDED.color,
                                price = EXCLUDED.price,
                                can_download = EXCLUDED.can_download,
                                can_read = EXCLUDED.can_read,
                                daily_downloads = EXCLUDED.daily_downloads,
                                has_mini_app_access = EXCLUDED.has_mini_app_access,
                                has_library_access = EXCLUDED.has_library_access,
                                can_request_books = EXCLUDED.can_request_books,
                                early_access = EXCLUDED.early_access,
                                custom_themes = EXCLUDED.custom_themes,
                                allow_theme_templates = EXCLUDED.allow_theme_templates,
                                show_recommendations = EXCLUDED.show_recommendations,
                                default_theme_id = EXCLUDED.default_theme_id
                        """),
                        mapped_data,
                    )

                await session.commit()

        except Exception as e:
            logger.error(f"[SYNC_ENGINE] Error in batch level update: {e}")
            raise

    async def _sync_admins_optimized(self):
        """Optimized admin synchronization."""
        if not supabase_manager.is_active:
            return

        try:
            result = supabase_manager.get_client().table("admins").select("*").execute()

            if not result or not result.data:
                return

            admin_ids = {item["user_id"] for item in result.data}
            await self._update_admins_table(admin_ids)

            logger.info(f"[SYNC_ENGINE] Successfully synced {len(admin_ids)} admins")

        except Exception as e:
            logger.error(f"[SYNC_ENGINE] Error in admins sync: {e}")

    async def _update_admins_table(self, admin_ids: set[int]):
        """Updates admins table in local database."""
        try:
            async with pg_manager.get_session() as session:
                # Clear current table
                await session.execute(text("DELETE FROM admins"))

                # Insert current admins
                for admin_id in admin_ids:
                    await session.execute(
                        text("INSERT INTO admins (user_id) VALUES (:user_id)"),
                        {"user_id": admin_id},
                    )

                await session.commit()

        except Exception as e:
            logger.error(f"[SYNC_ENGINE] Error updating admins table: {e}")
            raise

    def _parse_datetime(self, dt_str: str | None) -> datetime | None:
        """Parses ISO datetime string from Supabase."""
        if not dt_str:
            return None

        try:
            # Handle 'Z' suffix and ISO format
            dt_str = dt_str.replace("Z", "+00:00")
            return datetime.fromisoformat(dt_str).astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            return None

    # Public helper methods
    async def mark_user_changed(self, telegram_id: int):
        """Marks a user as changed for synchronization."""
        self.pending_changes["users"].add(telegram_id)

    async def mark_levels_changed(self):
        """Marks user levels as changed."""
        self.pending_changes["user_levels"].add("all")

    async def _sync_series_from_cloud(self):
        """Pulls series metadata from Supabase to local DB (Cloud -> Local)."""
        if not supabase_manager.is_active:
            return

        try:
            logger.info("[SYNC_ENGINE] Pulling series_metadata from Supabase...")
            result = supabase_manager.get_client().table("series_metadata").select("*").execute()

            if not result or not result.data:
                return

            async with pg_manager.get_session() as session:
                for s_data in result.data:
                    # Map Supabase data to local SeriesMetadata
                    # Note: we use series_hash as key
                    mapped_data = {
                        "series_hash": s_data["series_hash"],
                        "series_name": s_data["series_name"],
                        "author": s_data.get("author"),
                        "description": s_data.get("description"),
                        "tags": s_data.get("tags", []),
                        "demographics": s_data.get("demographics", []),
                        "cover_url": s_data.get("cover_url"),
                        "book_type": s_data.get("book_type"),
                        "publisher": s_data.get("publisher"),
                        "author_jap": s_data.get("author_jap"),
                        "rating_average": s_data.get("rating_average", 0.0),
                        "rating_count": s_data.get("rating_count", 0),
                        "book_count": s_data.get("book_count", 0),
                        "slug": s_data.get("slug"),
                    }

                    # JSONB fields handling - Ensure we pass a JSON string for text() queries
                    tags_raw = s_data.get("tags", [])
                    if isinstance(tags_raw, str):
                        try:
                            tags_list = json.loads(tags_raw)
                        except Exception:
                            tags_list = []
                    else:
                        tags_list = tags_raw if isinstance(tags_raw, list) else []

                    mapped_data["tags"] = json.dumps(tags_list)

                    demos_raw = s_data.get("demographics", [])
                    if isinstance(demos_raw, str):
                        try:
                            demos_list = json.loads(demos_raw)
                        except Exception:
                            demos_list = []
                    else:
                        demos_list = demos_raw if isinstance(demos_raw, list) else []

                    mapped_data["demographics"] = json.dumps(demos_list)

                    try:
                        await session.execute(
                            text("""
                                INSERT INTO series_metadata (
                                    series_hash, series_name,
                                    author, description, tags, demographics, cover_url,
                                    book_type, publisher, author_jap, rating_average,
                                    rating_count, book_count, slug
                                ) VALUES (
                                    :series_hash, :series_name,
                                    :author, :description, :tags, :demographics, :cover_url,
                                    :book_type, :publisher, :author_jap, :rating_average,
                                    :rating_count, :book_count, :slug
                                )
                                ON CONFLICT (series_hash) DO UPDATE SET
                                    series_name = EXCLUDED.series_name,
                                    author = EXCLUDED.author,
                                    description = EXCLUDED.description,
                                    tags = EXCLUDED.tags,
                                    demographics = EXCLUDED.demographics,
                                    cover_url = EXCLUDED.cover_url,
                                    book_type = EXCLUDED.book_type,
                                    publisher = EXCLUDED.publisher,
                                    author_jap = EXCLUDED.author_jap,
                                    rating_average = EXCLUDED.rating_average,
                                    rating_count = EXCLUDED.rating_count,
                                    book_count = EXCLUDED.book_count,
                                    slug = EXCLUDED.slug
                            """),
                            mapped_data,
                        )
                    except Exception as row_e:
                        print(
                            f"❌ Error syncing series {mapped_data['series_name']} ({mapped_data['series_hash']}): {row_e}"
                        )
                        # Continue with next series
                await session.commit()
            logger.info(f"[SYNC_ENGINE] Successfully pulled {len(result.data)} series from cloud")

        except Exception as e:
            logger.error(f"[SYNC_ENGINE] Error pulling series from cloud: {e}", exc_info=True)

    async def force_sync_all(self):
        """Triggers an immediate full synchronization."""
        logger.info("[SYNC_ENGINE] Force triggering immediate bidirectional sync...")

        if not config.ENABLE_SUPABASE:
            logger.warning("[SYNC_ENGINE] Supabase is disabled. Skipping force sync.")
            return

        # Pull everything from Supabase
        await self._sync_users_optimized()
        await self._sync_user_levels_optimized()
        await self._sync_admins_optimized()
        await self._sync_series_from_cloud()

        # Reset states
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        for key in self.last_sync_times:
            self.last_sync_times[key] = now_utc
            self.pending_changes[key].clear()

        logger.info("[SYNC_ENGINE] Bidirectional sync completed successfully")

    async def get_sync_status(self) -> dict[str, Any]:
        """Gets the current synchronization status."""
        return {
            "running": self.running,
            "last_sync_times": {k: v.isoformat() for k, v in self.last_sync_times.items()},
            "pending_changes": {k: len(v) for k, v in self.pending_changes.items()},
            "supabase_active": supabase_manager.is_active,
            "postgres_enabled": config.ENABLE_POSTGRES_PLUGIN,
        }


# Global Instance
optimized_sync_engine = OptimizedSyncEngine()
