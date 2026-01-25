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

def _get_sa_engine():
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
    
    return sa.create_engine(db_url, future=True, pool_pre_ping=True)


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
                upd = (
                    settings.update()
                    .where(settings.c.key == key)
                    .values(value=str(value))
                )
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
