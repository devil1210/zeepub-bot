import asyncio
import os
from datetime import datetime
from typing import Any

from sqlalchemy import select

from models.library_models import LibrarySource
from services.v4.base_service import BaseService
from services.v4.library_service import LibraryService
from utils.metadata_utils import process_book_identity_comprehensive


class ScannerServiceV4(BaseService):
    """
    Asynchronous Scanner Service for V4.
    Coordinates directory discovery, metadata extraction, and ingestion.
    """

    def __init__(self, db_manager=None, library_service=None):
        super().__init__(db_manager)
        self.library_service = library_service or LibraryService(db_manager)

    async def scan_source_by_path(self, path: str, source_name: str = "Local Library"):
        """
        Main entry point for scanning a physical directory.
        """
        self.logger.info(f"Starting V4 Scan for: {path}")

        # 1. Ensure LibrarySource exists and get ID
        source_id = await self._get_or_create_source(path, source_name)

        # 2. Discover all EPUB files recursively
        epub_files = await asyncio.to_thread(self._discover_epubs, path)
        self.logger.info(f"Discovered {len(epub_files)} EPUB files in {path}")

        if not epub_files:
            self.logger.warning(f"No EPUB files found in {path}")
            return

        # 3. Process files in controlled concurrent batches
        # We use a semaphore to avoid overloading DB or CPU during metadata extraction
        semaphore = asyncio.Semaphore(10)

        tasks = [self._process_file_task(file_path, source_id, semaphore) for file_path in epub_files]
        await asyncio.gather(*tasks)

        # 4. Update last_scanned
        await self._update_last_scanned(source_id)
        self.logger.info(f"V4 Scan completed for {path}")

    def _discover_epubs(self, root_path: str) -> list[str]:
        """Blocking I/O: Recursively finds all .epub files."""
        epubs = []
        for root, _, files in os.walk(root_path):
            for file in files:
                if file.lower().endswith(".epub"):
                    epubs.append(os.path.join(root, file))
        return epubs

    async def _process_file_task(self, file_path: str, source_id: Any, semaphore: asyncio.Semaphore):
        """Worker task to handle metadata extraction and ingestion for a single file."""
        async with semaphore:
            try:
                # Meta Extraction (likely blocking I/O)
                metadata = await asyncio.to_thread(process_book_identity_comprehensive, file_path)

                if metadata is None:
                    self.logger.error(f"Failed to extract metadata for {file_path}")
                    return

                # Ensure critical fields are present for V4 ingest_book
                metadata["source_id"] = source_id
                metadata["file_path"] = file_path
                metadata["file_size"] = os.path.getsize(file_path)
                metadata["extension"] = os.path.splitext(file_path)[1].replace(".", "").lower()

                # Ingest via LibraryService (uses V4 repos and models)
                await self.library_service.ingest_book(metadata)
                self.logger.debug(f"Successfully processed: {file_path}")

            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {str(e)}")

    async def _get_or_create_source(self, path: str, name: str) -> Any:
        """Retrieves or creates the LibrarySource record."""
        async with self.db.get_session() as session:
            stmt = select(LibrarySource).where(LibrarySource.path == path)
            result = await session.execute(stmt)
            source = result.scalar_one_or_none()

            if not source:
                source = LibrarySource(name=name, path=path)
                session.add(source)
                await session.flush()
                source_id = source.id
                self.logger.info(f"Created new LibrarySource: '{name}' (ID: {source_id})")
            else:
                source_id = source.id
                # Update name if it changed? Optional, let's keep it simple.

            return source_id

    async def _update_last_scanned(self, source_id: Any):
        """Updates the last_scanned timestamp for the source."""
        async with self.db.get_session() as session:
            stmt = select(LibrarySource).where(LibrarySource.id == source_id)
            result = await session.execute(stmt)
            source = result.scalar_one_or_none()
            if source:
                source.last_scanned = datetime.now()
