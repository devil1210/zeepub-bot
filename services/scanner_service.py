import os
import re
import json
import hashlib
import logging
import asyncio
from datetime import datetime
from utils.library_db import get_session, init_library_db, COVERS_DIR
from models.library_models import LibrarySource, LocalBook, DuplicateBook
from utils.epub_extractor import EpubMetadataExtractor
from utils.helpers import generate_book_hash, generate_series_hash, extract_author, parse_metadata_from_title

logger = logging.getLogger(__name__)


class ScannerService:
    """
    Servicio encargado de sincronizar las carpetas físicas con la base de datos.
    """

    _scan_lock = asyncio.Lock()
    _is_scanning = False

    def __init__(self, libraries_config_json: str):
        """
        libraries_config_json: JSON string con formato '{"Nombre": "/ruta", ...}'
        """
        try:
            self.libraries = json.loads(libraries_config_json)
        except Exception as e:
            logger.error(f"Error parseando configuración de librerías: {e}")
            self.libraries = {}

    def sync_all(self, force_scan=False):
        """
        Sincroniza todas las fuentes configuradas.
        """
        if ScannerService._is_scanning:
            logger.warning("Ya hay un escaneo en curso. Saltando.")
            return False

        ScannerService._is_scanning = True
        session = get_session()
        try:
            results = {
                "total_scanned": 0,
                "added": 0,
                "updated": 0,
                "duplicates": 0,
                "failed": 0,
                "covers_created": 0,
                "sources_scanned": len(self.libraries)
            }

            # Si self.libraries está vacío (caso común al iniciar sin config env),
            # cargamos TODAS las fuentes desde la base de datos para escanear todo.
            if not self.libraries:
                all_sources = session.query(LibrarySource).all()
                local_libs_map = {s.name: s.path for s in all_sources}
            else:
                # Si se pasaron librerías específicas, usamos esas
                local_libs_map = self.libraries

            results["sources_scanned"] = len(local_libs_map)

            for name, path in local_libs_map.items():
                logger.info(f"Iniciando escaneo de fuente: {name} ({path})")

                # 1. Asegurar que la fuente existe en DB (si viene del JSON)
                source = session.query(LibrarySource).filter_by(path=path).first()
                if not source:
                    source = LibrarySource(name=name, path=path)
                    session.add(source)
                    session.commit()

                source_results, found_files = self._scan_directory(source, session, force_scan)
                
                # Update global results
                for k, v in source_results.items():
                    results[k] += v

                # --- PRUNING: Delete books in DB not found on disk ---
                try:
                    # Get all DB filepaths for this source
                    db_books = session.query(LocalBook.filepath).filter(LocalBook.source_id == source.id).all()
                    db_paths = {b[0] for b in db_books}
                    
                    missing_paths = db_paths - found_files
                    if missing_paths:
                        logger.info(f"Detectados {len(missing_paths)} libros eliminados físicamente. Limpiando DB...")
                        # Delete in chunks to avoid SQL limits if many
                        missing_list = list(missing_paths)
                        chunk_size = 500
                        for i in range(0, len(missing_list), chunk_size):
                            chunk = missing_list[i:i+chunk_size]
                            session.query(LocalBook).filter(LocalBook.filepath.in_(chunk)).delete(synchronize_session=False)
                        
                        results["removed"] = results.get("removed", 0) + len(missing_paths)
                except Exception as e:
                    logger.error(f"Error durante pruning de {name}: {e}")

                source.last_scanned = datetime.utcnow()
                session.commit()

            logger.info(f"Escaneo completado: {results}")
            return results
        except Exception as e:
            logger.error(f"Error en sync_all: {e}")
            return None
        finally:
            session.close()
            ScannerService._is_scanning = False

    def sync_path(self, path: str, source_id: int = 1, force_scan: bool = True):
        """
        Sincroniza una ruta específica (archivo o directorio).
        Útil para procesar inmediatamente archivos recién subidos.
        """
        if ScannerService._is_scanning:
            logger.warning("Ya hay un escaneo en curso. Saltando sync_path.")
            return False

        ScannerService._is_scanning = True
        session = get_session()
        try:
            results = {
                "total_scanned": 0,
                "added": 0,
                "updated": 0,
                "duplicates": 0,
                "failed": 0,
                "covers_created": 0
            }

            source = session.query(LibrarySource).get(source_id)
            if not source:
                source = session.query(LibrarySource).first()

            if not source:
                logger.error("No se encontró ninguna fuente de librería válida.")
                return None

            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path):
                logger.error(f"La ruta no existe: {abs_path}")
                return None

            if os.path.isfile(abs_path):
                # Es un archivo individual
                if abs_path.lower().endswith(".epub"):
                    results["total_scanned"] = 1
                    res = self._process_book(abs_path, source, session, force_scan)
                    if res == "added": results["added"] = 1
                    elif res == "updated": results["updated"] = 1
                    elif res == "duplicate": results["duplicates"] = 1
                    elif res is False: results["failed"] = 1
            else:
                # Es un directorio
                source_results, _ = self._scan_directory(source, session, force_scan)
                results.update(source_results)

            session.commit()
            logger.info(f"Escaneo de ruta {path} completado: {results}")
            return results
        except Exception as e:
            logger.error(f"Error en sync_path: {e}")
            session.rollback()
            return None
        finally:
            session.close()
            ScannerService._is_scanning = False

    def sync_series(self, series_hash, force_scan=False):
        """
        Sincroniza una serie específica basada en su hash.
        Busca los libros que pertenecen a esa serie y los re-procesa.
        También escanea las carpetas donde se encuentran esos libros por si hay nuevos.
        """
        if ScannerService._is_scanning:
            logger.warning("Ya hay un escaneo en curso. Saltando.")
            return False

        ScannerService._is_scanning = True
        session = get_session()
        try:
            results = {
                "total_scanned": 0,
                "added": 0,
                "updated": 0,
                "duplicates": 0,
                "failed": 0,
                "covers_created": 0
            }

            # 1. Obtener libros existentes de esta serie para saber en qué carpetas buscar
            books = session.query(LocalBook).filter_by(series_hash=series_hash).all()
            if not books:
                logger.warning(f"No se encontraron libros para la serie con hash: {series_hash}")
                return {"success": False, "message": "Serie no encontrada en la base de datos local."}

            # 2. Identificar las carpetas (directorios) a escanear
            # Generalmente una serie está en una única carpeta, pero podría estar dispersa.
            directories_to_scan = set()
            source_map = {} # path -> source_id
            
            for b in books:
                dir_path = os.path.dirname(b.filepath)
                if os.path.exists(dir_path):
                    directories_to_scan.add(dir_path)
                    source_map[dir_path] = b.source_id

            logger.info(f"Sincronizando serie {series_hash}. Directorios a escanear: {len(directories_to_scan)}")

            # 3. Escanear cada directorio encontrado
            for dir_path in directories_to_scan:
                source_id = source_map[dir_path]
                source = session.query(LibrarySource).get(source_id)
                if not source: continue

                # Escaneamos solo el directorio específico (no recursivo hacia arriba, pero os.walk es recursivo hacia abajo)
                # En muchos casos el directorio de la serie es el final, pero si hay subcarpetas las procesará.
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        if file.lower().endswith(".epub"):
                            results["total_scanned"] += 1
                            full_path = os.path.join(root, file)
                            
                            # Procesar el libro
                            book_result = self._process_book(full_path, source, session, force_scan)
                            
                            if book_result == "added":
                                results["added"] += 1
                            elif book_result == "updated":
                                results["updated"] += 1
                            elif book_result == "duplicate":
                                results["duplicates"] += 1
                            elif book_result is False:
                                results["failed"] += 1

                session.commit()

            logger.info(f"Sincronización de serie {series_hash} completada: {results}")
            return results
        except Exception as e:
            logger.error(f"Error en sync_series: {e}")
            session.rollback()
            return None
        finally:
            session.close()
            ScannerService._is_scanning = False

    def _scan_directory(self, source, session, force_scan=False):
        """
        Recorre el directorio y procesa archivos nuevos o modificados.
        """
        results = {
            "total_scanned": 0,
            "added": 0,
            "updated": 0,
            "duplicates": 0,
            "failed": 0,
            "covers_created": 0
        }
        
        found_files = set()
        for root, dirs, files in os.walk(source.path):
            for file in files:
                if file.lower().endswith(".epub"):
                    results["total_scanned"] += 1
                    full_path = os.path.join(root, file)
                    found_files.add(full_path)
                    
                    book_result = self._process_book(full_path, source, session, force_scan)
                    
                    if book_result == "added":
                        results["added"] += 1
                    elif book_result == "updated":
                        results["updated"] += 1
                    elif book_result == "duplicate":
                        results["duplicates"] += 1
                    elif book_result is False:
                        results["failed"] += 1
                    
                    # Batch commit para no bloquear DB mucho tiempo pero asegurar progreso
                    if (results["added"] + results["updated"]) % 50 == 0 and (results["added"] + results["updated"]) > 0:
                        session.commit()
                        logger.info(f"Progreso de escaneo: {results['added'] + results['updated']} libros procesados en {source.name}")
        
        return results, found_files

    def _process_book(self, filepath, source, session, force_scan=False) -> bool:
        """
        Procesa un archivo individual. Devuelve True si el libro fue procesado/actualizado.
        """
        try:
            stat = os.stat(filepath)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            size = stat.st_size

            # Buscar si ya existe en DB
            book = session.query(LocalBook).filter_by(filepath=filepath).first()

            # Si ya existe y no ha cambiado el mtime ni el tamaño, saltar (a menos que sea force_scan)
            # SI el libro existe pero no tiene metadata enriquecida (word_count es 0 o None),
            # forzamos el procesamiento de metadata técnica
            force_metadata = False
            filename = os.path.basename(filepath)
            
            # Verificar si las portadas existen físicamente en el disco
            missing_covers = False
            if book and book.cover_low:
                from utils.library_db import DB_DIR
                # La ruta guardada es /api/library/covers/filename.jpg
                # Debemos convertirla a ruta local data/library/covers/filename.jpg
                relative_path = book.cover_low.replace("/api/library/covers/", "")
                local_cover_path = os.path.join(DB_DIR, "covers", relative_path)
                if not os.path.exists(local_cover_path):
                    missing_covers = True
                    logger.warning(f"Portada no encontrada en disco para {filename}: {local_cover_path}")

            if book and (not book.word_count or book.word_count == 0):
                logger.info(f"Forzando extracción de metadata para {filename} (metadata faltante)")
                force_metadata = True

            if (
                not force_scan
                and not force_metadata
                and not missing_covers
                and book
                and book.file_modified_at == mtime
                and book.file_size == size
                and book.content_hash
                and book.cover_low
            ):
                return False

            action_type = "Re-procesando" if book else "Procesando"
            if missing_covers:
                action_type = "Recuperando portadas de"
            elif force_scan:
                action_type = "Forzando escaneo de"
                
            logger.info(f"{action_type}: {filename}")

            # Primero extraer metadatos para obtener el hash
            extractor = EpubMetadataExtractor(filepath)
            meta = extractor.extract()

            if not meta:
                return

            if not book:
                book = LocalBook(filepath=filepath, source_id=source.id)
                # Don't add yet, will check for duplicates after generating hash

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
            
            # Clean description from HTML
            from utils.helpers import limpiar_html_basico
            book.description_clean = limpiar_html_basico(book.description)
            
            book.language = meta.get("language") or "es"
            book.english_title = meta.get("english_title") # Probablemente vacío de OPF
            book.spanish_title = meta.get("spanish_title")

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

            # Fallback a parseo inteligente del título si falta serie o volumen
            if not book.series or book.volume is None:
                parsed = parse_metadata_from_title(book.title)
                if not book.series and parsed.get("series"):
                    book.series = parsed["series"]
                if book.volume is None and parsed.get("volume"):
                    try:
                        book.volume = float(parsed["volume"])
                    except Exception:
                        pass

            # Enriched identifiers and dates
            book.isbn = meta.get("isbn")
            
            # Enriquecimientos adicionales se hacen manualmente via admin panel 
            # para evitar 429 Too Many Requests y bloqueos de DB innecesarios

            book.asin = meta.get("asin")
            book.uri_id = meta.get("uri")
            book.published_at = meta.get("published_at")
            book.modified_at_opf = meta.get("modified_at_opf")
            # book_type already set above
            book.epub_version = meta.get("version")
            book.word_count = meta.get("word_count")
            book.page_count = meta.get("page_count")
            book.reading_time = meta.get("reading_time")

            # Check for duplicates by filepath BEFORE generating hashes
            existing_same_file = session.query(LocalBook).filter(
                LocalBook.filepath == filepath
            ).first()
            
            outcome = "updated"
            if existing_same_file:
                # Same file, just update metadata on the EXISTING instance
                # Generate hashes for the existing book to check if metadata changed
                temp_book = LocalBook(filepath=filepath, source_id=source.id)
                temp_book.title = meta.get("title") or temp_book.filename
                temp_book.series = meta.get("series")
                temp_book.volume = meta.get("volume")
                temp_book.author = meta.get("author")
                temp_book.book_type = classified_type
                temp_book.translator = meta.get("translator")
                temp_book.layout_by = meta.get("layout_by")
                temp_book.language = meta.get("language") or "es"
                
                new_series_hash = self._generate_series_hash(temp_book)
                new_book_hash = self._generate_book_hash(temp_book)
                
                # Only update if hashes actually changed
                if existing_same_file.book_hash != new_book_hash:
                    self._copy_metadata_to_existing(temp_book, existing_same_file)
                    existing_same_file.series_hash = new_series_hash
                    existing_same_file.book_hash = new_book_hash
                
                book = existing_same_file # Point to the managed instance
                logger.debug(f"Actualizando archivo existente: {filepath}")
            else:
                # New file, generate hashes and check for real duplicates
                book.series_hash = self._generate_series_hash(book)
                book.book_hash = self._generate_book_hash(book)
                
                # Check if there's another file with same content (real duplicate)
                existing_with_same_hash = session.query(LocalBook).filter(
                    LocalBook.book_hash == book.book_hash
                ).first()
                
                if existing_with_same_hash:
                    # This is a REAL duplicate (different file, same content)
                    # We SKIP it to avoid UNIQUE constraint violation on book_hash
                    # But we RECORD it for the user to review
                    logger.warning(f"📕 Duplicado detectado: {book.title}")
                    
                    try:
                        # Check duplicate record existence
                        dup_exists = session.query(DuplicateBook).filter_by(duplicate_filepath=filepath).first()
                        if not dup_exists:
                            dup = DuplicateBook(
                                book_hash=book.book_hash,
                                original_filepath=existing_with_same_hash.filepath,
                                duplicate_filepath=filepath,
                                title=book.title,
                                author=book.author
                            )
                            session.add(dup)
                            session.commit() # Save duplicate immediately to be safe
                    except Exception as de:
                        logger.error(f"Error guardando registro de duplicado: {de}")
                        session.rollback()

                    return "duplicate"
                else:
                    # New unique file, add to session
                    session.add(book)
                    outcome = "added"


            # Guardar Portada en 4 calidades
            if extractor.cover_data:
                cover_filename = f"{hashlib.md5(filepath.encode()).hexdigest()}.jpg"
                cover_dest = os.path.join(COVERS_DIR, cover_filename)
                cover_paths = extractor.save_cover(cover_dest)
                if cover_paths:
                    # Guardar las 4 versiones en la base de datos
                    base_url = "/api/library/covers/"
                    book.cover_original = base_url + os.path.basename(cover_paths['original'])
                    book.cover_high = base_url + os.path.basename(cover_paths['high'])
                    book.cover_medium = base_url + os.path.basename(cover_paths['medium'])
                    book.cover_low = base_url + os.path.basename(cover_paths['low'])

            # session.commit()  # Movido a nivel de batch o fuente
            return outcome
        except Exception as e:
            logger.error(f"Error procesando libro {filepath}: {e}")
            session.rollback()
            return False

    def _generate_book_hash(self, book: LocalBook) -> str:
        """
        Genera un hash estable basado en: series + author + book_type + volume + translator + layout_by.
        """
        # NO usar book.title aquí
        return generate_book_hash(
            series=book.series,
            author=book.author,
            book_type=book.book_type,
            volume=book.volume,
            translator=book.translator,
            layout_by=book.layout_by,
            language=book.language
        )

    def _generate_series_hash(self, book: LocalBook) -> str:
        """
        Genera un hash estable para la serie basado en: series + author + book_type.
        """
        return generate_series_hash(
            series=book.series,
            author=book.author,
            book_type=book.book_type
        )

    def enrich_all_metadata(self, delay_seconds=2.0):
        """
        Busca metadatos online para libros que tienen ISBN pero les falta info,
        procesando uno a uno con esperas para evitar 429.
        """
        if ScannerService._is_scanning:
            logger.warning("No se puede enriquecer metadatos mientras hay un escaneo en curso.")
            return False

        ScannerService._is_scanning = True
        session = get_session()
        try:
            # Buscar libros con ISBN pero sin spanish_title o descripción
            books = session.query(LocalBook).filter(
                LocalBook.isbn != None,
                LocalBook.isbn != '',
                (LocalBook.spanish_title == None) | (LocalBook.description == None)
            ).all()

            logger.info(f"Iniciando enriquecimiento manual para {len(books)} libros.")
            
            for i, book in enumerate(books):
                if self._enrich_from_isbn(book):
                    session.commit()
                    logger.info(f"[{i+1}/{len(books)}] Enriquecido: {book.title}")
                    import time
                    time.sleep(delay_seconds)
                else:
                    # Si falla o no encuentra, no paramos pero notificamos
                    logger.debug(f"[{i+1}/{len(books)}] No se encontró info extra para: {book.title}")

            logger.info("Enriquecimiento masivo completado.")
            return True
        finally:
            session.close()
            ScannerService._is_scanning = False

    def _enrich_from_isbn(self, book):
        """
        Busca metadatos adicionales (títulos en inglés/español) usando Google Books API.
        Retorna True si encontró algo y lo aplicó.
        """
        import httpx
        try:
            if not book.isbn: return False
            isbn = re.sub(r'[^\d]', '', str(book.isbn))
            if not isbn: return False

            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&hl=es"
            response = httpx.get(url, timeout=10.0)
            
            if response.status_code == 429:
                logger.warning(f"Google Books API rate limited (429). Esperando...")
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
                        from utils.helpers import limpiar_html_basico
                        book.description_clean = limpiar_html_basico(book.description)
                        found_something = True
                    
                    if found_something:
                        logger.info(f"Metadatos extraídos para ISBN {isbn}: {api_title}")
                        return True
        except Exception:
            pass

        return False

    def _copy_metadata_to_existing(self, source_book: LocalBook, target_book: LocalBook):
        """Helper to copy updated fields from a fresh scan to an existing DB record."""
        target_book.title = source_book.title
        target_book.romaji_title = source_book.romaji_title
        target_book.english_title = source_book.english_title
        target_book.series = source_book.series
        target_book.volume = source_book.volume
        target_book.author = source_book.author
        target_book.publisher = source_book.publisher
        target_book.description = source_book.description
        target_book.description_clean = source_book.description_clean
        target_book.book_type = source_book.book_type
        target_book.tags = source_book.tags
        target_book.demographics = source_book.demographics
        target_book.series_hash = source_book.series_hash
        # Note: book_hash is handled separately to avoid constraint violations
        target_book.file_size = source_book.file_size


