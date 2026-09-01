# services/cache_service.py
"""
Servicio de Caché en Memoria Asíncrono (LRU + TTL) con soporte de invalidación por tags y prefijos.
Optimiza el rendimiento del bot reduciendo consultas redundantes a PostgreSQL.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


class CacheEntry:
    __slots__ = ("value", "expires_at", "tags")

    def __init__(self, value: Any, expires_at: float, tags: list[str] | None = None):
        self.value = value
        self.expires_at = expires_at
        self.tags = set(tags or [])


class AsyncLRUCache:
    """Caché asíncrono con control de expiración (TTL) y límite de capacidad."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300, ttl_seconds: int | None = None):
        self.max_size = max_size
        self.default_ttl = ttl_seconds if ttl_seconds is not None else default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._tag_map: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Obtiene un valor de la caché si no ha expirado."""
        entry = self._cache.get(key)
        if not entry:
            return None

        if time.time() > entry.expires_at:
            async with self._lock:
                self._evict(key)
            return None

        return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Almacena un valor en la caché con TTL y etiquetas de invalidación."""
        ttl_val = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + ttl_val
        entry = CacheEntry(value=value, expires_at=expires_at, tags=tags)

        async with self._lock:
            # Límite de tamaño: evict si se supera
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Eliminar el primer elemento (más antiguo)
                oldest_key = next(iter(self._cache))
                self._evict(oldest_key)

            self._cache[key] = entry
            if tags:
                for tag in tags:
                    self._tag_map.setdefault(tag, set()).add(key)

    def _evict(self, key: str) -> None:
        """Elimina una clave y limpia referencias en _tag_map."""
        entry = self._cache.pop(key, None)
        if entry and entry.tags:
            for tag in entry.tags:
                if tag in self._tag_map:
                    self._tag_map[tag].discard(key)
                    if not self._tag_map[tag]:
                        del self._tag_map[tag]

    async def invalidate_tag(self, tag: str) -> int:
        """Invalida todas las entradas asociadas a una etiqueta."""
        async with self._lock:
            keys_to_remove = list(self._tag_map.get(tag, set()))
            for k in keys_to_remove:
                self._evict(k)
            return len(keys_to_remove)

    async def invalidate_prefix(self, prefix: str) -> int:
        """Invalida todas las entradas cuya clave empiece con el prefijo."""
        async with self._lock:
            keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
            for k in keys_to_remove:
                self._evict(k)
            return len(keys_to_remove)

    async def delete(self, key: str) -> None:
        """Elimina una clave específica de la caché."""
        async with self._lock:
            self._evict(key)

    async def clear(self) -> None:
        """Limpia toda la caché."""
        async with self._lock:
            self._cache.clear()
            self._tag_map.clear()


# Alias para compatibilidad hacia atrás
AsyncTTLCache = AsyncLRUCache

# Instancia global de caché de catálogo
catalog_cache = AsyncLRUCache(max_size=2000, default_ttl=300)


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
            # Generar clave única
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
