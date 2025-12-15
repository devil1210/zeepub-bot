from functools import lru_cache
from datetime import datetime, timedelta
import asyncio
from typing import Any, Tuple, Optional, Dict

class AsyncTTLCache:
    """
    Cache asíncrono con Time-To-Live (TTL).
    Permite almacenar resultados de consultas u operaciones costosas por un tiempo definido.
    """
    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché si existe y no ha expirado."""
        async with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if datetime.now() - timestamp < timedelta(seconds=self._ttl):
                    return value
                else:
                    # Expirado, limpiar
                    del self._cache[key]
        return None
    
    async def set(self, key: str, value: Any):
        """Guarda un valor en el caché con timestamp actual."""
        async with self._lock:
            self._cache[key] = (value, datetime.now())
    
    async def invalidate(self, key: Optional[str] = None):
        """Invalida una clave específica o todo el caché."""
        async with self._lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()

    async def cleanup(self):
        """Limpieza periódica de elementos expirados (opcional)."""
        async with self._lock:
            now = datetime.now()
            keys_to_remove = [
                k for k, (v, ts) in self._cache.items()
                if now - ts > timedelta(seconds=self._ttl)
            ]
            for k in keys_to_remove:
                del self._cache[k]
