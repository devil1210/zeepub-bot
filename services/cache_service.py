import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class MemoryCache:
    """Cache en memoria con TTL y LRU eviction."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, datetime] = {}
        
    def get(self, key: str) -> Optional[Any]:
        """Obtiene valor del cache."""
        if key not in self.cache:
            return None
            
        item = self.cache[key]
        now = datetime.utcnow()
        
        # Verificar TTL
        if item['expires_at'] < now:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return None
            
        # Actualizar tiempo de acceso
        self.access_times[key] = now
        return item['value']
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Establece valor en cache."""
        now = datetime.utcnow()
        
        # Evict si es necesario
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()
            
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires_at': now + timedelta(seconds=ttl),
            'created_at': now
        }
        self.access_times[key] = now
        
    def invalidate(self, key: str) -> None:
        """Invalida una clave específica."""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_times:
            del self.access_times[key]
            
    def clear_pattern(self, pattern: str) -> None:
        """Limpia claves que coinciden con patrón."""
        keys_to_remove = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_remove:
            self.invalidate(key)
            
    def _evict_lru(self) -> None:
        """Elimina el elemento menos usado recientemente."""
        if not self.access_times:
            return
            
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        self.invalidate(lru_key)
        
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache."""
        now = datetime.utcnow()
        expired = sum(1 for item in self.cache.values() if item['expires_at'] < now)
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'expired': expired,
            'hit_rate': getattr(self, '_hits', 0) / max(getattr(self, '_requests', 1), 1)
        }

class AsyncTTLCache:
    """
    Cache asíncrono con Time-To-Live (TTL) optimizado para alto volumen.
    Usa lecturas sin lock (thread-safe con GIL) y lock solo para escrituras.
    Ideal para patrones read-heavy como get_effective_user() que se llama por cada mensaje.
    """

    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._ttl = ttl_seconds
        self._write_lock = asyncio.Lock()  # Solo para escrituras y limpieza

    async def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del caché si existe y no ha expirado.
        """
        if key in self._cache:
            value, expires_at = self._cache[key]
            if datetime.utcnow() < expires_at:
                return value
            else:
                # Expired, clean up lazily
                del self._cache[key]
        return None

    async def set(self, key: str, value: Any, custom_ttl: Optional[int] = None) -> None:
        """
        Establece un valor en el caché con TTL.
        """
        ttl = custom_ttl if custom_ttl is not None else self._ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        async with self._write_lock:
            self._cache[key] = (value, expires_at)

    async def invalidate(self, key: str) -> None:
        """
        Invalida una clave específica del caché.
        """
        async with self._write_lock:
            self._cache.pop(key, None)

    async def clear_pattern(self, pattern: str) -> None:
        """
        Invalida todas las claves que coinciden con un patrón.
        """
        async with self._write_lock:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._cache.pop(key, None)

    async def cleanup_expired(self) -> int:
        """
        Limpia entradas expiradas. Retorna cuántas se limpiaron.
        """
        now = datetime.utcnow()
        async with self._write_lock:
            expired_keys = [k for k, (_, expires_at) in self._cache.items() if expires_at < now]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    async def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas básicas del caché.
        """
        now = datetime.utcnow()
        total_entries = len(self._cache)
        expired_entries = sum(1 for _, expires_at in self._cache.values() if expires_at < now)
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "valid_entries": total_entries - expired_entries,
            "ttl_seconds": self._ttl
        }

class CacheManager:
    """Gestor de cache multinivel para el bot."""
    
    def __init__(self):
        self.memory_cache = MemoryCache(max_size=2000, default_ttl=300)
        self.user_cache = AsyncTTLCache(ttl_seconds=300)
        self.settings_cache = AsyncTTLCache(ttl_seconds=600)
        self.level_cache = AsyncTTLCache(ttl_seconds=1800)
        self.theme_cache = AsyncTTLCache(ttl_seconds=600)
        self._hits = 0
        self._requests = 0
        
    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene usuario desde cache."""
        self._requests += 1
        
        # Intentar memoria primero
        user = self.memory_cache.get(f"user:{telegram_id}")
        if user:
            self._hits += 1
            return user
            
        # Intentar cache específico de usuarios
        user = await self.user_cache.get(f"user:{telegram_id}")
        if user:
            self._hits += 1
            # Guardar en memoria cache también
            self.memory_cache.set(f"user:{telegram_id}", user, 300)
            return user
            
        return None
        
    async def set_user(self, telegram_id: int, user_data: Dict[str, Any], ttl: int = 300) -> None:
        """Guarda usuario en cache."""
        await self.user_cache.set(f"user:{telegram_id}", user_data, ttl)
        self.memory_cache.set(f"user:{telegram_id}", user_data, ttl)
        
    async def invalidate_user(self, telegram_id: int) -> None:
        """Invalida cache de un usuario."""
        await self.user_cache.invalidate(f"user:{telegram_id}")
        self.memory_cache.invalidate(f"user:{telegram_id}")

    async def delete_user(self, telegram_id: int) -> None:
        """Alias para invalidate_user (compatibilidad con user_repository)."""
        await self.invalidate_user(telegram_id)
        
    async def get_user_effective(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene usuario efectivo (con defaults)."""
        user = await self.get_user(telegram_id)
        if user:
            return user
            
        # Cache miss - debería venir de DB
        return None
        
    async def get_user_settings(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene configuración de usuario."""
        settings = self.memory_cache.get(f"settings:{telegram_id}")
        if settings:
            return settings
            
        settings = await self.settings_cache.get(f"settings:{telegram_id}")
        if settings:
            self.memory_cache.set(f"settings:{telegram_id}", settings, 600)
            return settings
            
        return None
        
    async def set_user_settings(self, telegram_id: int, settings: Dict[str, Any], ttl: int = 600) -> None:
        """Guarda configuración de usuario."""
        await self.settings_cache.set(f"settings:{telegram_id}", settings, ttl)
        self.memory_cache.set(f"settings:{telegram_id}", settings, ttl)
        
    async def invalidate_user_settings(self, telegram_id: int) -> None:
        """Invalida configuración de usuario."""
        await self.settings_cache.invalidate(f"settings:{telegram_id}")
        self.memory_cache.invalidate(f"settings:{telegram_id}")
        
    async def get_user_level(self, level_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene nivel de usuario."""
        level = self.memory_cache.get(f"level:{level_id}")
        if level:
            return level
            
        level = await self.level_cache.get(f"level:{level_id}")
        if level:
            self.memory_cache.set(f"level:{level_id}", level, 1800)
            return level
            
        return None
        
    async def set_user_level(self, level_id: int, level_data: Dict[str, Any], ttl: int = 1800) -> None:
        """Guarda nivel de usuario."""
        await self.level_cache.set(f"level:{level_id}", level_data, ttl)
        self.memory_cache.set(f"level:{level_id}", level_data, ttl)
        
    async def invalidate_level(self, level_id: int) -> None:
        """Invalida nivel."""
        await self.level_cache.invalidate(f"level:{level_id}")
        self.memory_cache.invalidate(f"level:{level_id}")
        
    async def get_themes(self) -> Optional[List[Dict[str, Any]]]:
        """Obtiene temas cacheados."""
        themes = self.memory_cache.get("themes:all")
        if themes:
            return themes
            
        themes = await self.theme_cache.get("themes:all")
        if themes:
            self.memory_cache.set("themes:all", themes, 600)
            return themes
            
        return None
        
    async def set_themes(self, themes: List[Dict[str, Any]], ttl: int = 600) -> None:
        """Guarda temas en cache."""
        await self.theme_cache.set("themes:all", themes, ttl)
        self.memory_cache.set("themes:all", themes, ttl)
        
    async def invalidate_themes(self) -> None:
        """Invalida cache de temas."""
        await self.theme_cache.invalidate("themes:all")
        self.memory_cache.invalidate("themes:all")
        
    async def get_sync_status(self) -> Optional[Dict[str, Any]]:
        """Obtiene estado de sincronización."""
        status = self.memory_cache.get("sync:status")
        if status:
            return status
            
        return None
        
    async def set_sync_status(self, status: Dict[str, Any], ttl: int = 60) -> None:
        """Guarda estado de sincronización."""
        self.memory_cache.set("sync:status", status, ttl)
        
    async def clear_user_cache(self, telegram_id: int) -> None:
        """Limpia todo el cache de un usuario."""
        self.memory_cache.clear_pattern(f"user:{telegram_id}")
        self.memory_cache.clear_pattern(f"settings:{telegram_id}")
        await self.user_cache.invalidate(f"user:{telegram_id}")
        await self.settings_cache.invalidate(f"settings:{telegram_id}")
        
    async def clear_all_user_cache(self) -> None:
        """Limpia todo el cache de usuarios."""
        self.memory_cache.clear_pattern("user:")
        self.memory_cache.clear_pattern("settings:")
        await self.user_cache.clear_pattern("user:")
        await self.settings_cache.clear_pattern("settings:")
        
    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache."""
        memory_stats = self.memory_cache.get_stats()
        user_stats = await self.user_cache.get_stats()
        settings_stats = await self.settings_cache.get_stats()
        level_stats = await self.level_cache.get_stats()
        theme_stats = await self.theme_cache.get_stats()
        
        return {
            'memory_cache': memory_stats,
            'user_cache': user_stats,
            'settings_cache': settings_stats,
            'level_cache': level_stats,
            'theme_cache': theme_stats,
            'overall_hit_rate': self._hits / max(self._requests, 1),
            'total_requests': self._requests,
            'total_hits': self._hits
        }
        
    async def cleanup_expired(self) -> None:
        """Limpia elementos expirados."""
        await self.user_cache.cleanup_expired()
        await self.settings_cache.cleanup_expired()
        await self.level_cache.cleanup_expired()
        await self.theme_cache.cleanup_expired()

# Instancia global
cache_manager = CacheManager()
