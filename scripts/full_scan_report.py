import asyncio
import os
import sys

from sqlalchemy import func, select

# Asegurar que el path del proyecto esté disponible
sys.path.append(os.getcwd())

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, SeriesMetadata
from services.scanner_service import ScannerService


async def run_full_scan():
    print("🚀 Iniciando escaneo completo de la librería...")

    # 1. Ejecutar el escaneo usando ScannerService (FORZADO con ruta explícita)
    # Pasamos la ruta directamente para evitar fallos de configuración
    lib_path = r"C:\Users\charl\Downloads\epub"
    scanner = ScannerService(libraries={"Main": lib_path})
    results = await scanner.sync_all(force_scan=True)

    if results:
        print("\n📊 Estadísticas del Escaneo:")
        print(f"Librerías/Fuentes procesadas: {results.get('sources_scanned', 0)}")
        print(f"Total escaneado: {results.get('total_scanned', 0)}")
        print(f"Nuevos añadidos: {results.get('added', 0)}")
        print(f"Actualizados: {results.get('updated', 0)}")
        print(f"Removidos: {results.get('removed', 0)}")
        print(f"Archivados (Orphaned): {results.get('archived', 0)}")

    # 2. Obtener resumen de la base de datos
    async with pg_manager.get_session() as session:
        # Contar series
        series_count = await session.scalar(select(func.count(SeriesMetadata.id)))

        # Contar libros (volúmenes)
        books_count = await session.scalar(select(func.count(LocalBook.id)))

        # Obtener lista de tipos de libros
        book_types_stmt = select(SeriesMetadata.book_type, func.count(SeriesMetadata.id)).group_by(
            SeriesMetadata.book_type
        )
        book_types_res = await session.execute(book_types_stmt)
        book_types = book_types_res.all()

        print("\n🏰 Resumen de Información Guardada:")
        print(f"📚 Total de Series: {series_count}")
        print(f"📖 Total de Volúmenes (EPUBs): {books_count}")

        print("\n📂 Distribución por tipo:")
        for b_type, count in book_types:
            print(f"- {b_type or 'Sin especificar'}: {count} series")


if __name__ == "__main__":
    asyncio.run(run_full_scan())
