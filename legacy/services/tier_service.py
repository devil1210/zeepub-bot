import logging
from typing import Any

from repositories.user_repository import user_repo
from services.cache_service import AsyncTTLCache

logger = logging.getLogger(__name__)


class TierService:
    """
    Service for managing User Tiers (Levels) with caching.
    Optimizes access to tier-related configurations.
    """

    def __init__(self):
        # Cache for all tiers list (2 hours - tiers change very rarely)
        self.all_tiers_cache = AsyncTTLCache(ttl_seconds=7200)
        # Cache for individual tiers (1 hour)
        self.tier_cache = AsyncTTLCache(ttl_seconds=3600)

    async def get_all_tiers(self, use_cache: bool = True) -> list[dict[str, Any]]:
        """Returns all available user tiers, with caching."""
        cache_key = "all_tiers_list"
        if use_cache:
            cached = await self.all_tiers_cache.get(cache_key)
            if cached:
                return cached

        tiers = await user_repo.get_all_levels()
        await self.all_tiers_cache.set(cache_key, tiers)
        return tiers

    async def get_tier_by_id(self, tier_id: int) -> dict[str, Any] | None:
        """Gets a specific tier by ID with caching."""
        cache_key = f"tier:id:{tier_id}"
        cached = await self.tier_cache.get(cache_key)
        if cached:
            return cached

        tier = await user_repo.get_level_by_id(tier_id)
        if tier:
            await self.tier_cache.set(cache_key, tier)
        return tier

    async def update_tier(self, tier_id: int, tier_data: dict[str, Any]) -> bool:
        """Updates a tier and invalidates relevant caches."""
        success = await user_repo.update_level(tier_id, tier_data)
        if success:
            await self.invalidate_caches()
            await self.tier_cache.invalidate(f"tier:id:{tier_id}")
        return success

    async def invalidate_caches(self):
        """Clears all tier-related caches."""
        await self.all_tiers_cache.invalidate("all_tiers_list")
        logger.info("Tier caches invalidated")


tier_service = TierService()
