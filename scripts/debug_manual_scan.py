import asyncio
import os
import sys

from sqlalchemy import select

# Asegurar que el path del proyecto esté disponible
sys.path.append(os.getcwd())

from core.db_manager_pg import pg_manager
from models.library_models import LibrarySource
from services.scanner.epub_scanner import EpubScanner
from services.scanner.library_scanner import LibraryScanner
from services.scanner.series_scanner import SeriesScanner


async def manual_scan():
    print("🔬 Iniciando escaneo MANUAL de archivos...")
    epub_dir = r"C:\Users\charl\Downloads\epub"

    async with pg_manager.get_session() as session:
        # Obtener o crear source
        stmt = select(LibrarySource).where(LibrarySource.path == epub_dir)
        source = (await session.execute(stmt)).scalar_one_or_none()
        if not source:
            source = LibrarySource(name="Main", path=epub_dir)
            session.add(source)
            await session.commit()
            print(f"✅ Source creado: {source.id}")

        files = [os.path.join(epub_dir, f) for f in os.listdir(epub_dir) if f.lower().endswith(".epub")]
        print(f"📂 Encontrados {len(files)} archivos EPUB.")

        count = 0
        for full_path in files:
            print(f"📖 Procesando: {os.path.basename(full_path)}")
            try:
                res = await EpubScanner.process_book(
                    full_path,
                    source,
                    session,
                    force_scan=True,
                    series_provider=SeriesScanner.get_or_create_series,
                    translator_provider=LibraryScanner.sync_translator_group,
                )
                print(f"   -> Resultado: {res}")
                await session.commit()
                count += 1
            except Exception as e:
                print(f"   ❌ ERROR en {os.path.basename(full_path)}: {e}")
                await session.rollback()

        print(f"\n✅ Finalizado. {count} archivos procesados con éxito.")


if __name__ == "__main__":
    asyncio.run(manual_scan())
