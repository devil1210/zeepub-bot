import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import LibrarySource, LocalBook
from services.scanner.epub_scanner import EpubScanner
from services.scanner.library_scanner import LibraryScanner
from services.scanner.series_scanner import SeriesScanner

load_dotenv()


async def debug_single_book():
    await pg_manager.initialize()
    # Una ruta real detectada por ls antes
    book_path = r"C:\Users\charl\Downloads\epub\The Angel Next Door Spoils Me Rotten - Saekisan [NL]\El ángel de al lado me convirtió en un inútil - V07 [ONIGRI].epub"

    if not os.path.exists(book_path):
        # Intentar buscar el primer epub que encuentre
        found = False
        for root, dirs, files in os.walk(r"C:\Users\charl\Downloads\epub"):
            for f in files:
                if f.lower().endswith(".epub"):
                    book_path = os.path.join(root, f)
                    found = True
                    break
            if found:
                break

    print(f"Probando con libro: {book_path}")

    async with pg_manager.get_session() as session:
        # Asegurar fuente
        source_path = r"C:\Users\charl\Downloads\epub"
        res = await session.execute(select(LibrarySource).where(LibrarySource.path == source_path))
        source = res.scalar_one_or_none()
        if not source:
            source = LibrarySource(name="Debug", path=source_path)
            session.add(source)
            await session.flush()

        print("Llamando a EpubScanner.process_book...")
        try:
            res = await EpubScanner.process_book(
                book_path,
                source,
                session,
                force_scan=True,
                series_provider=SeriesScanner.get_or_create_series,
                translator_provider=LibraryScanner.sync_translator_group,
            )
            print(f"Resultado de process_book: {res}")
            await session.commit()

            # Verificar si se insertó
            res_check = await session.execute(select(LocalBook).where(LocalBook.filepath == book_path))
            book = res_check.scalar_one_or_none()
            if book:
                print(f"ÉXITO: Libro insertado con ID {book.id}")
            else:
                print("FALLO: El libro no aparece en la DB tras el commit.")

        except Exception as e:
            print("\n" + "=" * 50)
            print(f"EXCEPCIÓN DETALLADA: {type(e).__name__}: {e}")
            print("=" * 50 + "\n")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_single_book())
