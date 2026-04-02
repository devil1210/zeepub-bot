# src/services/scanner/library_scanner.py
import os
import logging
import asyncio
from typing import List, Optional
from sqlalchemy import select, func
from src.core.db import db_manager
from src.models.library import LocalBook, SeriesMetadata, MetadataProposal
from src.services.scanner.epub_parser import EpubParser
from src.services.ai.gemini_client import gemini_client
from src.core.config import settings

logger = logging.getLogger(__name__)

class LibraryScanner:
    """
    Orquestador de escaneo masivo de la biblioteca Zeepub.
    Implementa sesiones atómicas para evitar desconexiones de DB durante procesos lentos (IA).
    """
    def __init__(self, root_path: str = None):
        self.root_path = root_path or settings.LIBRARY_PATH
        self.semaphore = asyncio.Semaphore(5) # Limitar concurrencia de parsing/AI

    async def run_full_scan(self):
        """Escaneo completo y recursivo para encontrar e integrar nuevos libros."""
        logger.info(f"🔍 Iniciando escaneo en: {self.root_path}")
        
        if not os.path.exists(self.root_path):
            logger.error(f"❌ Error: La ruta {self.root_path} no existe.")
            return

        # Caminata recursiva para encontrar todos los epubs
        for root, _, files in os.walk(self.root_path):
            epub_files = [f for f in files if f.lower().endswith(".epub")]
            if epub_files:
                tasks = [self.process_file(os.path.join(root, f)) for f in epub_files]
                await asyncio.gather(*tasks)
        
        logger.info("✅ Escaneo de biblioteca completado.")

    async def process_file(self, file_path: str):
        """Procesa un archivo individual con flujo Atómico: DB -> AI -> DB."""
        async with self.semaphore:
            # 1. Parsing técnico básico (Rápido, Offline)
            meta = EpubParser.extract_metadata(file_path)
            if not meta: return

            # 2. SECCIÓN ATÓMICA 1: Verificar existencia
            is_new = False
            async with db_manager.session_scope() as session:
                existing = await session.execute(
                    select(LocalBook).where(LocalBook.hash == meta['hash'])
                )
                if not existing.scalar_one_or_none():
                    is_new = True

            if not is_new:
                # logger.debug(f"⏭️ Libro ya existe: {meta['title']}")
                return

            logger.info(f"🆕 Integrando nuevo libro: {meta['title']}")

            # 3. PROCESO PESADO: IA (FUERA DE LA SESIÓN DE DB)
            # Esto evita que PostgreSQL cierre el socket por inactividad durante la llamada a la IA.
            ai_meta = await gemini_client.normalize_metadata(
                os.path.basename(file_path), meta
            )
            
            # 4. SECCIÓN ATÓMICA 2: Ingesta inteligente y auditoría
            async with db_manager.session_scope() as session:
                await self._persist_to_db(session, meta, ai_meta)

    async def _persist_to_db(self, session, raw_meta, ai_meta):
        """Asocia metadatos crudos y refinados por IA en la DB de forma segura."""
        # Título y Serie decididos por IA o por metadato crudo
        series_title = ai_meta.get("series_name") if (ai_meta and ai_meta.get("series_name")) else raw_meta['title']
        series_hash = hashlib_safe(series_title)

        # Buscar o crear serie
        series_q = await session.execute(select(SeriesMetadata).where(SeriesMetadata.hash == series_hash))
        series = series_q.scalar_one_or_none()
        
        if not series:
            series = SeriesMetadata(
                hash=series_hash,
                title=series_title,
                author=ai_meta.get("author") if ai_meta else raw_meta['author'],
                description=ai_meta.get("description") if ai_meta else raw_meta['description'],
                book_type=ai_meta.get("book_type", "Light Novel") if ai_meta else "Light Novel"
            )
            session.add(series)
            await session.flush() # Obtener ID para el libro

        # Crear Libro vinculado a la serie
        new_book = LocalBook(
            hash=raw_meta['hash'],
            series_id=series.id,
            title=ai_meta.get("suggested_filename") if ai_meta else raw_meta['title'],
            file_path=raw_meta['file_path'],
            file_size=raw_meta['file_size'],
            volume_number=ai_meta.get("volume", 0.0) if ai_meta else 0.0,
            is_uncensored=ai_meta.get("is_uncensored", False) if ai_meta else False,
            color_mode=ai_meta.get("color_mode", "bw") if ai_meta else "bw"
        )
        session.add(new_book)
        
        # Registrar propuesta de metadatos de la IA para auditoría
        if ai_meta:
            proposal = MetadataProposal(
                book_hash=raw_meta['hash'],
                source="gemini-3.1-flash-lite",
                proposed_data=ai_meta,
                confidence=0.9
            )
            session.add(proposal)

def hashlib_safe(text: str) -> str:
    """Genera hash estable del título para la serie."""
    import hashlib
    return hashlib.sha256(text.lower().strip().encode()).hexdigest()

# Singleton exportable
scanner = LibraryScanner()
