import os
import logging
from pathlib import Path
from typing import Dict
from datetime import datetime
from sqlalchemy import text, func

from utils.library_db import get_session, COVERS_DIR, engine
from models.library_models import LocalBook, LibrarySource

logger = logging.getLogger(__name__)

class LibraryMaintenanceService:
    """
    Servicio para mantenimiento y optimización de la biblioteca local (PostgreSQL).
    """

    @staticmethod
    def optimize_database() -> Dict[str, any]:
        """
        Ejecuta mantenimiento básico en PostgreSQL (VACUUM ANALYZE).
        """
        start_time = datetime.now()

        try:
            with engine.connect() as conn:
                # En PostgreSQL no se puede ejecutar VACUUM dentro de una transacción
                # pero SQLAlchemy engine.connect() suele estar en modo autocommit si se configura.
                # Para simplificar, usamos una ejecución directa.
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(text("VACUUM ANALYZE"))
            
            success = True
            error = None
        except Exception as e:
            logger.error(f"Error optimizando base de datos Postgres: {e}")
            success = False
            error = str(e)

        duration = (datetime.now() - start_time).total_seconds()

        return {
            "success": success,
            "error": error,
            "duration_seconds": round(duration, 2),
            "message": "VACUUM ANALYZE completado en PostgreSQL" if success else "Falló el mantenimiento"
        }

    @staticmethod
    def cleanup_orphaned_covers() -> Dict[str, any]:
        """
        Elimina archivos de portada huérfanos (sin libro asociado).
        """
        session = get_session()
        try:
            books = session.query(LocalBook).all()
            covers_in_use = set()

            for book in books:
                for cover_attr in ['cover_low', 'cover_medium', 'cover_high', 'cover_original']:
                    cover_path = getattr(book, cover_attr, None)
                    if cover_path:
                        filename = cover_path.split("/")[-1]
                        covers_in_use.add(filename)

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
        """
        session = get_session()
        try:
            total_books = session.query(LocalBook).count()
            total_sources = session.query(LibrarySource).count()

            unique_series = session.query(
                func.count(func.distinct(LocalBook.series))
            ).scalar()
            unique_authors = session.query(
                func.count(func.distinct(LocalBook.author))
            ).scalar()

            book_types = (
                session.query(LocalBook.book_type, func.count(LocalBook.id))
                .group_by(LocalBook.book_type)
                .all()
            )

            total_file_size = session.query(func.sum(LocalBook.file_size)).scalar() or 0

            books_with_covers = (
                session.query(LocalBook)
                .filter(
                    (LocalBook.cover_low.isnot(None)) |
                    (LocalBook.cover_medium.isnot(None)) |
                    (LocalBook.cover_high.isnot(None)) |
                    (LocalBook.cover_original.isnot(None))
                )
                .count()
            )

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
                "covers_dir_size_bytes": covers_size,
                "covers_dir_size_mb": round(covers_size / (1024 * 1024), 2),
            }
        finally:
            session.close()
