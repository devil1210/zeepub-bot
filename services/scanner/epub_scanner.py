import hashlib
import logging
import os
import re
from datetime import datetime
from typing import Any

from models.library_models import DuplicateBook, LocalBook
from services.hash_service import hash_service
from utils.epub_extractor import EpubMetadataExtractor
from utils.library_db import COVERS_DIR

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
            series=book.series,
            author=book.author,
            book_type=book.book_type,
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
            series=book.series or book.title,
            author=book.author,
            book_type=book.book_type,
        )

    @staticmethod
    def copy_metadata_to_existing(source_book: LocalBook, target_book: LocalBook):
        """Copia campos de metadata de un objeto LocalBook a otro existente."""
        target_book.title = source_book.title
        target_book.romaji_title = source_book.romaji_title
        target_book.english_title = source_book.english_title
        target_book.spanish_title = source_book.spanish_title
        target_book.series = source_book.series
        target_book.volume = source_book.volume
        target_book.author = source_book.author
        target_book.author_jap = source_book.author_jap
        target_book.illustrator = source_book.illustrator
        target_book.illustrator_jap = source_book.illustrator_jap
        target_book.translator = source_book.translator
        target_book.layout_by = source_book.layout_by
        target_book.publisher = source_book.publisher
        target_book.description = source_book.description
        target_book.book_type = source_book.book_type
        target_book.tags = source_book.tags
        target_book.demographics = source_book.demographics
        target_book.series_hash = source_book.series_hash
        target_book.is_uncensored = source_book.is_uncensored
        target_book.color_mode = source_book.color_mode
        target_book.series_spanish = source_book.series_spanish
        target_book.series_english = source_book.series_english
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
        series_provider: Any = None,  # Para desacoplar de series_scanner
        translator_provider: Any = None,  # Para desacoplar de library_scanner
    ) -> str | bool:
        """
        Procesa un archivo individual.
        """
        try:
            stat = os.stat(filepath)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            size = stat.st_size

            book = session.query(LocalBook).filter_by(filepath=filepath).first()

            force_metadata = False
            filename = os.path.basename(filepath)

            # Verificar portadas
            missing_covers = False
            if book and book.cover_low:
                from utils.library_db import DB_DIR

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
                and book.cover_low
                and book.series_metadata_id is not None
                and book.series
                and book.author
                and book.volume is not None
                and book.series_hash == hash_service.generate_series_hash(book.series, book.author, book.book_type)
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
                book = LocalBook(filepath=filepath, source_id=source.id)

            # Actualizar campos
            book.filename = filename
            book.file_size = size
            book.file_modified_at = mtime
            book.file_created_at = datetime.fromtimestamp(stat.st_ctime)

            book.title = identity["title"]
            book.author = identity["author"]
            book.series = identity["series"]
            book.volume = identity["volume"]
            book.book_type = identity["book_type"]
            book.language = identity["language"]
            book.translator = identity["translator"]
            book.layout_by = identity["layout_by"]
            book.series_spanish = identity["series_spanish"]
            book.series_english = identity["series_english"]
            book.edition = identity["edition"]

            book.author_jap = meta.get("author_jap")
            book.illustrator_jap = meta.get("illustrator_jap")
            book.description = meta.get("description")
            book.illustrator = meta.get("illustrator")
            book.publisher = meta.get("publisher")

            # Tags
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
            ]
            for tag in raw_tags:
                t_lower = tag.lower().strip()
                if any(d in t_lower for d in known_demographics):
                    classified_demographics.append(tag)
                else:
                    final_genres.append(tag)

            book.demographics = classified_demographics
            book.tags = final_genres

            # Romaji
            romaji = meta.get("romaji_title")
            if not romaji and book.title:
                title_without_vol = re.sub(r"\s*-\s*Volumen\s+\d+.*$", "", book.title, flags=re.IGNORECASE).strip()
                romaji = title_without_vol.split(" - ")[0].strip() if " - " in title_without_vol else title_without_vol
            book.romaji_title = romaji

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

            target_series_hash = cls.generate_series_hash(book)
            target_book_hash = cls.generate_book_hash(book)

            extracted_book_data = book

            with session.no_autoflush:
                existing_same_file = session.query(LocalBook).filter(LocalBook.filepath == filepath).first()

                if existing_same_file:
                    if existing_same_file.book_hash != target_book_hash:
                        hash_conflict = (
                            session.query(LocalBook)
                            .filter(
                                LocalBook.book_hash == target_book_hash,
                                LocalBook.id != existing_same_file.id,
                            )
                            .first()
                        )

                        if hash_conflict:
                            logger.warning(f"📕 Duplicado detectado: {book.title}")
                            try:
                                dup_exists = session.query(DuplicateBook).filter_by(duplicate_filepath=filepath).first()
                                if not dup_exists:
                                    dup = DuplicateBook(
                                        book_hash=target_book_hash,
                                        original_filepath=hash_conflict.filepath,
                                        duplicate_filepath=filepath,
                                        title=book.title,
                                        author=book.author,
                                    )
                                    session.add(dup)
                                    session.commit()
                            except Exception as de:
                                logger.error(f"Error registrando duplicado: {de}")
                                session.rollback()
                            return "duplicate"

                    book = existing_same_file
                    if not book.series_hash or force_scan:
                        book.series_hash = target_series_hash
                    if not book.book_hash or force_scan:
                        book.book_hash = target_book_hash
                    if not book.series or force_scan:
                        book.series = extracted_book_data.series

                    outcome = "updated"
                else:
                    existing_with_same_hash = (
                        session.query(LocalBook).filter(LocalBook.book_hash == target_book_hash).first()
                    )

                    if existing_with_same_hash:
                        if not os.path.exists(existing_with_same_hash.filepath):
                            logger.info(f"🔄 Migración detectada: {existing_with_same_hash.filepath} -> {filepath}")
                            cls.copy_metadata_to_existing(extracted_book_data, existing_with_same_hash)
                            book = existing_with_same_hash
                            book.filepath = filepath
                            book.filename = filename
                            book.file_size = size
                            book.file_modified_at = mtime
                            book.source_id = source.id
                            if not book.series_hash or force_scan:
                                book.series_hash = target_series_hash
                            if not book.book_hash or force_scan:
                                book.book_hash = target_book_hash
                            outcome = "updated"
                        else:
                            logger.warning(f"📕 Duplicado detectado: {book.title}")
                            try:
                                dup_exists = session.query(DuplicateBook).filter_by(duplicate_filepath=filepath).first()
                                if not dup_exists:
                                    dup = DuplicateBook(
                                        book_hash=target_book_hash,
                                        original_filepath=existing_with_same_hash.filepath,
                                        duplicate_filepath=filepath,
                                        title=book.title,
                                        author=book.author,
                                    )
                                    session.add(dup)
                                    session.commit()
                            except Exception as de:
                                logger.error(f"Error registrando duplicado: {de}")
                                session.rollback()
                            return "duplicate"
                    else:
                        book.series_hash = target_series_hash
                        book.book_hash = target_book_hash
                        session.add(book)
                        outcome = "added"

            # 🚀 Asignar short_link determinista basado en el hash del libro
            from utils.helpers import generate_short_link
            new_sl = generate_short_link(book.book_hash)
            if book.short_link != new_sl:
                book.short_link = new_sl

            # Vinculación (Se delega al orquestador o providers)
            if book not in session:
                session.add(book)

            if series_provider:
                series = series_provider(session, book)
                book.series_metadata_id = series.id

            if translator_provider:
                translator_provider(session, book)

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

            return outcome
        except Exception as e:
            logger.error(f"Error procesando libro {filepath}: {e}")
            session.rollback()
            return False
