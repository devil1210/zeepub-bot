from datetime import datetime, timedelta
import asyncio
from typing import Any, Tuple, Optional, Dict


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
        ⚠️ LECTURA SIN LOCK: Safe porque:
        - GIL protege dict lookup atomicity
        - Peor caso: lectura de valor expirado (se descarta, re-fetch en DB)
        - Mejor que contención de lock con 1000+ mensajes/segundo
        """
        if key in self._cache:
            value, timestamp = self._cache[key]
            # Verificar expiration sin lock
            if datetime.now() - timestamp < timedelta(seconds=self._ttl):
                return value
            # Expirado: volverá a hacer lookup en DB
        return None

    async def set(self, key: str, value: Any):
        """Guarda un valor en el caché con timestamp actual. Lock para escritura segura."""
        async with self._write_lock:
            self._cache[key] = (value, datetime.now())

    async def invalidate(self, key: Optional[str] = None):
        """Invalida una clave específica o todo el caché."""
        async with self._write_lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()

    async def cleanup(self):
        """Limpieza periódica de elementos expirados (opcional)."""
        async with self._write_lock:
            now = datetime.now()
            keys_to_remove = [
                k
                for k, (v, ts) in self._cache.items()
                if now - ts > timedelta(seconds=self._ttl)
            ]
            for k in keys_to_remove:
                del self._cache[k]
