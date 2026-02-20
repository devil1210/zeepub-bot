import asyncio
import logging
import os

# Override for local execution if needed
db_url = os.getenv("DATABASE_URL", "")
if "@db:" in db_url:
    os.environ["DATABASE_URL"] = db_url.replace("@db:", "@localhost:").replace("postgresql://", "postgresql+asyncpg://")
elif not db_url:
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"

from sqlalchemy import text

from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def force_sync_user():
    target_id = 133994080
    new_name = "Charly Silva"
    new_username = "Devil_1210"

    logger.info(f"Forzando actualización de datos para usuario {target_id}...")

    try:
        async with pg_manager.get_session() as session:
            # Actualización con SQL puro para evitar problemas de inicialización de modelos
            sql = text("""
                UPDATE users 
                SET name = :name, nickname = :nickname, username = :username, role = :role, level_id = :level_id
                WHERE telegram_id = :telegram_id
            """)

            result = await session.execute(
                sql,
                {
                    "name": new_name,
                    "nickname": new_name,
                    "username": new_username,
                    "role": "admin",
                    "level_id": 1,
                    "telegram_id": target_id,
                },
            )

            await session.commit()

            if result.rowcount > 0:
                logger.info(f"¡Éxito! Usuario {target_id} actualizado a: {new_name} (@{new_username})")
            else:
                logger.error(f"Usuario {target_id} no encontrado en la base de datos.")

            # Invalidar caché
            try:
                from services.cache_service import cache_manager

                await cache_manager.delete_user(target_id)
                logger.info("Caché invalidada.")
            except Exception as e:
                logger.warning(f"No se pudo invalidar la caché: {e}")
    except Exception as e:
        logger.error(f"Error en la base de datos: {e}")


if __name__ == "__main__":
    asyncio.run(force_sync_user())
