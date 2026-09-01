# services/cache_service.py
"""
Servicio de Caché Unificado para ZeePub (Memoria, Async TTL, LRU con Tags e Invalidación).
Optimiza el rendimiento del bot reduciendo consultas redundantes a PostgreSQL.
"""

import asyncio
import functools
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable

logger = logging.getLogger(__name__)


class CacheEntry:
    __slots__ = ("value", "expires_at", "tags")

    def __init__(self, value: Any, expires_at: float, tags: list[str] | None = None):
        self.value = value
        self.expires_at = expires_at
        self.tags = set(tags or [])


class MemoryCache:
    """Caché sincrónico en memoria con soporte de patrones."""

    def __init__(self, max_size: int = 2000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: dict[str, tuple[Any, float]] = {}
        self._requests = 0
        self._hits = 0

    def get(self, key: str) -> Any | None:
        self._requests += 1
        if key not in self.cache:
            return None
        value, expires_at = self.cache[key]
        if time.time() > expires_at:
            del self.cache[key]
            return None
        self._hits += 1
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl_val = ttl if ttl is not None else self.default_ttl
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        self.cache[key] = (value, time.time() + ttl_val)

    def delete(self, key: str) -> None:
        self.cache.pop(key, None)

    def clear_pattern(self, pattern: str) -> int:
        keys_to_del = [k for k in self.cache if pattern in k]
        for k in keys_to_del:
            del self.cache[k]
        return len(keys_to_del)

    def get_stats(self) -> dict[str, Any]:
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "requests": self._requests,
            "hits": self._hits,
            "hit_rate": self._hits / max(self._requests, 1),
        }


class AsyncLRUCache:
    """Caché asíncrono LRU con control de expiración (TTL) y límite de capacidad."""

    def __init__(self, max_size: int = 2000, default_ttl: int = 300, ttl_seconds: int | None = None):
        self.max_size = max_size
        self.default_ttl = ttl_seconds if ttl_seconds is not None else default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._tag_map: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()
        self._requests = 0
        self._hits = 0

    async def get(self, key: str) -> Any | None:
        self._requests += 1
        entry = self._cache.get(key)
        if not entry:
            return None

        if time.time() > entry.expires_at:
            async with self._lock:
                self._evict(key)
            return None

        self._hits += 1
        return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        ttl_seconds: int | None = None,
        tags: list[str] | None = None,
    ) -> None:
        effective_ttl = ttl if ttl is not None else (ttl_seconds if ttl_seconds is not None else self.default_ttl)
        expires_at = time.time() + effective_ttl
        entry = CacheEntry(value=value, expires_at=expires_at, tags=tags)

        async with self._lock:
            if len(self._cache) >= self.max_size and key not in self._cache:
                oldest_key = next(iter(self._cache))
                self._evict(oldest_key)

            self._cache[key] = entry
            if tags:
                for tag in tags:
                    self._tag_map.setdefault(tag, set()).add(key)

    def _evict(self, key: str) -> None:
        entry = self._cache.pop(key, None)
        if entry and entry.tags:
            for tag in entry.tags:
                if tag in self._tag_map:
                    self._tag_map[tag].discard(key)
                    if not self._tag_map[tag]:
                        del self._tag_map[tag]

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._evict(key)

    async def invalidate(self, key: str) -> None:
        await self.delete(key)

    async def clear_pattern(self, pattern: str) -> int:
        async with self._lock:
            keys_to_del = [k for k in self._cache if pattern in k]
            for k in keys_to_del:
                self._evict(k)
            return len(keys_to_del)

    async def invalidate_tag(self, tag: str) -> int:
        async with self._lock:
            keys_to_remove = list(self._tag_map.get(tag, set()))
            for k in keys_to_remove:
                self._evict(k)
            return len(keys_to_remove)

    async def invalidate_prefix(self, prefix: str) -> int:
        async with self._lock:
            keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
            for k in keys_to_remove:
                self._evict(k)
            return len(keys_to_remove)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()
            self._tag_map.clear()

    async def cleanup_expired(self) -> int:
        now = time.time()
        async with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.expires_at < now]
            for k in expired_keys:
                self._evict(k)
            return len(expired_keys)

    async def get_stats(self) -> dict[str, Any]:
        return {
            "total_entries": len(self._cache),
            "requests": self._requests,
            "hits": self._hits,
            "hit_rate": self._hits / max(self._requests, 1),
        }


