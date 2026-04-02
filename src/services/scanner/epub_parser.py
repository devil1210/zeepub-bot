# src/services/scanner/epub_parser.py
import os
import hashlib
import warnings
import logging
from typing import Optional, Any
from ebooklib import epub
from bs4 import BeautifulSoup

# Silenciar advertencias de EbookLib (comunes con EPUBs de diversas fuentes)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

logger = logging.getLogger(__name__)

class EpubParser:
    """
    Componente especializado en la extracción de metadatos de archivos EPUB.
    Mantiene la lógica bajo las 500 líneas al enfocarse solo en el parsing.
    """
    @staticmethod
    def extract_metadata(file_path: str) -> Optional[dict]:
        """Lee un archivo EPUB y extrae metadatos básicos y Hash."""
        if not os.path.exists(file_path):
            return None

        try:
            book = epub.read_epub(file_path)
            
            # Extracción segura de Dublin Core metadata
            def get_dc(field):
                items = book.get_metadata('DC', field)
                return items[0][0] if items else None

            title = get_dc('title') or os.path.basename(file_path)
            author = get_dc('creator') or "Unknown"
            publisher = get_dc('publisher') or "Unknown"
            
            # Limpieza de descripción (HTML to Text)
            description_raw = get_dc('description') or ""
            description = ""
            if description_raw:
                try:
                    description = BeautifulSoup(description_raw, "html.parser").get_text(separator=" ").strip()
                except Exception:
                    description = str(description_raw)

            # Generar hash del archivo para unicidad (vital para evitar duplicados)
            file_hash = EpubParser.generate_hash(file_path)

            return {
                "title": str(title),
                "author": str(author),
                "publisher": str(publisher),
                "description": description[:1000], # Limitar para DB
                "hash": file_hash,
                "file_path": file_path,
                "file_size": os.path.getsize(file_path)
            }
        except Exception as e:
            logger.error(f"❌ EpubParser: Error procesando {file_path}: {e}")
            return None

    @staticmethod
    def generate_hash(file_path: str) -> str:
        """Genera un SHA256 del contenido del archivo."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Leer en bloques para no saturar memoria con archivos grandes
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"❌ Error generando hash: {e}")
            return "unknown_hash_" + str(os.path.getmtime(file_path))
