#!/usr/bin/env python3
"""
Script para convertir rutas de portada de URLs API a rutas absolutas.
Ejecutar una sola vez después de actualizar el scanner.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.library_db import COVERS_DIR


async def fix_cover_paths():
    from sqlalchemy import select, update
    from core.db_manager_pg import pg_manager
    from models.library_models import LocalBook

    print(f"COVERS_DIR: {COVERS_DIR}")
    print(f"Absolute path: {os.path.abspath(COVERS_DIR)}")

    async with pg_manager.get_session() as session:
        # Get all books with API URL covers
        stmt = select(LocalBook).where(LocalBook.cover_low.like("/api/library/covers/%"))
        result = await session.execute(stmt)
        books = result.scalars().all()

        print(f"Found {len(books)} books with API URL covers")

        fixed = 0
        for book in books:
            # Extract filename from URL
            if book.cover_low:
                filename = book.cover_low.replace("/api/library/covers/", "")
                abs_path = os.path.join(COVERS_DIR, filename)

                if os.path.exists(abs_path):
                    book.cover_low = abs_path
                    fixed += 1
                    print(f"Fixed cover_low for book {book.id}: {abs_path}")

            if book.cover_medium:
                filename = book.cover_medium.replace("/api/library/covers/", "")
                abs_path = os.path.join(COVERS_DIR, filename)
                if os.path.exists(abs_path):
                    book.cover_medium = abs_path

            if book.cover_high:
                filename = book.cover_high.replace("/api/library/covers/", "")
                abs_path = os.path.join(COVERS_DIR, filename)
                if os.path.exists(abs_path):
                    book.cover_high = abs_path

            if book.cover_original:
                filename = book.cover_original.replace("/api/library/covers/", "")
                abs_path = os.path.join(COVERS_DIR, filename)
                if os.path.exists(abs_path):
                    book.cover_original = abs_path

        await session.commit()
        print(f"Fixed {fixed} books")


if __name__ == "__main__":
    asyncio.run(fix_cover_paths())
