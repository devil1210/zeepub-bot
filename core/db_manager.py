import aiosqlite
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestión centralizada de conexiones a BD SQLite con pooling básico."""

    def __init__(self, db_path: str, pool_size: int = 20):
        self.db_path = db_path
        self._pool: List[aiosqlite.Connection] = []
        self._pool_size = pool_size
        self._lock = asyncio.Lock()
        self._active_connections = 0

    async def initialize(self):
        """Inicializa la base de datos (WAL mode)."""
        async with self.connection() as conn:
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA synchronous=NORMAL")
            logger.info(f"Database initialized at {self.db_path} (WAL mode enabled)")

    async def connection(self):
        """Context manager para obtener conexión del pool con retry logic."""
        conn = None
        start_time = asyncio.get_event_loop().time()
        timeout = 5.0  # Tiempo máximo de espera

        # Esperar hasta que haya una conexión disponible
        while True:
            async with self._lock:
                if self._pool:
                    conn = self._pool.pop()
                    break
                elif self._active_connections < self._pool_size:
                    # Crear nueva conexión
                    try:
                        conn = await aiosqlite.connect(self.db_path)
                        self._active_connections += 1
                        break
                    except Exception as e:
                        logger.error(f"Error connecting to DB: {e}")
                        raise

            # Si llegamos aquí, el pool está lleno. Verificar timeout.
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise asyncio.TimeoutError("Timeout waiting for DB connection")

            # Esperar un poco antes de reintentar (optimizado 10ms vs 100ms)
            from asyncio import sleep
            await sleep(0.005)

        try:
            yield conn
        except Exception:
            # Si ocurre un error con la conexión, intentamos cerrarla
            # y no la devolvemos al pool para evitar estados corruptos
            try:
                await conn.close()
            except Exception:
                pass
            async with self._lock:
                self._active_connections -= 1
            raise
        else:
            # Si todo salió bien, devolver al pool
            async with self._lock:
                # Verificar si el pool tiene espacio (por si acaso se cambió el tamaño)
                # O si queremos mantener límite estricto
                if len(self._pool) < self._pool_size:
                    try:
                        await conn.rollback()  # Reset state
                        self._pool.append(conn)
                    except Exception:
                        # Si falla el rollback, descartar conexión
                        await conn.close()
                        self._active_connections -= 1
                else:
                    await conn.close()
                    self._active_connections -= 1

    async def close_all(self):
        """Cierra todas las conexiones del pool."""
        async with self._lock:
            while self._pool:
                conn = self._pool.pop()
                await conn.close()
            logger.info("All DB connections closed.")


from config.config_settings import config

db_manager = DatabaseManager(config.URL_CACHE_DB_PATH)
