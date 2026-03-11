import hashlib
import logging
import os
import re
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.library_models import DuplicateBook, LocalBook
from services.hash_service import hash_service
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
    def generate_book_hash(book: LocalBook) -> str:
        """
        Genera un hash estable basado en la metadata técnica del libro.
        """
        return hash_service.generate_book_hash(
            series=book.series.series_name if book.series else "Unknown",
            author=book.series.author if book.series else "Unknown",
            book_type=book.series.book_type if book.series else "Light Novel",
            volume=book.volume,
            translator=book.translator,
            layout_by=book.layout_by,
            language=book.language,
            edition=book.edition,
            is_uncensored=book.is_uncensored or 0,
            color_mode=book.color_mode or "bw",
        )

    @staticmethod
    def generate_series_hash(book: LocalBook) -> str:
        """
        Genera un hash estable para la serie.
        """
        return hash_service.generate_series_hash(
            series=(book.series.series_name if book.series else book.title),
            author=(book.series.author if book.series else "Unknown"),
            book_type=(book.series.book_type if book.series else "Light Novel"),
        )

    @staticmethod
    def copy_metadata_to_existing(source_book: LocalBook, target_book: LocalBook):
        """Copia campos de metadata de un objeto LocalBook a otro existente."""
        target_book.title = source_book.title
        target_book.romaji_title = source_book.romaji_title
        target_book.english_title = source_book.english_title
        target_book.spanish_title = source_book.spanish_title
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
                    if api_lang == "es":
                        if not book.spanish_title:
                            book.spanish_title = api_title
                            found_something = True
                    elif api_lang in ("ja", "jp"):
                        if not book.jap_title:
                            book.jap_title = api_title
                            found_something = True
                    else:
                        if not book.english_title:
                            book.english_title = api_title
                            found_something = True

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
    ) -> str | bool:
        """
        Procesa un archivo individual.
        """
        try:
            stat = os.stat(filepath)
            mtime = float(stat.st_mtime)
            size = stat.st_size

            stmt = select(LocalBook).options(selectinload(LocalBook.series)).where(LocalBook.filepath == filepath)
            result = await session.execute(stmt)
            book = result.scalar_one_or_none()

            force_metadata = False
            filename = os.path.basename(filepath)

            # Verificar portadas
            missing_covers = False
            if book and book.cover_low:
                relative_path = book.cover_low.replace("/api/library/covers/", "")
                local_cover_path = os.path.join(DB_DIR, "covers", relative_path)
                if not os.path.exists(local_cover_path):
                    missing_covers = True
                    logger.warning(f"Portada no encontrada para {filename}")

            if book and (not book.word_count or book.word_count == 0):
                force_metadata = True

            if (
                not force_scan
                and not force_metadata
                and not missing_covers
                and book
                and book.file_modified_at == mtime
                and book.file_size == size
                and book.book_hash
                and book.short_link
                and book.cover_low
                and book.series is not None
                and book.series_hash
                == hash_service.generate_series_hash(book.series.series_name, book.series.author, book.series.book_type)
            ):
                return "skipped"

            action_type = "Re-procesando" if book else "Procesando"
            logger.info(f"{action_type}: {filename}")

            extractor = EpubMetadataExtractor(filepath)
            meta = extractor.extract()
            if not meta:
                return False

            from utils.helpers import process_book_identity_comprehensive

            identity = process_book_identity_comprehensive(filepath)
            if not identity:
                return False

            if not book:
                book = LocalBook(filepath=filepath)

            # Actualizar campos
            book.filename = filename
            book.file_size = size
            book.file_modified_at = mtime
            book.file_created_at = datetime.fromtimestamp(stat.st_ctime)

            book.title = identity["title"]
            book.volume = identity["volume"]
            book.language = identity["language"]
            book.translator = identity["translator"]
            book.layout_by = identity["layout_by"]
            book.author = identity["author"]
            book.english_title = identity.get("series")
            book.jap_title = identity.get("romaji_title")
            book.edition = identity["edition"]
            book.book_type = identity.get("book_type", "Novela Ligera")
            book.publisher = meta.get("publisher")

            # Tags clasificación
            raw_tags = meta.get("tags", [])
            classified_demographics = []
            final_genres = []
            known_demographics = [
                "shounen",
                "seinen",
                "shoujo",
                "josei",
                "kodomo",
                "seijin",
                "adultos",
                "mature",
                "maduro",
                "juvenil",
            ]

            for tag in raw_tags:
                t_lower = tag.lower().strip()
                if any(d in t_lower for d in known_demographics):
                    classified_demographics.append(tag)
                else:
                    final_genres.append(tag)

            extracted_data = {
                "series": identity["series"] or book.title,
                "author": identity["author"],
                "author_jap": meta.get("author_jap"),
                "illustrator": meta.get("illustrator"),
                "illustrator_jap": meta.get("illustrator_jap"),
                "description": meta.get("description"),
                "tags": final_genres,
                "demographics": classified_demographics,
                "book_type": identity["book_type"],
            }
            book.extracted_data = extracted_data
            book.romaji_title = identity.get("romaji_title") or meta.get("romaji_title")

            try:
                with open(filepath, "rb") as f:
                    book.hash_md5 = hashlib.md5(f.read()).hexdigest()
            except Exception:
                pass

            book.isbn = meta.get("isbn")
            book.asin = meta.get("asin")
            book.uri_id = meta.get("uri")
            book.published_at = meta.get("published_at")
            book.modified_at_opf = meta.get("modified_at_opf")
            book.epub_version = meta.get("version")
            book.word_count = meta.get("word_count")
            book.page_count = meta.get("page_count")
            book.reading_time = meta.get("reading_time")
            book.is_uncensored = meta.get("is_uncensored", 0)
            book.color_mode = meta.get("color_mode")

            target_series_hash = hash_service.generate_series_hash(
                series=extracted_data["series"],
                author=extracted_data["author"],
                book_type=extracted_data["book_type"],
            )
            target_book_hash = hash_service.generate_book_hash(
                series=identity.get("series"),
                author=identity.get("author"),
                book_type=identity.get("book_type"),
                volume=identity.get("volume"),
                translator=identity.get("translator"),
                layout_by=identity.get("layout_by"),
                language=identity.get("language"),
                edition=identity.get("edition"),
                is_uncensored=meta.get("is_uncensored", 0),
                color_mode=meta.get("color_mode") or "bw",
            )

            with session.no_autoflush:
                # El book ya puede estar en la sesión si existía para ese filepath
                book.series_hash = target_series_hash
                book.book_hash = target_book_hash

                # Buscar conflictos de hash con OTROS paths
                conflict_stmt = (
                    select(LocalBook)
                    .options(selectinload(LocalBook.series))
                    .where(LocalBook.book_hash == target_book_hash, LocalBook.filepath != filepath)
                )
                conflict_res = await session.execute(conflict_stmt)
                hash_conflict = conflict_res.scalar_one_or_none()

                if hash_conflict:
                    if not os.path.exists(hash_conflict.filepath):
                        logger.info(f"🔄 Migración detectada: {hash_conflict.filepath} -> {filepath}")
                        # En lugar de crear uno nuevo, tomamos el conflictivo y actualizamos su path
                        # Pero ya tenemos un objeto 'book', así que es más fácil borrar el conflictivo
                        # o actualizarlo. Hagamos lo segundo: borramos el 'book' (si es nuevo) y usamos el conflictivo.
                        cls.copy_metadata_to_existing(book, hash_conflict)
                        hash_conflict.filepath = filepath
                        hash_conflict.filename = filename
                        hash_conflict.file_size = size
                        hash_conflict.file_modified_at = mtime
                        hash_conflict.series_hash = target_series_hash
                        # Si 'book' es nuevo y no estaba en DB, no pasa nada.
                        # Si estaba en DB (existing_same_file), borrarlo.
                        if book.id and book.id != hash_conflict.id:
                            await session.delete(book)
                        book = hash_conflict
                        outcome = "updated"
                    else:
                        logger.warning(
                            f"📕 [DEDUPLICATION] Duplicate detected for '{book.title}'. Conflict path: {filepath}"
                        )
                        dup_stmt = select(DuplicateBook).where(DuplicateBook.duplicate_filepath == filepath)
                        dup_res = await session.execute(dup_stmt)
                        if not dup_res.scalar_one_or_none():
                            dup = DuplicateBook(
                                book_hash=target_book_hash,
                                original_filepath=hash_conflict.filepath,
                                duplicate_filepath=filepath,
                                title=book.title,
                                author=extracted_data.get("author")
                                or (book.series.author if book.series else "Unknown"),
                            )
                            session.add(dup)
                        return "duplicate"

                if book not in session:
                    session.add(book)
                outcome = "added" if not book.id else "updated"

            # Vinculación
            if series_provider:
                series = await series_provider(session, book, identity=identity)
                book.series_metadata_id = series.id

            if translator_provider:
                await translator_provider(session, book)

            # Portadas
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

            if book.book_hash:
                book.short_link = generate_short_link(book.book_hash)

            await session.flush()
            return outcome
        except Exception as e:
            logger.error(f"Error procesando libro {filepath}: {e}")
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
