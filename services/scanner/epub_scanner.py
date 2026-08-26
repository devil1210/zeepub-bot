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
from utils.helpers import (
    generate_short_link,
    is_demographic_tag,
    normalize_demographics_list,
)
from utils.library_db import COVERS_DIR, DB_DIR

logger = logging.getLogger(__name__)


class EpubScanner:
    """
    Lógica especializada en procesar archivos EPUB individuales,
    extraer su metadata y generar su identidad (hashes).
    """

    @staticmethod
    def parse_opf_date(date_str: str) -> datetime | None:
        """
        Parse string date from OPF metadata into datetime object.
        """
        if not date_str or not isinstance(date_str, str):
            return None
        try:
            # Eliminar la 'Z' final si existe y parsear como ISO
            clean_date = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_date)
            # Retornar como naive (UTC implicito por convención de este proyecto)
            return dt.replace(tzinfo=None)
        except Exception:
            try:
                # Fallback para fechas simples YYYY-MM-DD
                return datetime.strptime(date_str[:10], "%Y-%m-%d")
            except Exception:
                return None

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
        uuid: str | None = None,
    ) -> str:
        """
        Genera un hash estable basado en la metadata técnica o UUID del libro.
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
            uuid=uuid,
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
        target_book.published_at = source_book.published_at
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
                        logger.info(
                            f"Metadatos extraídos para ISBN {isbn}: {api_title}"
                        )
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
                    selectinload(LocalBook.demographics),
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

            # Extracción nativa adicional desde el HTML del EPUB
            try:
                from services.epub_service import extract_internal_title
                from utils.metadata_utils import is_romaji_string

                internal_title = extract_internal_title(filepath)
                if internal_title:
                    if is_romaji_string(internal_title):
                        meta["romaji_title"] = internal_title
                        logger.info(
                            f"📖 Título en Romaji extraído del HTML nativo: {internal_title}"
                        )
                    else:
                        meta["series_spanish"] = internal_title
                        logger.info(
                            f"📖 Título en Español extraído del HTML nativo: {internal_title}"
                        )
            except Exception as e:
                logger.debug(f"No se pudo extraer el título interno de {filename}: {e}")

            # 4. PROCESAR IDENTIDAD (Sin redundancia de E/S)
            from utils.helpers import process_book_identity_comprehensive

            identity = process_book_identity_comprehensive(
                meta=meta, original_filename=filename
            )
            if not identity:
                return False

            # Inyectar el UUID en la identidad
            identity["uuid"] = meta.get("uuid")

            # 5. GENERACIÓN DE HASHES SAGRADOS
            # El hash depende de la identidad extraída (normalizada) o del UUID
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
                uuid=identity["uuid"],
            )

            # 6. RESOLUCIÓN DE CONFLICTOS Y ACTUALIZACIÓN
            with session.no_autoflush:
                # Si existía un registro para este filepath pero su hash cambió, lo eliminamos para evitar
                # actualizar la clave primaria (id/book_hash) en caliente, previniendo ForeignKeyViolationError.
                if book and book.book_hash != target_book_hash:
                    logger.info(
                        f"🗑️ Reemplazando libro por cambio de hash sagrado: {book.book_hash} -> {target_book_hash}"
                    )
                    from services.scanner.library_scanner import LibraryScanner

                    await LibraryScanner._cleanup_book_references(
                        session, book.book_hash
                    )
                    await session.delete(book)
                    await session.flush()
                    book = None

                conflict_stmt = (
                    select(LocalBook)
                    .options(
                        selectinload(LocalBook.series_info),
                        selectinload(LocalBook.genres),
                        selectinload(LocalBook.demographics),
                    )
                    .where(
                        LocalBook.book_hash == target_book_hash,
                        LocalBook.filepath != filepath,
                    )
                )
                conflict_res = await session.execute(conflict_stmt)
                hash_conflict = conflict_res.scalar_one_or_none()

                if hash_conflict:
                    if not os.path.exists(hash_conflict.filepath):
                        logger.info(
                            f"🔄 Migración detectada: {hash_conflict.filepath} -> {filepath}"
                        )
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
                        logger.warning(
                            f"📕 Duplicado ignorado (ya existe en DB): {filename}"
                        )
                        # Registrar duplicado si es necesario
                        from models.library import DuplicateBook

                        dup_stmt = select(DuplicateBook).where(
                            DuplicateBook.duplicate_filepath == filepath
                        )
                        dup_res = await session.execute(dup_stmt)
                        dup_exists = dup_res.scalar_one_or_none()
                        if not dup_exists:
                            new_duplicate = DuplicateBook(
                                book_hash=target_book_hash,
                                original_filepath=hash_conflict.filepath,
                                duplicate_filepath=filepath,
                                title=identity.get("title") or hash_conflict.title,
                                author=identity.get("author") or hash_conflict.author,
                            )
                            session.add(new_duplicate)
                            await session.flush()
                        return "duplicate"

                # 6.2 Detección de Colisión de Metadatos Homólogos con UUIDs Distintos
                if not hash_conflict:
                    target_series_hash = cls.generate_series_hash(
                        series_name=identity["series"],
                        author=identity["author"],
                        book_type=identity["book_type"],
                    )
                    dup_meta_stmt = select(LocalBook).where(
                        LocalBook.series_id == target_series_hash,
                        LocalBook.volume == identity["volume"],
                        LocalBook.translator == identity["translator"],
                        LocalBook.layout_by == identity["layout_by"],
                        LocalBook.edition
                        == (identity["edition"] or meta.get("edition")),
                        LocalBook.is_uncensored == bool(identity["is_uncensored"]),
                        LocalBook.color_mode == identity["color_mode"],
                        LocalBook.id != target_book_hash,
                    )
                    dup_meta_res = await session.execute(dup_meta_stmt)
                    logical_conflict = dup_meta_res.scalar_one_or_none()

                    if logical_conflict:
                        logger.warning(
                            f"⚠️ Alerta [POR REVISAR]: Colisión de metadatos homólogos pero UUIDs distintos para {filename}"
                        )
                        from models.library import DuplicateBook

                        dup_stmt = select(DuplicateBook).where(
                            DuplicateBook.duplicate_filepath == filepath
                        )
                        dup_res = await session.execute(dup_stmt)
                        dup_exists = dup_res.scalar_one_or_none()
                        if not dup_exists:
                            new_duplicate = DuplicateBook(
                                book_hash=target_book_hash,
                                original_filepath=logical_conflict.filepath,
                                duplicate_filepath=filepath,
                                title=f"[POR REVISAR] {identity.get('title') or logical_conflict.title}",
                                author=identity.get("author")
                                or logical_conflict.author,
                            )
                            session.add(new_duplicate)
                            await session.flush()

                if not book:
                    # Inicializamos colecciones vacías para evitar lazy-load al asignar después del flush
                    book = LocalBook(
                        id=target_book_hash,
                        filepath=filepath,
                        source=source,
                        genres=[],
                        demographics=[],
                    )
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
                if not getattr(book, "id", None):
                    book.id = target_book_hash
                book.is_uncensored = identity["is_uncensored"]
                book.color_mode = identity["color_mode"]
                from utils.metadata_utils import is_romaji_string

                sp_val = identity.get("series_spanish") or identity.get("spanish_title")
                if sp_val and is_romaji_string(sp_val):
                    if not book.romaji_title or book.romaji_title == identity.get(
                        "title"
                    ):
                        book.romaji_title = sp_val
                    sp_val = None

                book.romaji_title = (
                    identity.get("romaji_title")
                    or meta.get("romaji_title")
                    or book.romaji_title
                )
                book.spanish_title = sp_val or (
                    book.spanish_title
                    if not is_romaji_string(book.spanish_title or "")
                    else None
                )
                book.english_title = (
                    identity.get("series_english") or book.english_title
                )
                book.series_spanish = sp_val or (
                    book.series_spanish
                    if not is_romaji_string(book.series_spanish or "")
                    else None
                )
                book.series_english = (
                    identity.get("series_english") or book.series_english
                )
                book.uuid = identity.get("uuid") or book.uuid

                # Campos adicionales desde OPF Meta
                book.publisher = meta.get("publisher") or book.publisher
                book.description = meta.get("description") or book.description
                book.illustrator = meta.get("illustrator") or book.illustrator
                book.illustrator_jap = (
                    meta.get("illustrator_jap") or book.illustrator_jap
                )
                book.author_jap = meta.get("author_jap") or book.author_jap
                book.isbn = meta.get("isbn") or book.isbn
                book.asin = meta.get("asin") or book.asin
                book.epub_version = meta.get("version") or book.epub_version
                book.word_count = meta.get("word_count") or book.word_count
                book.page_count = meta.get("page_count") or book.page_count
                book.reading_time = meta.get("reading_time") or book.reading_time

                # Parsear fecha de publicación (dc:date original)
                published_date_str = meta.get("published_at") or meta.get("fecha_publicacion")
                if published_date_str:
                    book.published_at = (
                        cls.parse_opf_date(published_date_str) or getattr(book, "published_at", None)
                    )

                # Parsear fecha de modificación de metadatos (evitar DataError con asyncpg si es string)
                opf_date_str = meta.get("modified_at_opf")
                if opf_date_str:
                    book.modified_at_opf = (
                        cls.parse_opf_date(opf_date_str) or book.modified_at_opf
                    )

                # Tags y Clasificación (JSON - Legacy)
                raw_tags = meta.get("tags", [])
                raw_demo = (
                    meta.get("demographics")
                    or meta.get("demografia")
                    or [t for t in raw_tags if is_demographic_tag(t)]
                )
                book_demographics = normalize_demographics_list(raw_demo)
                book_tags = [t for t in raw_tags if not is_demographic_tag(t)]

                book.demographics_json = book_demographics
                book.tags_json = book_tags

                # 7. VINCULACIÓN DE SERIE (Aislado de la identidad básica)
                # Debe ocurrir ANTES de sync_taxonomy porque sync_taxonomy dispara un flush()
                if series_provider:
                    # Cálculo proactivo del hash de serie para evitar IntegrityErrors por IDs nulos
                    book.series_hash = cls.generate_series_hash(
                        series_name=identity["series"],
                        author=identity["author"],
                        book_type=identity["book_type"],
                    )

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

                # Relaciones (NUEVO)
                # Obtenemos los objetos de taxonomía (esto hace E/S asíncrona permitida)
                genres_objs = await ScannerHelpers.sync_taxonomy(
                    session, Genre, book_tags
                )
                demo_objs = await ScannerHelpers.sync_taxonomy(
                    session, Demographic, book_demographics
                )

                # Asignamos las colecciones (ya cargadas o inicializadas, evitando lazy-load)
                book.genres = genres_objs
                book.demographics = demo_objs

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
                    book.cover_original = base_url + os.path.basename(
                        cover_paths["original"]
                    )
                    book.cover_high = base_url + os.path.basename(cover_paths["high"])
                    book.cover_medium = base_url + os.path.basename(
                        cover_paths["medium"]
                    )
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
    async def refresh_book_cover(
        cls, filepath: str, book: LocalBook, session: Any
    ) -> bool:
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
                    book.cover_original = base_url + os.path.basename(
                        cover_paths["original"]
                    )
                    book.cover_high = base_url + os.path.basename(cover_paths["high"])
                    book.cover_medium = base_url + os.path.basename(
                        cover_paths["medium"]
                    )
                    book.cover_low = base_url + os.path.basename(cover_paths["low"])
                    await session.flush()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error refrescando portada para {filepath}: {e}")
            return False
