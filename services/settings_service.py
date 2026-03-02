"""
Servicio para gestionar configuración dinámica persistente (Key-Value).
Backend: PostgreSQL (via SQLAlchemy).
"""

import logging
import os

import sqlalchemy as sa
from sqlalchemy import Column, MetaData, String, Table, Text

from config.config_settings import config

logger = logging.getLogger(__name__)


_engine = None


def _get_sa_engine():
    global _engine
    if _engine is not None:
        return _engine

    if not config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL not configured. PostgreSQL is mandatory.")

    # Force synchronous driver for this module
    db_url = config.DATABASE_URL
    if "postgresql" in db_url or "postgres" in db_url:
        # Standardize prefix and remove async driver
        db_url = db_url.replace("postgres://", "postgresql://")
        db_url = db_url.replace("+asyncpg", "")
        # Force psycopg2
        if "+psycopg2" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")

    _engine = sa.create_engine(db_url, future=True, pool_pre_ping=True)
    return _engine


def init_settings_db():
    """Inicializa la tabla bot_settings."""
    try:
        engine = _get_sa_engine()
        meta = MetaData()
        Table(
            "bot_settings",
            meta,
            Column("key", String(128), primary_key=True),
            Column("value", Text),
        )
        meta.create_all(engine)
    except Exception as e:
        logger.error(f"Error initializing settings DB: {e}")


def get_setting(key: str, default: str = None) -> str | None:
    """Obtiene un valor de configuración."""
    try:
        engine = _get_sa_engine()
        metadata = MetaData()
        settings = Table("bot_settings", metadata, autoload_with=engine)
        with engine.connect() as conn:
            sel = sa.select(settings.c.value).where(settings.c.key == key)
            result = conn.execute(sel).first()
            return result[0] if result else default
    except Exception as e:
        logger.error(f"Error getting setting {key}: {e}")
        return default


def set_setting(key: str, value: str):
    """Guarda o actualiza un valor de configuración."""
    try:
        engine = _get_sa_engine()
        metadata = MetaData()
        settings = Table("bot_settings", metadata, autoload_with=engine)
        with engine.begin() as conn:
            # Upsert logic for Postgres (INSERT ... ON CONFLICT DO UPDATE)
            # Using generic select check for cross-compatibility if engine varies,
            # but here specifically for standard SQL logic.
            sel = sa.select(settings.c.key).where(settings.c.key == key)
            if conn.execute(sel).first():
                upd = settings.update().where(settings.c.key == key).values(value=str(value))
                conn.execute(upd)
            else:
                ins = settings.insert().values(key=key, value=str(value))
                conn.execute(ins)
    except Exception as e:
        logger.error(f"Error setting {key}: {e}")


try:
    if os.getenv("PYTEST_CURRENT_TEST") is None:
        init_settings_db()
except Exception as e:
    logger.error(f"Could not init settings DB: {e}")


class SettingsService:
    """Wrapper asíncrono para los handlers."""

    async def set_setting(self, key: str, value: str):
        import asyncio

        return await asyncio.to_thread(set_setting, key, value)

    async def get_setting(self, key: str, default: str = None) -> str | None:
        import asyncio

        return await asyncio.to_thread(get_setting, key, default)

    async def update_env_variable(self, key: str, value: str) -> bool:
        """
        Actualiza una variable en el archivo .env de forma segura.
        Evita condiciones de carrera y mantiene el formato del archivo.
        """
        import asyncio

        def _update():
            env_path = ".env"
            try:
                lines = []
                if os.path.exists(env_path):
                    with open(env_path, encoding="utf-8") as f:
                        lines = f.readlines()

                new_lines = []
                found = False
                for line in lines:
                    if line.startswith(f"{key}="):
                        new_lines.append(f"{key}={value}\n")
                        found = True
                    else:
                        new_lines.append(line)

                if not found:
                    if new_lines and not new_lines[-1].endswith("\n"):
                        new_lines.append("\n")
                    new_lines.append(f"{key}={value}\n")

                # Escritura atómica usando un archivo temporal
                temp_path = f"{env_path}.tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)

                os.replace(temp_path, env_path)
                return True
            except Exception as e:
                logger.error(f"Error actualizando .env: {e}")
                return False

        return await asyncio.to_thread(_update)
