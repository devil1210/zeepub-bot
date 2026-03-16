#!/usr/bin/env python3
"""
scripts/migrate_users_v3_to_v4.py
------------------------------------
Script de migración one-shot: copia los usuarios del schema V3
(tabla `users` de PostgreSQL) al schema V4 (tabla `users_v4`).

Uso:
    python scripts/migrate_users_v3_to_v4.py [--dry-run]

Opciones:
    --dry-run   Muestra los cambios sin escribir nada en la BD.
    --force     Sobreescribe usuarios ya migrados.

La migración es idempotente: si un usuario ya existe en V4
(mismo telegram_id), se omite salvo que se use --force.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("migrate_v3→v4")


async def migrate(dry_run: bool = False, force: bool = False) -> int:
    """
    Ejecuta la migración y devuelve el número de usuarios migrados.
    """
    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from config.config_settings import config

    if not config.DATABASE_URL:
        logger.error("DATABASE_URL no configurada. El script require PostgreSQL.")
        return 0

    # Importar modelos V4
    # Importar Base después de los modelos para que todos estén registrados
    from models.base import Base
    from models.user_models import User, UserLevel

    engine = create_async_engine(config.DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    migrated = 0
    skipped = 0
    errors = 0

    try:
        # 1. Leer usuarios de la tabla V3 (`users`)
        async with engine.begin() as conn:
            result = await conn.execute(
                text("""
                    SELECT
                        u.id AS telegram_id,
                        u.username,
                        u.first_name,
                        u.last_name,
                        ul.name     AS level_name,
                        ul.daily_downloads,
                        u.created_at
                    FROM users u
                    LEFT JOIN user_levels ul ON u.level_id = ul.id
                    ORDER BY u.created_at ASC
                """)
            )
            v3_users = result.mappings().all()

        logger.info(f"📦 Encontrados {len(v3_users)} usuarios en V3")

        # 2. Asegurarse de que el schema V4 existe
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

        # 3. Migrar cada usuario
        async with session_maker() as session:
            # Obtener o crear nivel "free" por defecto
            free_level = await session.execute(select(UserLevel).where(UserLevel.name == "free"))
            free_level = free_level.scalars().first()

            if not free_level:
                free_level = UserLevel(
                    name="free",
                    daily_downloads=3,
                    can_download=True,
                )
                session.add(free_level)
                await session.flush()
                logger.info("♻️  Nivel 'free' creado en V4")

            for row in v3_users:
                telegram_id: int = row["telegram_id"]
                try:
                    # Verificar si ya existe en V4
                    existing = await session.execute(select(User).where(User.telegram_id == telegram_id))
                    existing = existing.scalars().first()

                    if existing and not force:
                        skipped += 1
                        continue

                    # Mapear nivel V3 → V4
                    v3_level_name = (row.get("level_name") or "free").lower()
                    level_map = {
                        "free": free_level,
                        "vip": free_level,
                        "premium": free_level,
                        "admin": free_level,
                    }
                    level = level_map.get(v3_level_name, free_level)

                    if existing and force:
                        existing.username = row.get("username")
                        existing.level_id = level.id
                        logger.debug(f"  🔄 Actualizado t_id={telegram_id}")
                    else:
                        user_v4 = User(
                            id=telegram_id,
                            username=row.get("username"),
                            role="user",
                            level_id=level.id,
                        )
                        session.add(user_v4)
                        logger.debug(f"  ➕ Migrado t_id={telegram_id}")

                    migrated += 1

                except Exception as e:
                    logger.warning(f"  ❌ Error al migrar t_id={telegram_id}: {e}")
                    errors += 1

            if not dry_run:
                await session.commit()
                logger.info("✅ Commit realizado")
            else:
                await session.rollback()
                logger.info("🔍 DRY-RUN: Cambios revertidos (ningún dato fue escrito)")

    finally:
        await engine.dispose()

    logger.info(
        f"\n📊 RESULTADO:\n   Migrados : {migrated}\n   Omitidos : {skipped} (ya existían)\n   Errores  : {errors}"
    )
    return migrated


def main():
    parser = argparse.ArgumentParser(description="Migración de usuarios V3 → V4")
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra los cambios, no escribe")
    parser.add_argument("--force", action="store_true", help="Sobreescribe usuarios ya migrados")
    args = parser.parse_args()

    if args.dry_run:
        logger.info("🔍 MODO DRY-RUN activado")

    count = asyncio.run(migrate(dry_run=args.dry_run, force=args.force))
    sys.exit(0 if count >= 0 else 1)


if __name__ == "__main__":
    main()
