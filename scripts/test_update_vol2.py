import asyncio
import httpx
from core.db_manager_pg import pg_manager
from models.library import Book
from models.communications import PublicationChannel
from services.publisher.publisher_service import publisher_service
from sqlalchemy import select

async def inspect_vol2():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        b = (await s.execute(select(Book).where(Book.id == "077bfed3d8275fd58eb903b0ebae4e8790aa7003fa347a1dbbe5066b5f1efc1a"))).scalar_one_or_none()
        print("LIBRO VOL 2:", b.title if b else None)
        print("FB_POST_ID:", b.fb_post_id if b else None)
        print("FB_PHOTO_ID:", b.fb_photo_id if b else None)
        
        # Ejecutar update_published_book directamente para capturar el error exacto
        res = await publisher_service.update_published_book(
            book_hash="077bfed3d8275fd58eb903b0ebae4e8790aa7003fa347a1dbbe5066b5f1efc1a"
        )
        print("RESULTADO UPDATE DIRECTO:", res)

asyncio.run(inspect_vol2())
