import os
import json
import hashlib
from datetime import datetime
from utils.library_db import get_session, init_library_db, COVERS_DIR
from models.library_models import LibrarySource, LocalBook
from utils.epub_extractor import EpubMetadataExtractor
from sqlalchemy import select

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

    def sync_all(self):
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
                
                self._scan_directory(source, session)
                
                source.last_scanned = datetime.utcnow()
                session.commit()
            
            print("Escaneo completado exitosamente.")
        finally:
            session.close()

    def _scan_directory(self, source, session):
        """
        Recorre el directorio y procesa archivos nuevos o modificados.
        """
        for root, dirs, files in os.walk(source.path):
            for file in files:
                if file.lower().endswith('.epub'):
                    full_path = os.path.join(root, file)
                    self._process_book(full_path, source, session)

    def _process_book(self, filepath, source, session):
        """
        Procesa un archivo individual.
        """
        try:
            stat = os.stat(filepath)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            size = stat.st_size
            
            # Buscar si ya existe en DB
            book = session.query(LocalBook).filter_by(filepath=filepath).first()
            
            # Si ya existe y no ha cambiado el mtime ni el tamaño, saltar
            if book and book.file_modified_at == mtime and book.file_size == size:
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
            
            book.title = meta.get('title') or book.filename
            book.author = meta.get('author')
            book.illustrator = meta.get('illustrator')
            book.translator = meta.get('translator')
            book.layout_by = meta.get('layout_by')
            book.publisher = meta.get('publisher')
            book.description = meta.get('description')
            book.language = meta.get('language') or 'es'
            book.tags = meta.get('tags', [])
            book.series = meta.get('series')
            book.volume = meta.get('volume')
            
            # Enriched identifiers and dates
            book.isbn = meta.get('isbn')
            book.asin = meta.get('asin')
            book.published_at = meta.get('published_at')
            book.modified_at_opf = meta.get('modified_at_opf')
            book.book_type = meta.get('book_type')
            
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
