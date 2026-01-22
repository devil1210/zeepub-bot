"""
Sistema de caché persistente para URLs acortadas usando PostgreSQL (via SQLAlchemy).
"""

import hashlib
import logging
from typing import Optional
from config.config_settings import config
import sqlalchemy as sa
from sqlalchemy import (
    Table,
    Column,
    String,
    Text,
    Integer,
    Boolean,
    MetaData,
    DateTime,
)
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

def _get_sa_engine():
    if not config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL not configured. PostgreSQL is mandatory.")
    
    db_url = config.DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    # Force synchronous driver for this module
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")
    
    if "postgresql" in db_url and "+psycopg2" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")
    
    engine = sa.create_engine(db_url, future=True, pool_pre_ping=True)
    return engine

def init_db():
    """Inicializa la tabla url_mappings en PostgreSQL."""
    try:
        engine = _get_sa_engine()
        meta = MetaData()
        Table(
            "url_mappings",
            meta,
            Column("hash", String(128), primary_key=True),
            Column("url", Text, nullable=False),
            Column("book_title", Text),
            Column("series_name", Text),
            Column("volume_number", Text),
            Column("created_at", DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
            Column("last_checked", DateTime),
            Column("is_valid", Boolean, server_default=sa.true()),
            Column("failed_checks", Integer, server_default="0"),
        )
        meta.create_all(engine)
        logger.info("URL cache database initialized in PostgreSQL.")
    except Exception as e:
        logger.error(f"Failed to initialize URL cache DB: {e}")

def create_short_url(
    url: str, book_title: str = None, series_name: str = None, volume_number: str = None
) -> str:
    """
    Crea un hash corto para una URL y lo guarda en Postgres.
    """
    try:
        engine = _get_sa_engine()
        metadata = MetaData()
        url_mappings = Table("url_mappings", metadata, autoload_with=engine)

        full_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        base_len = 12
        url_hash = full_hash[:base_len]

        with engine.begin() as conn:
            # Check if URL already exists
            sel = sa.select(url_mappings.c.hash).where(url_mappings.c.url == url)
            r = conn.execute(sel).first()
            if r:
                existing_hash = r[0]
                if book_title:
                    upd = (
                        url_mappings.update()
                        .where(url_mappings.c.hash == existing_hash)
                        .values(
                            book_title=book_title,
                            series_name=series_name,
                            volume_number=volume_number,
                        )
                    )
                    conn.execute(upd)
                return existing_hash

            attempt = 0
            while True:
                try:
                    ins = url_mappings.insert().values(
                        hash=url_hash,
                        url=url,
                        book_title=book_title,
                        series_name=series_name,
                        volume_number=volume_number,
                        is_valid=True,
                    )
                    conn.execute(ins)
                    return url_hash
                except IntegrityError:
                    sel2 = sa.select(url_mappings.c.url).where(
                        url_mappings.c.hash == url_hash
                    )
                    r2 = conn.execute(sel2).first()
                    if r2 and r2[0] == url:
                        return url_hash
                    attempt += 1
                    if base_len + attempt <= len(full_hash):
                        url_hash = full_hash[: base_len + attempt]
                        continue
                    url_hash = full_hash
                    ins2 = sa.text(
                        "INSERT INTO url_mappings (hash, url, book_title, series_name, volume_number, is_valid) "
                        "VALUES (:h, :u, :bt, :sn, :vn, 1) ON CONFLICT (hash) DO UPDATE SET is_valid = 1"
                    )
                    conn.execute(
                        ins2,
                        {
                            "h": url_hash,
                            "u": url,
                            "bt": book_title,
                            "sn": series_name,
                            "vn": volume_number,
                        },
                    )
                    return url_hash
    except Exception as e:
        logger.error(f"create_short_url failed: {e}")
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]

def get_url_from_hash(url_hash: str) -> Optional[str]:
    try:
        engine = _get_sa_engine()
        metadata = MetaData()
        url_mappings = Table("url_mappings", metadata, autoload_with=engine)
        with engine.connect() as conn:
            sel = sa.select(url_mappings.c.url).where(url_mappings.c.hash == url_hash)
            r = conn.execute(sel).first()
            return r[0] if r else None
    except Exception as e:
        logger.error(f"Error retrieving URL: {e}")
        return None

def delete_url_mapping(url_hash: str) -> bool:
    try:
        engine = _get_sa_engine()
        metadata = MetaData()
        url_mappings = Table("url_mappings", metadata, autoload_with=engine)
        with engine.begin() as conn:
            stmt = url_mappings.delete().where(url_mappings.c.hash == url_hash)
            result = conn.execute(stmt)
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting URL mapping: {e}")
        return False

