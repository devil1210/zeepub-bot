import asyncio
import logging
import os
import sys

from sqlalchemy import select

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.db_manager_pg import pg_manager
from models.library_models import Book, LibrarySource, Series
from services.v4.scanner_service import ScannerServiceV4


async def verify_scanner():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("VerifyScanner")

    # Initialize DB
    await pg_manager.initialize()

    scanner = ScannerServiceV4()

    # Create a test directory
    test_dir = os.path.abspath("test_library_v4")
    os.makedirs(test_dir, exist_ok=True)

    # Create a valid test epub using the utility or inline
    import zipfile

    epub_path = os.path.join(test_dir, "ScannerTest.epub")
    with zipfile.ZipFile(epub_path, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
        )
        z.writestr(
            "content.opf",
            '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" unique-identifier="pub-id" version="3.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Scanner Test Book</dc:title><dc:creator>Test Author</dc:creator><dc:language>es</dc:language><dc:identifier id="pub-id">test-scanner</dc:identifier><meta property="belongs-to-collection" id="coll1">Scanner Test Series</meta></metadata><manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="c1" href="c1.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="c1"/></spine></package>',
        )
        z.writestr(
            "nav.xhtml",
            '<html><body><nav xmlns:epub="http://www.idpf.org/2007/ops" epub:type="toc"><h1>TOC</h1></nav></body></html>',
        )
        z.writestr("c1.xhtml", "<html><body><p>Hello Scanner Test</p></body></html>")

    logger.info(f"Running scan on {test_dir}")

    try:
        await scanner.scan_source_by_path(test_dir, "Test V4 Source")
        logger.info("Scan call finished.")

        # Verify results
        async with pg_manager.get_session() as session:
            # Check Source
            sources = await session.execute(select(LibrarySource))
            logger.info(f"Sources in DB: {len(sources.scalars().all())}")

            # Check Series
            series = await session.execute(select(Series))
            series_list = series.scalars().all()
            logger.info(f"Series in DB: {len(series_list)}")
            for s in series_list:
                logger.info(f" - Series: {s.title_raw} (ID: {s.id})")

            # Check Books
            books = await session.execute(select(Book))
            books_list = books.scalars().all()
            logger.info(f"Books in DB: {len(books_list)}")
            for b in books_list:
                logger.info(f" - Book: {b.title} (Series ID: {b.series_id})")

    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(verify_scanner())
