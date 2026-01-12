import aiosqlite
import asyncio
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class MetricsDatabaseManager:
    """Gestión de la base de datos de métricas de usuario (descargas y valoraciones)."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Inicializa las tablas de métricas basadas en hashes."""
        async with self.connection() as conn:
            await conn.execute("PRAGMA journal_mode=WAL")

            # Tabla de descargas
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    series_hash TEXT,
                    title TEXT,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_downloads_hash ON user_downloads(content_hash)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_downloads_series ON user_downloads(series_hash)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_downloads_user ON user_downloads(user_id, content_hash)")

            # Tabla de valoraciones
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, content_hash)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ratings_hash ON user_ratings(content_hash)")

            await conn.commit()
            logger.info(f"Metrics database initialized at {self.db_path}")

    @asynccontextmanager
    async def connection(self):
        conn = await aiosqlite.connect(self.db_path)
        try:
            yield conn
        finally:
            await conn.close()

# Inicialización global
import os

METRICS_DB_PATH = os.path.join("data", "user_metrics.db")
metrics_db = MetricsDatabaseManager(METRICS_DB_PATH)
