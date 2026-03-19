import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import select, text

from core.db_manager_pg import pg_manager
from models.base import Base
from models.library_models import LibrarySource, LocalBook
from services.scanner.epub_scanner import EpubScanner
from services.scanner.library_scanner import LibraryScanner
from services.scanner.series_scanner import SeriesScanner

load_dotenv()


async def debug_fix():
    await pg_manager.initialize()

    # FORZAR RECREACIÓN DE TABLAS PARA ASEGURAR ESQUEMA
    print("Paso 1: Recreando esquema...")
    async with pg_manager.engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Peligroso, mejor solo create
        await conn.run_sync(Base.metadata.create_all)

    book_path = r"C:\Users\charl\Downloads\epub\The Angel Next Door Spoils Me Rotten - Saekisan [NL]\El ángel de al lado me convirtió en un inútil - V07 [ONIGRI].epub"
    if not os.path.exists(book_path):
        for root, dirs, files in os.walk(r"C:\Users\charl\Downloads\epub"):
            for f in files:
                if f.lower().endswith(".epub"):
                    book_path = os.path.join(root, f)
                    break
            if book_path:
                break

    print(f"Paso 2: Procesando libro: {book_path}")
    async with pg_manager.get_session() as session:
        source_path = r"C:\Users\charl\Downloads\epub"
        res = await session.execute(select(LibrarySource).where(LibrarySource.path == source_path))
        source = res.scalar_one_or_none()
        if not source:
            source = LibrarySource(name="Debug", path=source_path)
            session.add(source)
            await session.flush()

        try:
            # Limpiar si ya existe para forzar inserción limpia
            await session.execute(text("DELETE FROM books WHERE file_path = :p"), {"p": book_path})

            res_val = await EpubScanner.process_book(
                book_path,
                source,
                session,
                force_scan=True,
                series_provider=SeriesScanner.get_or_create_series,
                translator_provider=LibraryScanner.sync_translator_group,
            )
            print(f"Resultado process_book: {res_val}")
            await session.commit()

            res_check = await session.execute(select(LocalBook).where(LocalBook.file_path == book_path))
            book = res_check.scalar_one_or_none()
            if book:
                print(f"¡ÉXITO! Libro ID: {book.id}, Título: {book.title}")
            else:
                print("ERROR: No se encontró el libro tras commit.")
        except Exception as e:
            with open("debug_error.log", "w", encoding="utf-8") as f:
                f.write(f"ERROR: {type(e).__name__}\n")
                f.write(f"MENSAJE: {str(e)}\n")
                if hasattr(e, "orig"):
                    f.write(f"ORIGINAL: {e.orig}\n")
                import traceback

                f.write(traceback.format_exc())
            print("\n!!! ERROR capturado en debug_error.log !!!\n")
            raise


if __name__ == "__main__":
    asyncio.run(debug_fix())