def count_mappings() -> int:
    try:
        engine = _get_sa_engine()
        metadata = MetaData()
        url_mappings = Table("url_mappings", metadata, autoload_with=engine)
        with engine.connect() as conn:
            sel = sa.select(sa.func.count()).select_from(url_mappings)
            return int(conn.execute(sel).scalar() or 0)
    except Exception:
        return 0

async def validate_and_update_url(url_hash: str, url: str) -> bool:
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Range": "bytes=0-1024"}
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
                allow_redirects=True,
            ) as resp:
                is_valid = 200 <= resp.status < 300
    except Exception:
        is_valid = False

    try:
        engine = _get_sa_engine()
        metadata = MetaData()
        url_mappings = Table("url_mappings", metadata, autoload_with=engine)
        with engine.begin() as conn:
            if is_valid:
                upd = (
                    url_mappings.update()
                    .where(url_mappings.c.hash == url_hash)
                    .values(
                        last_checked=sa.func.now(),
                        is_valid=True,
                        failed_checks=0,
                    )
                )
            else:
                upd = (
                    url_mappings.update()
                    .where(url_mappings.c.hash == url_hash)
                    .values(
                        last_checked=sa.func.now(),
                        is_valid=False,
                        failed_checks=url_mappings.c.failed_checks + 1,
                    )
                )
            conn.execute(upd)
    except Exception as e:
        logger.error(f"Error updating URL status: {e}")
    
    return is_valid

def get_stats() -> dict:
    try:
        engine = _get_sa_engine()
        metadata = MetaData()
        url_mappings = Table("url_mappings", metadata, autoload_with=engine)
        with engine.connect() as conn:
            total = conn.execute(sa.select(sa.func.count()).select_from(url_mappings)).scalar() or 0
            valid = conn.execute(sa.select(sa.func.count()).select_from(url_mappings).where(url_mappings.c.is_valid == True)).scalar() or 0
            broken = conn.execute(sa.select(sa.func.count()).select_from(url_mappings).where(url_mappings.c.is_valid == False)).scalar() or 0
            at_risk = conn.execute(sa.select(sa.func.count()).select_from(url_mappings).where(url_mappings.c.failed_checks >= 2)).scalar() or 0
            return {
                "total": int(total),
                "valid": int(valid),
                "broken": int(broken),
                "at_risk": int(at_risk),
            }
    except Exception:
        return {"total": 0, "valid": 0, "broken": 0, "at_risk": 0}

def get_broken_links(limit: int = 10):
    try:
        engine = _get_sa_engine()
        metadata = MetaData()
        url_mappings = Table("url_mappings", metadata, autoload_with=engine)
        with engine.connect() as conn:
            sel = (
                sa.select(
                    url_mappings.c.hash,
                    url_mappings.c.book_title,
                    url_mappings.c.failed_checks,
                    url_mappings.c.last_checked,
                    url_mappings.c.created_at,
                )
                .where(url_mappings.c.is_valid == False)
                .order_by(
                    sa.desc(url_mappings.c.failed_checks),
                    sa.desc(url_mappings.c.last_checked),
                )
                .limit(limit)
            )
            return [tuple(r) for r in conn.execute(sel).all()]
    except Exception:
        return []

def get_recent_links(limit: int = 20):
    try:
        engine = _get_sa_engine()
        metadata = MetaData()
        url_mappings = Table("url_mappings", metadata, autoload_with=engine)
        sel = (
            sa.select(
                url_mappings.c.hash,
                url_mappings.c.url,
                url_mappings.c.book_title,
                url_mappings.c.created_at,
            )
            .order_by(sa.desc(url_mappings.c.created_at))
            .limit(limit)
        )
        with engine.connect() as conn:
            return [tuple(r) for r in conn.execute(sel).all()]
    except Exception:
        return []

def get_candidates_for_validation(limit: int = 100, older_than_seconds: int = 3600):
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=older_than_seconds)

    try:
        engine = _get_sa_engine()
        metadata = MetaData()
        url_mappings = Table("url_mappings", metadata, autoload_with=engine)
        with engine.connect() as conn:
            sel = (
                sa.select(url_mappings.c.hash, url_mappings.c.url)
                .where(
                    sa.or_(
                        url_mappings.c.last_checked == None,
                        url_mappings.c.last_checked < cutoff,
                        url_mappings.c.is_valid == False,
                    )
                )
                .limit(limit)
            )
            return [tuple(r) for r in conn.execute(sel).all()]
    except Exception:
        return []

import os
if not os.getenv("PYTEST_CURRENT_TEST"):
    init_db()