# Alias para compatibilidad hacia atrás
AsyncTTLCache = AsyncLRUCache


class CacheManager:
    """Administrador centralizado de cachés del sistema."""

    def __init__(self):
        self.memory_cache = MemoryCache(max_size=3000, default_ttl=300)
        self.user_cache = AsyncLRUCache(max_size=2000, default_ttl=600)
        self.settings_cache = AsyncLRUCache(max_size=1000, default_ttl=600)
        self.level_cache = AsyncLRUCache(max_size=100, default_ttl=1800)
        self.theme_cache = AsyncLRUCache(max_size=100, default_ttl=3600)
        self._requests = 0
        self._hits = 0

    async def get_user(self, telegram_id: int) -> dict[str, Any] | None:
        self._requests += 1
        user = self.memory_cache.get(f"user:{telegram_id}")
        if user:
            self._hits += 1
            return user
        user = await self.user_cache.get(f"user:{telegram_id}")
        if user:
            self._hits += 1
            self.memory_cache.set(f"user:{telegram_id}", user, 300)
            return user
        return None

    async def set_user(self, telegram_id: int, user_data: dict[str, Any], ttl: int = 300) -> None:
        await self.user_cache.set(f"user:{telegram_id}", user_data, ttl)
        self.memory_cache.set(f"user:{telegram_id}", user_data, ttl)

    async def invalidate_user(self, telegram_id: int) -> None:
        self.memory_cache.delete(f"user:{telegram_id}")
        self.memory_cache.clear_pattern(f"user:{telegram_id}")
        await self.user_cache.delete(f"user:{telegram_id}")

    async def delete_user(self, telegram_id: int) -> None:
        await self.invalidate_user(telegram_id)

    async def invalidate_series(self, series_id: str) -> None:
        self.memory_cache.clear_pattern(f"series:{series_id}")
        self.memory_cache.clear_pattern("grid:")
        await catalog_cache.invalidate_tag("series")
        await catalog_cache.invalidate_tag("volumes")

    async def delete_series(self, series_id: str) -> None:
        await self.invalidate_series(series_id)

    async def invalidate_book(self, book_id: str) -> None:
        self.memory_cache.clear_pattern(f"book:{book_id}")
        self.memory_cache.clear_pattern("grid:")
        await catalog_cache.invalidate_tag("volumes")

    async def delete_book(self, book_id: str) -> None:
        await self.invalidate_book(book_id)

    async def get_stats(self) -> dict[str, Any]:
        return {
            "memory_cache": self.memory_cache.get_stats(),
            "user_cache": await self.user_cache.get_stats(),
            "catalog_cache": await catalog_cache.get_stats(),
            "overall_hit_rate": self._hits / max(self._requests, 1),
        }

    async def cleanup_expired(self) -> None:
        await self.user_cache.cleanup_expired()
        await self.settings_cache.cleanup_expired()
        await self.level_cache.cleanup_expired()
        await self.theme_cache.cleanup_expired()
        await catalog_cache.cleanup_expired()


# Instancias globales
cache_manager = CacheManager()
catalog_cache = AsyncLRUCache(max_size=3000, default_ttl=300)


def cached(
    ttl: int = 300,
    tag: str | None = None,
    key_builder: Callable[..., str] | None = None,
):
    """
    Decorador para métodos asíncronos que cachea su resultado automáticamente.
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                args_str = ":".join(str(a) for a in args[1:] if a is not None)
                kwargs_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
                cache_key = f"{func.__qualname__}:{args_str}:{kwargs_str}"

            cached_val = await catalog_cache.get(cache_key)
            if cached_val is not None:
                return cached_val

            result = await func(*args, **kwargs)
            if result is not None:
                tags = [tag] if tag else []
                await catalog_cache.set(cache_key, result, ttl=ttl, tags=tags)

            return result

        return wrapper

    return decorator
