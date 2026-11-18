import asyncio
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.communications import BookPublication
from models.library import Book

async def check_publications_short_links():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        # Cargar todos los libros actuales
        res_books = await session.execute(select(Book))
        books = res_books.scalars().all()
        books_by_id = {b.id: b for b in books}
        books_by_short = {b.short_link: b for b in books if b.short_link}

        # Cargar todas las publicaciones
        res_pubs = await session.execute(select(BookPublication))
        pubs = res_pubs.scalars().all()

        print(f"Total libros en DB: {len(books)}")
        print(f"Total publicaciones en DB: {len(pubs)}")

        missing_links = []
        for p in pubs:
            if not p.caption:
                continue
            # Buscar links tipo dl.zeepubs.com/XXXXXXXXXX
            matches = re.findall(r"dl\.zeepubs\.com/([a-zA-Z0-9_-]+)", p.caption)
            for m in matches:
                # Comprobar si existe en books
                if m not in books_by_short and m not in books_by_id:
                    # Encontrar el libro correspondiente por p.book_id o por título en el caption
                    current_book = books_by_id.get(p.book_id)
                    missing_links.append({
                        "pub_id": p.id,
                        "platform": p.platform,
                        "post_id": p.post_id,
                        "published_hash": m,
                        "pub_book_id": p.book_id,
                        "current_book_found": current_book is not None,
                        "current_short_link": current_book.short_link if current_book else None,
                        "filepath": current_book.filepath if current_book else None,
                        "caption_first_line": p.caption.split("\n")[0] if p.caption else ""
                    })

        print(f"\n--- ENLACES PUBLICADOS QUE NO EXISTEN DIRECTAMENTE EN BOOKS: {len(missing_links)} ---")
        for item in missing_links:
            print(f"Hash en Post: {item['published_hash']} | Plataforma: {item['platform']} | Header: {item['caption_first_line']}")
            print(f"   Libro encontrado por ID antiguo: {item['current_book_found']} | Short link actual: {item['current_short_link']}")
            print(f"   Filepath: {item['filepath']}")

if __name__ == "__main__":
    asyncio.run(check_publications_short_links())
