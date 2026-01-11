import os
import re
import json
import hashlib
import logging
from datetime import datetime
from utils.library_db import get_session, init_library_db, COVERS_DIR
from models.library_models import LibrarySource, LocalBook
from utils.epub_extractor import EpubMetadataExtractor
from utils.helpers import parse_metadata_from_title, generate_book_hash, generate_series_hash
from sqlalchemy import select

logger = logging.getLogger(__name__)


class ScannerService:
    """
    Servicio encargado de sincronizar las carpetas físicas con la base de datos.
    """

    def __init__(self, libraries_config_json: str):
        """
        libraries_config_json: JSON string con formato '{"Nombre": "/ruta", ...}'
        """
        try:
            self.libraries = json.loads(libraries_config_json)
        except Exception as e:
            print(f"Error parseando configuración de librerías: {e}")
            self.libraries = {}

        init_library_db()

    def sync_all(self, force_scan=False):
        """
        Sincroniza todas las fuentes configuradas.
        """
        session = get_session()
        try:
            for name, path in self.libraries.items():
                print(f"Iniciando escaneo de fuente: {name} ({path})")

                # 1. Asegurar que la fuente existe en DB
                source = session.query(LibrarySource).filter_by(path=path).first()
                if not source:
                    source = LibrarySource(name=name, path=path)
                    session.add(source)
                    session.commit()

                self._scan_directory(source, session, force_scan)

                source.last_scanned = datetime.utcnow()
                session.commit()

            print("Escaneo completado exitosamente.")
        finally:
            session.close()

    def _scan_directory(self, source, session, force_scan=False):
        """
        Recorre el directorio y procesa archivos nuevos o modificados.
        """
        for root, dirs, files in os.walk(source.path):
            for file in files:
                if file.lower().endswith(".epub"):
                    full_path = os.path.join(root, file)
                    self._process_book(full_path, source, session, force_scan)

    def _process_book(self, filepath, source, session, force_scan=False):
        """
        Procesa un archivo individual.
        """
        try:
            stat = os.stat(filepath)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            size = stat.st_size

            # Buscar si ya existe en DB
            book = session.query(LocalBook).filter_by(filepath=filepath).first()

            # Si ya existe y no ha cambiado el mtime ni el tamaño, saltar (a menos que sea force_scan)
            if (
                not force_scan
                and book
                and book.file_modified_at == mtime
                and book.file_size == size
            ):
                return

            print(f"Procesando: {filepath}")

            # Extraer Metadatos
            extractor = EpubMetadataExtractor(filepath)
            meta = extractor.extract()

            if not meta:
                return

            if not book:
                book = LocalBook(filepath=filepath, source_id=source.id)
                session.add(book)

            # Actualizar campos
            book.filename = os.path.basename(filepath)
            book.file_size = size
            book.file_modified_at = mtime
            book.file_created_at = datetime.fromtimestamp(stat.st_ctime)

            book.title = meta.get("title") or book.filename

            # Extract Romaji Title from main Title
            # Title format: "86 ―Eitishikkusu― - Volumen 01" or "Byōsoku Go Senchimētoru + Hoshi wo Ou Kodomo - Volumen 01"
            # We want only the romaji part before " - Volumen"
            romaji = meta.get("romaji_title")
            if not romaji and book.title:
                # Remove volume part first
                title_without_vol = re.sub(r'\s*-\s*Volumen\s+\d+.*$', '', book.title, flags=re.IGNORECASE).strip()
                # If there's still a " - " separator, take the first part as romaji
                if " - " in title_without_vol:
                    romaji = title_without_vol.split(" - ")[0].strip()
                else:
                    # Otherwise use the whole cleaned title
                    romaji = title_without_vol

            book.romaji_title = romaji
            book.author = meta.get("author")
            book.illustrator = meta.get("illustrator")
            book.translator = meta.get("translator")
            book.layout_by = meta.get("layout_by")

            # Publisher / Translation Group - use full name from OPF
            book.publisher = meta.get("publisher")
            book.description = meta.get("description")
            book.language = meta.get("language") or "es"

            # Smart Tag Categorization
            raw_tags = meta.get("tags", [])
            classified_type = meta.get("book_type")
            classified_demographics = []
            final_genres = []

            type_mapping = {
                "nl": "Novela Ligera",
                "nw": "Novela Web",
                "wn": "Web Novel",
            }
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
                # 1. Book Type?
                if t_lower in type_mapping:
                    if not classified_type:
                        classified_type = type_mapping[t_lower]
                elif "novela" in t_lower:
                    if not classified_type:
                        classified_type = tag
                # 2. Demographic?
                elif any(d in t_lower for d in known_demographics):
                    classified_demographics.append(tag)
                # 3. Otherwise a Genre
                else:
                    final_genres.append(tag)

            book.book_type = classified_type
            book.demographics = classified_demographics
            book.tags = final_genres

            book.series = meta.get("series")
            book.volume = meta.get("volume")

            # series_clean: series already comes cleaned from extractor
            # If series is empty, extract from title as fallback
            if book.series:
                book.series_clean = book.series
            elif book.title:
                # Fallback: extract series name from title
                clean = re.sub(r'\s*-\s*Volumen\s+\d+.*$', '', book.title, flags=re.IGNORECASE).strip()
                clean = re.sub(r'\s*\[.*?\]\s*', ' ', clean).strip()
                clean = re.sub(r'\s+', ' ', clean).strip()
                book.series_clean = clean
            else:
                book.series_clean = None

            # Debug log for series metadata
            logger.debug(
                f"[SCAN] {book.filename} | Series: '{book.series}' | Series Clean: '{book.series_clean}' | Title: '{book.title}'"
            )

            # Enriched identifiers and dates
            book.isbn = meta.get("isbn")
            book.asin = meta.get("asin")
            book.uri_id = meta.get("uri")
            book.published_at = meta.get("published_at")
            book.modified_at_opf = meta.get("modified_at_opf")
            book.book_type = meta.get("book_type")
            book.epub_version = meta.get("version")
            book.word_count = meta.get("word_count")
            book.page_count = meta.get("page_count")
            book.reading_time = meta.get("reading_time")

            # Generar hashes estables
            book.series_hash = self._generate_series_hash(book)
            book.content_hash = self._generate_book_hash(book)

            # Guardar Portada
            if extractor.cover_data:
                cover_filename = f"{hashlib.md5(filepath.encode()).hexdigest()}.jpg"
                cover_dest = os.path.join(COVERS_DIR, cover_filename)
                if extractor.save_cover(cover_dest):
                    book.cover_path = f"/api/library/covers/{cover_filename}"

            session.commit()
        except Exception as e:
            print(f"Error procesando libro {filepath}: {e}")
            session.rollback()

    def _generate_book_hash(self, book: LocalBook) -> str:
        """
        Genera un hash estable basado en los metadatos clave del libro.
        Detecta cambios en título, autor, volumen, tipo y traductor.
        """
        return generate_book_hash(
            title=book.title,
            author=book.author,
            series=book.series_clean,
            volume=book.volume,
            book_type=book.book_type,
            language=book.language,
            translator=book.translator or book.publisher or book.layout_by
        )

    def _generate_series_hash(self, book: LocalBook) -> str:
        """
        Genera un hash estable para agrupar volúmenes de la misma serie.
        """
        # Usar series_clean preferentemente
        series_name = book.series_clean or book.series or book.title
        return generate_series_hash(
            series=series_name,
            author=book.author,
            book_type=book.book_type
        )
