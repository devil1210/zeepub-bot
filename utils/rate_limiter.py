import time
import asyncio
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class RateLimitType(Enum):
    DOWNLOAD = "download"
    COMMAND = "command"
    SEARCH = "search"
    DEFAULT = "default"


@dataclass
class RateLimit:
    max_requests: int
    window_seconds: int
    requests: List[float]


class RateLimitManager:
    def __init__(self):
        self._limits: Dict[int, Dict[RateLimitType, RateLimit]] = {}
        self._lock = asyncio.Lock()
        self._default_limits: Dict[RateLimitType, tuple[int, int]] = {}

    def set_default_limit(
        self, limit_type: RateLimitType, max_requests: int, window_seconds: int
    ):
        self._default_limits[limit_type] = (max_requests, window_seconds)

    async def _ensure_user(self, user_id: int):
        if user_id not in self._limits:
            self._limits[user_id] = {}

    async def _cleanup_old_requests(self, rate_limit: RateLimit):
        now = time.time()
        # Keep only requests within the window
        rate_limit.requests = [
            t for t in rate_limit.requests if now - t < rate_limit.window_seconds
        ]

    async def add_limit(
        self,
        user_id: int,
        limit_type: RateLimitType,
        max_requests: int,
        window_seconds: int,
    ):
        async with self._lock:
            await self._ensure_user(user_id)
            self._limits[user_id][limit_type] = RateLimit(
                max_requests=max_requests, window_seconds=window_seconds, requests=[]
            )

    async def is_allowed(self, user_id: int, limit_type: RateLimitType) -> bool:
        async with self._lock:
            await self._ensure_user(user_id)

            # If no limit explicitly set, try to use default
            if limit_type not in self._limits[user_id]:
                if limit_type in self._default_limits:
                    mx, win = self._default_limits[limit_type]
                    self._limits[user_id][limit_type] = RateLimit(mx, win, [])
                else:
                    # No limit defined = allowed
                    return True

            rate_limit = self._limits[user_id][limit_type]
            await self._cleanup_old_requests(rate_limit)

            if len(rate_limit.requests) < rate_limit.max_requests:
                rate_limit.requests.append(time.time())
                return True
            return False

    async def get_remaining(self, user_id: int, limit_type: RateLimitType) -> int:
        async with self._lock:
            await self._ensure_user(user_id)
            if limit_type not in self._limits[user_id]:
                if limit_type in self._default_limits:
                    # Logic to treat it as if new
                    return self._default_limits[limit_type][0]
                return 9999  # Infinite

            rate_limit = self._limits[user_id][limit_type]
            await self._cleanup_old_requests(rate_limit)
            return max(0, rate_limit.max_requests - len(rate_limit.requests))


# Global instance
rate_limiter = RateLimitManager()


def create_rate_limit_manager_from_config(config):
    # This might be deprecated with the global instance,
    # but keeping signature for compatibility if needed.
    return rate_limiter
