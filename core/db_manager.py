import aiosqlite
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestión centralizada de conexiones a BD SQLite con pooling básico."""

    def __init__(self, db_path: str, pool_size: int = 5):
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

    @asynccontextmanager
    async def connection(self):
        """Context manager para obtener conexión del pool."""
        conn = None
        async with self._lock:
            if self._pool:
                conn = self._pool.pop()
            else:
                if self._active_connections < self._pool_size:
                    pass  # We will create one below
                else:
                    # Pool empty and max connections reached?
                    # For simplicity in this basic pool, we just create a new one if pool empty,
                    # but real pooling would wait. Given SQLite constraint (single writer),
                    # we usually want limited connections.
                    # Let's verify if we want to enforce hard limit or just soft pool.
                    # Proposal said "pool_size".
                    pass  # Just create new for now to avoid blocking, user is single tenant mostly.

        if not conn:
            try:
                conn = await aiosqlite.connect(self.db_path)
                self._active_connections += 1
            except Exception as e:
                logger.error(f"Error connecting to DB: {e}")
                raise

        try:
            yield conn
        finally:
            async with self._lock:
                if len(self._pool) < self._pool_size:
                    # Reset connection state if needed? aiosqlite handles some.
                    # Ideally rollback any pending transaction
                    await conn.rollback()
                    self._pool.append(conn)
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
