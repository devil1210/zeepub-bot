import asyncio
import logging
import sys
import os

# Añadir el directorio actual al path para importar módulos locales
sys.path.append(os.getcwd())

from models.library import SeriesMetadata, LocalBook, UploadBook, MetadataProposal, TranslatorsGroup
from models.user_models import User
from utils.helpers import generar_slug_from_meta
from config.config_settings import config
from sqlalchemy import select

# Sobrescribir DATABASE_URL para uso local (fuera de Docker)
# El usuario indica que en local se usa el puerto 5432 en localhost
if "@db:5432" in config.DATABASE_URL:
    config.DATABASE_URL = config.DATABASE_URL.replace("@db:5432", "@localhost:5432")
    print(f"DATABASE_URL local: {config.DATABASE_URL}")
elif "db" in config.DATABASE_URL and "localhost" not in config.DATABASE_URL:
    # Caso genérico si solo dice 'db' sin puerto o con otro puerto
    config.DATABASE_URL = config.DATABASE_URL.replace("@db", "@localhost")
    print(f"DATABASE_URL local (fallback): {config.DATABASE_URL}")

from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("slug_updater")

async def update_all_slugs():
    logger.info("Iniciando actualizacion masiva de slugs...")
    
    # Optimized async connection pool settings for local maintenance
    engine_args = {
        "echo": False,
        "pool_pre_ping": True,
        "connect_args": {
            "server_settings": {"jit": "off"},
            "timeout": 60,
            "command_timeout": 300, # 5 minutos para tareas pesadas
        },
    }
    db_url = config.DATABASE_URL
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    engine = create_async_engine(db_url, **engine_args)
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with session_maker() as session:
        logger.info("Conexion establecida. Obteniendo series...")
        stmt = select(SeriesMetadata)
        result = await session.execute(stmt)
        series_list = result.scalars().all()
        
        total = len(series_list)
        updated_count = 0
        
        logger.info(f"Encontradas {total} series para procesar.")
        
        # Opcional: Preparar cliente de Supabase
        supabase_client = None
        if config.ENABLE_SUPABASE:
            try:
                from core.supabase_manager import supabase_manager
                supabase_client = supabase_manager.get_client()
            except Exception as e:
                logger.warning(f"No se pudo conectar con Supabase: {e}")

        for series in series_list:
            old_slug = series.slug
            new_slug = generar_slug_from_meta(series.to_dict())
            
            if new_slug and new_slug != old_slug:
                series.slug = new_slug
                updated_count += 1
                # Log cada 10 para no saturar si son muchas
                if updated_count % 10 == 0 or total < 50:
                    logger.info(f"Actualizando [{series.series_name}]: {old_slug} -> {new_slug}")
                
                if supabase_client:
                    try:
                        supabase_client.table("series_metadata").update(
                            {"slug": new_slug}
                        ).eq("series_hash", series.series_hash).execute()
                    except Exception:
                        pass # Ignorar fallos de red puntuales en cloud
        
        if updated_count > 0:
            await session.commit()
            logger.info(f"Exito: {updated_count} series actualizadas.")
        else:
            logger.info("Todos los slugs ya están actualizados.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(update_all_slugs())
