import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func
from core.db_manager_pg import pg_manager
from models.communications import BookPublication
from models.library import Book

async def inspect_publications():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        # 1. Total publicaciones registradas
        total_res = await session.execute(select(func.count(BookPublication.id)))
        total_pubs = total_res.scalar_one()

        # 2. Libros publicados más de 1 vez
        dup_res = await session.execute(
            select(BookPublication.book_id, func.count(BookPublication.id).label("count"))
            .group_by(BookPublication.book_id)
            .having(func.count(BookPublication.id) > 1)
            .order_by(func.count(BookPublication.id).desc())
            .limit(5)
        )
        multi_published = dup_res.all()

        print(f"📊 Total registros en book_publications: {total_pubs}")
        print(f"\n📚 Libros con múltiples publicaciones (Top 5):")
        for b_id, count in multi_published:
            b_res = await session.execute(select(Book).where(Book.id == b_id))
            b = b_res.scalar_one_or_none()
            title = b.title if b else "Desconocido"
            
            # Obtener fechas de publicación
            pubs_res = await session.execute(
                select(BookPublication).where(BookPublication.book_id == b_id).order_by(BookPublication.published_at.asc())
            )
            pubs = pubs_res.scalars().all()
            print(f"\n📖 {title} (Publicado {count} veces):")
            for p in pubs:
                f_str = p.published_at.strftime('%Y-%m-%d') if p.published_at else 'Sin fecha'
                print(f"   - [{p.platform.upper()}] Fecha: {f_str} -> {p.post_url}")

if __name__ == "__main__":
    asyncio.run(inspect_publications())
