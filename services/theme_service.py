import logging
from typing import Any, Dict, List, Optional
from repositories.theme_repository import theme_repo
from services.cache_service import AsyncTTLCache

logger = logging.getLogger(__name__)

class ThemeService:
    """
    Service for managing application themes with a high-performance caching layer.
    Optimizes performance for the Mini App and Bot interactions.
    """
    
    def __init__(self):
        # Cache for all themes list (1 hour)
        self.all_themes_cache = AsyncTTLCache(ttl_seconds=3600)
        # Cache for individual themes (30 minutes)
        self.theme_cache = AsyncTTLCache(ttl_seconds=1800)

    async def get_all_themes(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Returns all available theme templates, with caching."""
        cache_key = "all_themes_list"
        if use_cache:
            cached = await self.all_themes_cache.get(cache_key)
            if cached:
                return cached

        themes = await theme_repo.get_all_themes()
        await self.all_themes_cache.set(cache_key, themes)
        return themes

    async def get_theme_by_id(self, theme_id: int) -> Optional[Dict[str, Any]]:
        """Gets a specific theme by ID with caching."""
        cache_key = f"theme:id:{theme_id}"
        cached = await self.theme_cache.get(cache_key)
        if cached:
            return cached

        theme = await theme_repo.get_by_id(theme_id)
        if theme:
            await self.theme_cache.set(cache_key, theme)
        return theme

    async def save_theme(self, theme_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves or updates a theme and invalidates relevant caches."""
        result = await theme_repo.upsert(theme_data)
        if result:
            await self.invalidate_caches()
            # Also cache this specific one immediately
            if result.get("id"):
                await self.theme_cache.set(f"theme:id:{result['id']}", result)
        return result

    async def delete_theme(self, theme_id: int) -> bool:
        """Deletes a theme and clears caches."""
        success = await theme_repo.delete(theme_id)
        if success:
            await self.invalidate_caches()
            await self.theme_cache.invalidate(f"theme:id:{theme_id}")
        return success

    async def invalidate_caches(self):
        """Clears all theme-related caches."""
        await self.all_themes_cache.invalidate("all_themes_list")
        # Note: We can't easily clear all individual theme caches without scanning, 
        # but the master list invalidation is usually enough for UI refreshes.
        logger.info("Theme caches invalidated")

theme_service = ThemeService()
