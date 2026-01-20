import aiosqlite
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List

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
        """Inicializa la base de datos (WAL mode, integridad y esquemas básicos)."""
        import os
        import shutil
        from datetime import datetime

        if os.path.exists(self.db_path):
            try:
                import sqlite3
                conn_check = sqlite3.connect(self.db_path)
                res = conn_check.execute("PRAGMA integrity_check;").fetchone()
                conn_check.close()
                if res[0] != "ok":
                    logger.error(f"⚠️ BASE DE DATOS {self.db_path} MALFORMADA: {res[0]}")
                    raise sqlite3.DatabaseError("Malformed")
            except Exception as e:
                logger.error(f"❌ Corrupción detectada en {self.db_path}: {e}")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                shutil.move(self.db_path, f"{self.db_path}.corrupt_{timestamp}")
                logger.warning(f"Se ha reseteado la base de datos por corrupción. Backup en .corrupt_{timestamp}")

        async with self.connection() as conn:
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA synchronous=NORMAL")
            await conn.execute("PRAGMA busy_timeout=5000")

            # Crear tabla de niveles si no existe
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    priority INTEGER NOT NULL UNIQUE,
                    color TEXT NOT NULL DEFAULT '#5EAEE6',
                    has_mini_app_access BOOLEAN NOT NULL DEFAULT 0,
                    daily_downloads INTEGER NOT NULL DEFAULT 5,
                    early_access BOOLEAN NOT NULL DEFAULT 0,
                    custom_themes BOOLEAN NOT NULL DEFAULT 0,
                    price FLOAT NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migración: Verificar y añadir nuevas columnas si no existen
            cursor = await conn.execute("PRAGMA table_info(user_levels)")
            tier_cols = [row[1] for row in await cursor.fetchall()]
            new_tier_cols = [
                ("daily_downloads", "INTEGER DEFAULT 5"),
                ("early_access", "BOOLEAN DEFAULT 0"),
                ("custom_themes", "BOOLEAN DEFAULT 0"),
                ("price", "FLOAT DEFAULT 0.0"),
                ("show_recommendations", "BOOLEAN DEFAULT 1"),
                ("ui_theme", "TEXT DEFAULT 'dark'"),
                ("ui_font_size", "INTEGER DEFAULT 14"),
                ("ui_glass_blur", "INTEGER DEFAULT 12"),
                ("ui_cover_width", "INTEGER DEFAULT 120"),
                ("ui_nav_opacity", "FLOAT DEFAULT 0.8"),
                ("ui_accent_opacity", "FLOAT DEFAULT 0.2"),
                ("panel_transparency", "INTEGER DEFAULT 60"),
                ("ui_primary_color", "TEXT DEFAULT '#2b6cee'"),
                ("can_download", "BOOLEAN DEFAULT 1"),
                ("can_read", "BOOLEAN DEFAULT 1"),
                ("ui_glow_intensity", "FLOAT DEFAULT 0.5"),
                ("background_color", "TEXT DEFAULT '#0f172a'"),
                ("card_color", "TEXT DEFAULT '#1e293b'"),
                ("force_settings", "BOOLEAN DEFAULT 0"),
                ("banner_content_offset", "INTEGER DEFAULT 0"),
                ("has_library_access", "BOOLEAN DEFAULT 1"),
                ("can_request_books", "BOOLEAN DEFAULT 1")
            ]
            for col_name, col_def in new_tier_cols:
                if col_name not in tier_cols:
                    print(f"Migración: Añadiendo columna '{col_name}' a tabla user_levels...")
                    await conn.execute(f"ALTER TABLE user_levels ADD COLUMN {col_name} {col_def}")

            # Insertar niveles iniciales si la tabla está vacía
            cursor = await conn.execute("SELECT COUNT(*) FROM user_levels")
            count = (await cursor.fetchone())[0]
            if count == 0:
                # name, priority, color, has_mini_app_access, daily_downloads, early_access, custom_themes, price
                levels = [
                    ('Administrador', 10, '#FF6B6B', 1, 999, 1, 1, 0.0),
                    ('Staff', 9, '#FF9800', 1, 100, 1, 1, 0.0),
                    ('Premium', 5, '#4CAF50', 1, 50, 1, 1, 15.0),
                    ('VIP', 4, '#9C27B0', 1, 20, 1, 0, 5.0),
                    ('Patrocinador', 3, '#2196F3', 1, 10, 0, 0, 2.0),
                    ('Lector', 1, '#9E9E9E', 0, 5, 0, 0, 0.0)
                ]
                await conn.executemany(
                    "INSERT INTO user_levels (name, priority, color, has_mini_app_access, daily_downloads, early_access, custom_themes, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    levels
                )
            else:
                # Actualizar niveles existentes si no tienen los valores por defecto esperados (opcional pero recomendado)
                # Solo para asegurar que los niveles base tengan coherencia tras la migración
                pass

            # Crear tabla de usuarios si no existe
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    role TEXT NOT NULL DEFAULT 'free',
                    level_id INTEGER DEFAULT 6,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    custom_status TEXT,
                    created_by INTEGER,
                    nickname TEXT,
                    name TEXT,
                    username TEXT,
                    roles TEXT DEFAULT '[]',
                    insignias TEXT DEFAULT '[]',
                    settings JSON DEFAULT '{}',
                    total_downloads INTEGER DEFAULT 0,
                    FOREIGN KEY (level_id) REFERENCES user_levels(id)
                )
            """)

            # Migraciones: Verificar y añadir columnas si no existen
            cursor = await conn.execute("PRAGMA table_info(users)")
            cols = [row[1] for row in await cursor.fetchall()]
            
            user_migrations = [
                ('settings', "JSON DEFAULT '{}'"),
                ('nickname', "TEXT"),
                ('name', "TEXT"),
                ('username', "TEXT"),
                ('roles', "TEXT DEFAULT '[]'"),
                ('insignias', "TEXT DEFAULT '[]'"),
                ('level_id', "INTEGER DEFAULT 6"),
                ('total_downloads', "INTEGER DEFAULT 0"),
                ('custom_status', "TEXT"),
                ('expires_at', "TIMESTAMP"),
                ('has_library_access', "BOOLEAN DEFAULT 1"),
                ('can_request_books', "BOOLEAN DEFAULT 1")
            ]
            
            for col_name, col_def in user_migrations:
                if col_name not in cols:
                    try:
                        logger.info(f"Migración: Añadiendo columna '{col_name}' a tabla users...")
                        await conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                    except Exception as e:
                        logger.error(f"Error en migración de columna {col_name}: {e}")

            # Crear índice para level_id si no existe
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_level_id ON users(level_id)")

            # Crear tabla de admins si no existe
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    granted_by INTEGER,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                    FOREIGN KEY (granted_by) REFERENCES users(telegram_id)
                )
            """)

            # Crear tabla de historial de descargas si no existe
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT,
                    download_url TEXT,
                    file_size INTEGER,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
                )
            """)

            # Crear índice para búsquedas rápidas por usuario
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_download_history_user_id
                ON download_history(user_id, downloaded_at DESC)
            """)

            # Migración: Agregar nuevas columnas a download_history para historial enriquecido
            for col in [
                ("romaji_title", "TEXT"),
                ("series", "TEXT"),
                ("volume", "TEXT"),
                ("translator", "TEXT"),
                ("clean_title", "TEXT"),
                ("book_hash", "TEXT")
            ]:
                try:
                    await conn.execute(f"ALTER TABLE download_history ADD COLUMN {col[0]} {col[1]}")
                    logger.info(f"Migración: Agregada columna '{col[0]}' a tabla download_history")
                except Exception as e:
                    if "duplicate column" not in str(e).lower():
                        logger.debug(f"Notice during migration (download_history {col[0]}): {e}")

            # Optimización: Índices para estadísticas
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_download_history_stats
                ON download_history(downloaded_at)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_added_at
                ON users(added_at)
            """)

            await conn.commit()
            logger.info(f"Database initialized and schema verified at {self.db_path}")

    async def get_stats_counts(self, period: str = "day") -> dict:
        """
        Obtiene contadores de descargas y usuarios para un periodo dado.
        period: 'day', 'month', 'year', 'all'
        """
        async with self.connection() as conn:
            if period == "all":
                time_filter = "1=1"
                params = ()
            else:
                # SQLite modifier strings
                modifiers = {
                    "day": "start of day",
                    "month": "start of month",
                    "year": "start of year"
                }
                mod = modifiers.get(period, "start of day")

                time_filter = f"downloaded_at >= datetime('now', '{mod}')"
                params = ()

            # Total Downloads
            cursor = await conn.execute(f"SELECT COUNT(*) FROM download_history WHERE {time_filter}", params)
            downloads = (await cursor.fetchone())[0]

            # Unique Users (Downloaders)
            cursor = await conn.execute(f"SELECT COUNT(DISTINCT user_id) FROM download_history WHERE {time_filter}", params)
            active_users = (await cursor.fetchone())[0]

            # New Users joined
            user_time_filter = time_filter.replace("downloaded_at", "added_at")
            cursor = await conn.execute(f"SELECT COUNT(*) FROM users WHERE {user_time_filter}", params)
            new_users = (await cursor.fetchone())[0]

            return {
                "downloads": downloads,
                "active_users": active_users,
                "new_users": new_users
            }

    @asynccontextmanager
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
                        conn = await aiosqlite.connect(self.db_path, timeout=30)
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
        except Exception as e:
            # Si ocurre un error con la conexión, intentamos cerrarla
            # y no la devolvemos al pool para evitar estados corruptos
            logger.error(f"Error in DB connection context: {e}")
            try:
                await conn.close()
            except Exception as close_error:
                logger.debug(f"Error closing corrupted connection: {close_error}")
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
                    except Exception as e:
                        # Si falla el rollback, descartar conexión
                        logger.warning(f"Rollback failed, discarding connection: {e}")
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
