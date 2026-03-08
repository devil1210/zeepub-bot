import hashlib
import logging
import os
import re
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.library import Demographic, Genre, LocalBook
from services.hash_service import hash_service
from services.scanner.scanner_helpers import ScannerHelpers
from utils.epub_extractor import EpubMetadataExtractor
from utils.helpers import generate_short_link
from utils.library_db import COVERS_DIR, DB_DIR

logger = logging.getLogger(__name__)


class EpubScanner:
    """
    Lógica especializada en procesar archivos EPUB individuales,
    extraer su metadata y generar su identidad (hashes).
    """

    @staticmethod
    def generate_book_hash(
        series_name: str,
        author: str,
        book_type: str,
        volume: float,
        translator: str,
        layout_by: str,
        language: str,
        edition: str,
        is_uncensored: int,
        color_mode: str,
    ) -> str:
        """
        Genera un hash estable basado en la metadata técnica del libro.
        """
        return hash_service.generate_book_hash(
            series=series_name or "Unknown",
            author=author or "Unknown",
            book_type=book_type or "Light Novel",
            volume=volume,
            translator=translator,
            layout_by=layout_by,
            language=language,
            edition=edition,
            is_uncensored=is_uncensored or 0,
            color_mode=color_mode or "bw",
        )

    @staticmethod
    def generate_series_hash(series_name: str, author: str, book_type: str) -> str:
        """
        Genera un hash estable para la serie.
        """
        return hash_service.generate_series_hash(
            series=series_name or "Unknown",
            author=author or "Unknown",
            book_type=book_type or "Light Novel",
        )

    @staticmethod
    def copy_metadata_to_existing(source_book: LocalBook, target_book: LocalBook):
        """Copia campos de metadata de un objeto LocalBook a otro existente."""
        target_book.title = source_book.title
        target_book.romaji_title = source_book.romaji_title
        target_book.is_uncensored = source_book.is_uncensored
        target_book.color_mode = source_book.color_mode
        target_book.edition = source_book.edition
        target_book.isbn = source_book.isbn
        target_book.asin = source_book.asin
        target_book.epub_version = source_book.epub_version
        target_book.modified_at_opf = source_book.modified_at_opf
        target_book.word_count = source_book.word_count
        target_book.page_count = source_book.page_count
        target_book.reading_time = source_book.reading_time
        target_book.file_size = source_book.file_size

    @staticmethod
    async def enrich_from_isbn(book: LocalBook) -> bool:
        """
        Busca metadatos adicionales usando Google Books API.
        """
        import httpx

        try:
            if not book.isbn:
                return False
            isbn = re.sub(r"[^\d]", "", str(book.isbn))
            if not isbn:
                return False

            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&hl=es"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)

            if response.status_code == 429:
                logger.warning("Google Books API rate limited (429).")
                return False

            if response.status_code == 200:
                data = response.json()
                if data.get("totalItems", 0) > 0:
                    item = data["items"][0]["volumeInfo"]
                    api_title = item.get("title")
                    api_lang = item.get("language", "en")

                    found_something = False
                    if api_lang in ("ja", "jp"):
                        if not book.jap_title:
                            book.jap_title = api_title
                            found_something = True
                    else:
                        # We don't save translated titles anymore, only Japanese/Romaji
                        pass

                    if not book.description and item.get("description"):
                        book.description = item.get("description")
                        found_something = True

                    if found_something:
                        logger.info(f"Metadatos extraídos para ISBN {isbn}: {api_title}")
                        return True
        except Exception as e:
            logger.error(f"Error enriqueciendo desde ISBN {book.isbn}: {e}")
        return False

    @classmethod
    async def process_book(
        cls,
        filepath: str,
        source: Any,
        session: Any,
        force_scan: bool = False,
        series_provider: Any = None,
        translator_provider: Any = None,
        force_metadata: bool = False,
        missing_covers: bool = False,
        skip_ai: bool = True,
    ) -> Any:
        """
        Procesa un archivo individual de forma eficiente.
        """
        try:
            filename = os.path.basename(filepath)
            stat = os.stat(filepath)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            size = stat.st_size

            # 1. Búsqueda rápida en DB
            stmt = (
                select(LocalBook)
                .options(
                    selectinload(LocalBook.series_info),
                    selectinload(LocalBook.genres),
                    selectinload(LocalBook.demographics_list),
                )
                .where(LocalBook.filepath == filepath)
            )
            result = await session.execute(stmt)
            book = result.scalar_one_or_none()

            # 2. Evaluación de necesidad de escaneo
            needs_processing = force_scan or not book

            if book:
                if not book.book_hash or not book.short_link:
                    needs_processing = True

                # Verificar portadas
                if not book.cover_low:
                    missing_covers = True
                else:
                    relative_path = book.cover_low.replace("/api/library/covers/", "")
                    local_cover_path = os.path.join(DB_DIR, "covers", relative_path)
                    if not os.path.exists(local_cover_path):
                        missing_covers = True

                if not book.word_count or book.word_count == 0:
                    force_metadata = True

                # Si el archivo cambió físicamente, forzar re-escaneo
                if book.file_modified_at != mtime or book.file_size != size:
                    needs_processing = True

            if not needs_processing and not force_metadata and not missing_covers:
                return "skipped"

            # 3. EXTRACCIÓN ÚNICA
            logger.info(f"{'Re-procesando' if book else 'Procesando'}: {filename}")
            extractor = EpubMetadataExtractor(filepath)
            meta = extractor.extract()
            if not meta:
                logger.error(f"❌ No se pudo extraer metadata de {filename}")
                return False

            # 4. PROCESAR IDENTIDAD (Sin redundancia de E/S)
            from utils.helpers import process_book_identity_comprehensive

            identity = process_book_identity_comprehensive(meta=meta, original_filename=filename)
            if not identity:
                return False

            # 5. GENERACIÓN DE HASHES SAGRADOS
            # El hash depende de la identidad extraída (normalizada)
            target_book_hash = cls.generate_book_hash(
                series_name=identity["series"],
                author=identity["author"],
                book_type=identity["book_type"],
                volume=identity["volume"],
                translator=identity["translator"],
                layout_by=identity["layout_by"],
                language=identity["language"],
                edition=identity["edition"] or meta.get("edition"),
                is_uncensored=identity["is_uncensored"],
                color_mode=identity["color_mode"],
            )

            # 6. RESOLUCIÓN DE CONFLICTOS Y ACTUALIZACIÓN
            with session.no_autoflush:
                conflict_stmt = (
                    select(LocalBook)
                    .options(
                        selectinload(LocalBook.series_info),
                        selectinload(LocalBook.genres),
                        selectinload(LocalBook.demographics_list),
                    )
                    .where(LocalBook.book_hash == target_book_hash, LocalBook.filepath != filepath)
                )
                conflict_res = await session.execute(conflict_stmt)
                hash_conflict = conflict_res.scalar_one_or_none()

                if hash_conflict:
                    if not os.path.exists(hash_conflict.filepath):
                        logger.info(f"🔄 Migración detectada: {hash_conflict.filepath} -> {filepath}")
                        # Si 'book' ya existía pero con otro hash, lo eliminamos a favor del conflictivo que migramos
                        if book and book.book_hash != hash_conflict.book_hash:
                            await session.delete(book)

                        hash_conflict.filepath = filepath
                        hash_conflict.filename = filename
                        hash_conflict.file_size = size
                        hash_conflict.file_modified_at = mtime
                        hash_conflict.source = source
                        book = hash_conflict
                    else:
                        logger.warning(f"📕 Duplicado ignorado (ya existe en DB): {filename}")
                        # Registrar duplicado si es necesario
                        return "duplicate"

                if not book:
                    book = LocalBook(filepath=filepath, source=source)
                    session.add(book)

                # Sincronizar campos principales desde Identity y Meta
                book.filename = filename
                book.file_size = size
                book.file_modified_at = mtime
                book.title = identity["title"]
                book.volume = identity["volume"]
                book.language = identity["language"]
                book.translator = identity["translator"]
                book.layout_by = identity["layout_by"]
                book.edition = identity["edition"] or meta.get("edition")
                book.author = identity["author"]
                book.book_type = identity["book_type"]
                # Deferimos la asignación de series_hash hasta que el series_provider la valide
                book.book_hash = target_book_hash
                book.is_uncensored = identity["is_uncensored"]
                book.color_mode = identity["color_mode"]
                book.romaji_title = identity.get("romaji_title") or book.romaji_title

                # Campos adicionales desde OPF Meta
                book.publisher = meta.get("publisher") or book.publisher
                book.description = meta.get("description") or book.description
                book.illustrator = meta.get("illustrator") or book.illustrator
                book.illustrator_jap = meta.get("illustrator_jap") or book.illustrator_jap
                book.author_jap = meta.get("author_jap") or book.author_jap
                book.isbn = meta.get("isbn") or book.isbn
                book.asin = meta.get("asin") or book.asin
                book.epub_version = meta.get("version") or book.epub_version
                book.word_count = meta.get("word_count") or book.word_count
                book.page_count = meta.get("page_count") or book.page_count
                book.reading_time = meta.get("reading_time") or book.reading_time
                book.modified_at_opf = meta.get("modified_at_opf") or book.modified_at_opf

                # Tags y Clasificación (JSON - Legacy)
                raw_tags = meta.get("tags", [])
                known_demographics = ["shounen", "seinen", "shoujo", "josei", "kodomo", "seijin", "adultos", "mature"]
                book_demographics = [t for t in raw_tags if any(d in t.lower() for d in known_demographics)]
                book_tags = [t for t in raw_tags if t not in book_demographics]

                book.demographics_json = book_demographics
                book.tags_json = book_tags

                # 7. VINCULACIÓN DE SERIE (Aislado de la identidad básica)
                # Debe ocurrir ANTES de sync_taxonomy porque sync_taxonomy dispara un flush()
                if series_provider:
                    # Adjuntamos datos extraídos al objeto temporalmente para el provider
                    book.extracted_data = identity
                    book.extracted_data.update(
                        {
                            "tags": raw_tags,
                            "demographics": book_demographics,
                            "description": book.description,
                            "publisher": book.publisher,
                            "illustrator": book.illustrator,
                            "author_jap": book.author_jap,
                            "illustrator_jap": book.illustrator_jap,
                        }
                    )
                    series = await series_provider(session, book, skip_ai=skip_ai)
                    book.series_hash = series.series_hash

                # Relaciones Normalizadas (NUEVO)
                book.genres = await ScannerHelpers.sync_taxonomy(session, Genre, book_tags)
                book.demographics_list = await ScannerHelpers.sync_taxonomy(session, Demographic, book_demographics)

                # Hash MD5 físico (opcional para integridad extra)
                try:
                    with open(filepath, "rb") as f:
                        book.hash_md5 = hashlib.md5(f.read()).hexdigest()
                except Exception:
                    pass

                if book.book_hash:
                    book.short_link = generate_short_link(book.book_hash)

            if translator_provider:
                await translator_provider(session, book)

            # 8. GESTIÓN DE PORTADAS
            if extractor.cover_data:
                cover_filename = f"{hashlib.md5(filepath.encode()).hexdigest()}.jpg"
                cover_dest = os.path.join(COVERS_DIR, cover_filename)
                cover_paths = extractor.save_cover(cover_dest)
                if cover_paths:
                    base_url = "/api/library/covers/"
                    book.cover_original = base_url + os.path.basename(cover_paths["original"])
                    book.cover_high = base_url + os.path.basename(cover_paths["high"])
                    book.cover_medium = base_url + os.path.basename(cover_paths["medium"])
                    book.cover_low = base_url + os.path.basename(cover_paths["low"])

            await session.flush()
            return "added" if not book.book_hash else "updated"

        except Exception as e:
            logger.error(f"Error procesando libro {filepath}: {e}")
            import traceback

            traceback.print_exc()
            await session.rollback()
            return False

    @classmethod
    async def refresh_book_cover(cls, filepath: str, book: LocalBook, session: Any) -> bool:
        """
        Extrae y guarda únicamente la portada de un libro existente.
        """
        try:
            if not os.path.exists(filepath):
                return False
            extractor = EpubMetadataExtractor(filepath)
            extractor.extract()
            if extractor.cover_data:
                cover_filename = f"{hashlib.md5(filepath.encode()).hexdigest()}.jpg"
                cover_dest = os.path.join(COVERS_DIR, cover_filename)
                cover_paths = extractor.save_cover(cover_dest)
                if cover_paths:
                    base_url = "/api/library/covers/"
                    book.cover_original = base_url + os.path.basename(cover_paths["original"])
                    book.cover_high = base_url + os.path.basename(cover_paths["high"])
                    book.cover_medium = base_url + os.path.basename(cover_paths["medium"])
                    book.cover_low = base_url + os.path.basename(cover_paths["low"])
                    await session.flush()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error refrescando portada para {filepath}: {e}")
            return False
