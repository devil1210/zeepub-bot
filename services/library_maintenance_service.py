import os
import sqlite3
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from utils.library_db import get_session, COVERS_DIR, DB_PATH
from models.library_models import LocalBook


class LibraryMaintenanceService:
    """
    Servicio para mantenimiento y optimización de la biblioteca local.
    """

    @staticmethod
    def optimize_database() -> Dict[str, any]:
        """
        Optimiza la base de datos SQLite (VACUUM y ANALYZE).

        Returns:
            Diccionario con resultados de la optimización
        """
        start_time = datetime.now()

        # Obtener tamaño antes
        size_before = os.path.getsize(DB_PATH)

        # Conectar directamente a SQLite para VACUUM
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            # VACUUM: Reconstruye la base de datos para liberar espacio
            cursor.execute("VACUUM")

            # ANALYZE: Actualiza estadísticas para el optimizador de consultas
            cursor.execute("ANALYZE")

            conn.commit()
        finally:
            conn.close()

        # Obtener tamaño después
        size_after = os.path.getsize(DB_PATH)
        duration = (datetime.now() - start_time).total_seconds()

        return {
            "success": True,
            "size_before_bytes": size_before,
            "size_after_bytes": size_after,
            "size_before_mb": round(size_before / (1024 * 1024), 2),
            "size_after_mb": round(size_after / (1024 * 1024), 2),
            "space_saved_bytes": size_before - size_after,
            "space_saved_mb": round((size_before - size_after) / (1024 * 1024), 2),
            "duration_seconds": round(duration, 2),
        }

    @staticmethod
    def cleanup_orphaned_covers() -> Dict[str, any]:
        """
        Elimina archivos de portada huérfanos (sin libro asociado).

        Returns:
            Diccionario con resultados de la limpieza
        """
        session = get_session()
        try:
            # Obtener todas las portadas en uso
            books = session.query(LocalBook).all()
            covers_in_use = set()

            for book in books:
                if book.cover_path:
                    # Extraer nombre del archivo
                    filename = book.cover_path.split("/")[-1]
                    covers_in_use.add(filename)

            # Escanear directorio de portadas
            covers_dir = Path(COVERS_DIR)
            if not covers_dir.exists():
                return {
                    "success": True,
                    "orphaned_files": 0,
                    "space_freed_bytes": 0,
                    "space_freed_mb": 0,
                }

            orphaned_files = []
            total_size = 0

            for cover_file in covers_dir.iterdir():
                if cover_file.is_file() and cover_file.name not in covers_in_use:
                    file_size = cover_file.stat().st_size
                    orphaned_files.append(
                        {"filename": cover_file.name, "size_bytes": file_size}
                    )
                    total_size += file_size

                    # Eliminar archivo huérfano
                    cover_file.unlink()

            return {
                "success": True,
                "orphaned_files": len(orphaned_files),
                "files_deleted": orphaned_files,
                "space_freed_bytes": total_size,
                "space_freed_mb": round(total_size / (1024 * 1024), 2),
            }
        finally:
            session.close()

    @staticmethod
    def get_library_stats() -> Dict[str, any]:
        """
        Genera estadísticas detalladas de la biblioteca.

        Returns:
            Diccionario con estadísticas
        """
        session = get_session()
        try:
            from sqlalchemy import func
            from models.library_models import LibrarySource

            # Estadísticas básicas
            total_books = session.query(LocalBook).count()
            total_sources = session.query(LibrarySource).count()

            # Series y autores únicos
            unique_series = session.query(
                func.count(func.distinct(LocalBook.series))
            ).scalar()
            unique_authors = session.query(
                func.count(func.distinct(LocalBook.author))
            ).scalar()

            # Tipos de libro
            book_types = (
                session.query(LocalBook.book_type, func.count(LocalBook.id))
                .group_by(LocalBook.book_type)
                .all()
            )

            # Tamaño total de archivos
            total_file_size = session.query(func.sum(LocalBook.file_size)).scalar() or 0

            # Portadas
            books_with_covers = (
                session.query(LocalBook)
                .filter(LocalBook.cover_path.isnot(None))
                .count()
            )

            # Tamaño de la base de datos
            db_size = os.path.getsize(DB_PATH)

            # Tamaño del directorio de portadas
            covers_size = (
                sum(
                    f.stat().st_size for f in Path(COVERS_DIR).rglob("*") if f.is_file()
                )
                if Path(COVERS_DIR).exists()
                else 0
            )

            return {
                "total_books": total_books,
                "total_sources": total_sources,
                "unique_series": unique_series,
                "unique_authors": unique_authors,
                "book_types": [{"type": bt[0], "count": bt[1]} for bt in book_types],
                "total_file_size_bytes": total_file_size,
                "total_file_size_gb": round(total_file_size / (1024**3), 2),
                "books_with_covers": books_with_covers,
                "cover_percentage": (
                    round((books_with_covers / total_books * 100), 1)
                    if total_books > 0
                    else 0
                ),
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "covers_dir_size_bytes": covers_size,
                "covers_dir_size_mb": round(covers_size / (1024 * 1024), 2),
            }
        finally:
            session.close()
