import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import selectinload

from models.library_models import LibrarySource, LocalBook, SeriesMetadata
from utils.library_db import get_session


class LibraryExportService:
    """
    Servicio para exportar e importar metadatos de la biblioteca en formato JSON.
    """

    @staticmethod
    def export_library(
        source_id: int | None = None,
        series: str | None = None,
        include_stats: bool = True,
    ) -> dict[str, Any]:
        """
        Exporta metadatos de la biblioteca a un diccionario.

        Args:
            source_id: Filtrar por fuente específica
            series: Filtrar por serie específica
            include_stats: Incluir estadísticas en la exportación

        Returns:
            Diccionario con los metadatos exportados
        """
        session = get_session()
        try:
            query = session.query(LocalBook).options(selectinload(LocalBook.series))

            if source_id:
                query = query.filter(LocalBook.source_id == source_id)

            if series:
                query = query.join(LocalBook.series).filter(SeriesMetadata.series_name == series)

            books = query.all()

            # Convertir a diccionarios
            books_data = [book.to_dict() for book in books]

            # Obtener fuentes
            sources_query = session.query(LibrarySource)
            if source_id:
                sources_query = sources_query.filter(LibrarySource.id == source_id)

            sources = sources_query.all()
            sources_data = [
                {
                    "id": s.id,
                    "name": s.name,
                    "path": s.path,
                    "last_scanned": (s.last_scanned.isoformat() if s.last_scanned else None),
                }
                for s in sources
            ]

            export_data = {
                "export_date": datetime.now().isoformat(),
                "version": "1.0",
                "sources": sources_data,
                "books": books_data,
            }

            if include_stats:
                export_data["stats"] = {
                    "total_books": len(books_data),
                    "total_sources": len(sources_data),
                    "unique_series": len({b.get("series") for b in books_data if b.get("series")}),
                    "unique_authors": len({b.get("author") for b in books_data if b.get("author")}),
                }

            return export_data
        finally:
            session.close()

    @staticmethod
    def export_to_json_file(
        filepath: str,
        source_id: int | None = None,
        series: str | None = None,
        pretty: bool = True,
    ) -> str:
        """
        Exporta metadatos a un archivo JSON.

        Args:
            filepath: Ruta del archivo de salida
            source_id: Filtrar por fuente específica
            series: Filtrar por serie específica
            pretty: Formatear JSON con indentación

        Returns:
            Ruta al archivo creado
        """
        data = LibraryExportService.export_library(source_id, series)

        with open(filepath, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                json.dump(data, f, ensure_ascii=False)

        return filepath

    @staticmethod
    def import_from_json(data: dict[str, Any], merge: bool = True) -> dict[str, int]:
        """
        Importa metadatos desde un diccionario JSON.

        Args:
            data: Diccionario con los datos a importar
            merge: Si True, actualiza registros existentes. Si False, solo inserta nuevos.

        Returns:
            Diccionario con estadísticas de la importación
        """
        session = get_session()
        try:
            stats = {
                "sources_added": 0,
                "sources_updated": 0,
                "books_added": 0,
                "books_updated": 0,
                "books_skipped": 0,
            }

            # Importar fuentes
            for source_data in data.get("sources", []):
                existing = session.query(LibrarySource).filter_by(path=source_data["path"]).first()

                if existing:
                    if merge:
                        existing.name = source_data["name"]
                        stats["sources_updated"] += 1
                else:
                    new_source = LibrarySource(name=source_data["name"], path=source_data["path"])
                    session.add(new_source)
                    stats["sources_added"] += 1

            session.commit()

            # Importar libros
            for book_data in data.get("books", []):
                # Buscar por filepath (identificador único)
                existing = session.query(LocalBook).filter_by(filepath=book_data["filepath"]).first()

                if existing:
                    if merge:
                        # Actualizar campos
                        for key, value in book_data.items():
                            if hasattr(existing, key) and key not in ["id", "filepath"]:
                                setattr(existing, key, value)
                        stats["books_updated"] += 1
                    else:
                        stats["books_skipped"] += 1
                else:
                    # Crear nuevo libro (sin el ID para que se auto-genere)
                    book_dict = {k: v for k, v in book_data.items() if k != "id"}
                    new_book = LocalBook(**book_dict)
                    session.add(new_book)
                    stats["books_added"] += 1

            session.commit()
            return stats
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def import_from_json_file(filepath: str, merge: bool = True) -> dict[str, int]:
        """
        Importa metadatos desde un archivo JSON.

        Args:
            filepath: Ruta al archivo JSON
            merge: Si True, actualiza registros existentes

        Returns:
            Diccionario con estadísticas de la importación
        """
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        return LibraryExportService.import_from_json(data, merge)
