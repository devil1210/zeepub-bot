
import asyncio
import os
import logging

# Configurar logging antes de nada
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB_FIX")

# PARCHE CRÍTICO: Sobrescribir la variable de entorno ANTES de importar config
os.environ["DATABASE_URL"] = "postgresql://zeepub:zeepub@localhost:5432/zeepub"
logger.info(f"📍 DATABASE_URL forzada a localhost para ejecución local.")

from core.db_manager_pg import pg_manager
from models.library import LocalBook, SeriesMetadata
from sqlalchemy import select, func
import hashlib

async def run_fix():
    logger.info("🚀 Iniciando Sync de SeriesMetadata...")
    
    async with pg_manager.get_session() as session:
        # 1. Diagnóstico inicial
        res_b = await session.execute(select(func.count(LocalBook.id)))
        total_books = res_b.scalar()
        res_s = await session.execute(select(func.count(SeriesMetadata.id)))
        total_series = res_s.scalar()
        
        logger.info(f"📊 Estado: {total_books} libros / {total_series} series.")
        
        if total_books == 0:
            logger.error("❌ No se encontraron libros en la base de datos. ¿Estás en la DB correcta?")
            return

        # 2. Buscar libros sin vincular
        stmt = select(LocalBook).where(LocalBook.series_metadata_id.is_(None))
        books = (await session.execute(stmt)).scalars().all()
        logger.info(f"📦 Libros sin vincular: {len(books)}")

        from services.scanner_service import ScannerService
        scanner = ScannerService("{}")
        
        touched_hashes = set()
        for i, book in enumerate(books):
            # Regenerar hashes por si acaso
            if not book.series_hash or len(book.series_hash) < 10:
                book.series_hash = scanner._generate_series_hash(book)
            
            # Obtener serie (usamos el método asíncrono manual aquí para evitar líos de sync/async)
            s_stmt = select(SeriesMetadata).where(SeriesMetadata.series_hash == book.series_hash)
            series = (await session.execute(s_stmt)).scalar_one_or_none()
            
            if not series:
                series = SeriesMetadata(
                    series_name=book.series_english or book.title,
                    series_spanish=book.series_spanish,
                    series_hash=book.series_hash,
                    author="Unknown",
                    description="",
                    tags=[],
                    book_count=0,
                )
                session.add(series)
                await session.flush()
            
            book.series_metadata_id = series.id
            touched_hashes.add(book.series_hash)
            
            if i % 100 == 0:
                await session.commit()
                logger.info(f"⏳ Procesando: {i}/{len(books)}")

        await session.commit()
        logger.info(f"✨ Sincronización completada. {len(touched_hashes)} series creadas/vinculadas.")

if __name__ == "__main__":
    asyncio.run(run_fix())
