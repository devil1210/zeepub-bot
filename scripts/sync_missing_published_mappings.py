import asyncio
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text
from core.db_manager_pg import pg_manager
from models.communications import BookPublication
from models.library import Book

async def sync_published_hashes():
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

        inserted_count = 0

        # Mapeos explícitos seguros conocidos
        manual_mappings = {
            "haNZhpelWg": {
                "filepath": "/library/Life Reversal. I Was Cheated On and Falsely Accused, but Now the Most Beautiful Girl in the School is Getting Close to Me - D [NW]/Tras ser engañado y acusado falsamente de un delito - V04 [TP].epub",
                "title": "Life Reversal - Volumen 04",
                "series": "Life Reversal",
                "volume": "4"
            },
            "J9RyHZtpD1": {
                "filepath": "/library/Life Reversal. I Was Cheated On and Falsely Accused, but Now the Most Beautiful Girl in the School is Getting Close to Me - D [NW]/Tras ser engañado y acusado falsamente de un delito - V03 [TP].epub",
                "title": "Life Reversal - Volumen 03",
                "series": "Life Reversal",
                "volume": "3"
            },
            "7jNub8utew": {
                "filepath": "/library/After-School Duty - Gakuto Kouda [NL]/Encargado de después de clases - V03 [TP].epub",
                "title": "Houkago Gakari - Volumen 03",
                "series": "Houkago Gakari",
                "volume": "3"
            }
        }

        for h, data in manual_mappings.items():
            insert_sql = text("""
                INSERT INTO url_mappings (hash, url, book_title, series_name, volume_number, is_valid)
                VALUES (:hash, :url, :title, :series, :volume, true)
                ON CONFLICT (hash) DO UPDATE SET 
                    url = EXCLUDED.url,
                    book_title = EXCLUDED.book_title,
                    is_valid = true;
            """)
            await session.execute(insert_sql, {
                "hash": h,
                "url": data["filepath"],
                "title": data["title"],
                "series": data["series"],
                "volume": data["volume"]
            })
            inserted_count += 1
            print(f"✅ Mapeo insertado/actualizado para hash '{h}' -> {data['title']}")

        # Buscar otros enlaces en book_publications
        for p in pubs:
            if not p.caption:
                continue
            matches = re.findall(r"dl\.zeepubs\.com/([a-zA-Z0-9_-]+)", p.caption)
            for m in matches:
                if m in manual_mappings:
                    continue
                # Si no está en books actual por short_link
                if m not in books_by_short and m not in books_by_id:
                    # Si el book_id de la publicación existe en books
                    target_b = books_by_id.get(p.book_id)
                    if target_b and target_b.filepath:
                        insert_sql = text("""
                            INSERT INTO url_mappings (hash, url, book_title, series_name, volume_number, is_valid)
                            VALUES (:hash, :url, :title, :series, :volume, true)
                            ON CONFLICT (hash) DO UPDATE SET 
                                url = EXCLUDED.url,
                                book_title = EXCLUDED.book_title,
                                is_valid = true;
                        """)
                        await session.execute(insert_sql, {
                            "hash": m,
                            "url": target_b.filepath,
                            "title": target_b.title,
                            "series": target_b.series_spanish or target_b.series_english or "",
                            "volume": str(target_b.volume) if target_b.volume is not None else ""
                        })
                        inserted_count += 1
                        print(f"✅ Auto-mapeado histórico: '{m}' -> {target_b.title} ({target_b.filepath})")

        await session.commit()
        print(f"\n🎉 Total mapeos registrados en url_mappings: {inserted_count}")

if __name__ == "__main__":
    asyncio.run(sync_published_hashes())
