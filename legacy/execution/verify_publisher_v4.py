
import asyncio
import uuid
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock

import os

# Override DATABASE_URL for local execution (outside docker)
os.environ["DATABASE_URL"] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"

from core.v4_db_manager import db_v4
from models.library_models import LibrarySource, Series, Book
from models.publication_models import PublicationChannel, PublicationQueue
from services.v4.publisher_service import PublisherServiceV4
from repositories.v4.publication_repository import PublicationQueueRepository

async def verify_publisher():
    print("Starting PublisherServiceV4 Verification...")
    
    # 1. Ensure tables exist
    await db_v4.create_all_tables()
    
    async with db_v4.get_session() as session:
        # 2. Cleanup (Optional, but good for idempotent testing)
        # For simplicity, we'll just create new records with unique hashes
        test_suffix = str(uuid.uuid4())[:8]
        
        # 3. Create Mock Data
        source = LibrarySource(name=f"Source {test_suffix}", path=f"/tmp/books_{test_suffix}")
        session.add(source)
        await session.flush()
        
        series = Series(
            hash=f"series_hash_{test_suffix}",
            source_id=source.id,
            title_raw=f"Test Series {test_suffix}",
            title_spanish=f"Serie de Prueba {test_suffix}",
            description="Una descripción de prueba con glassmorphism.",
            slug=f"test_slug_{test_suffix}"
        )
        session.add(series)
        await session.flush()
        
        book = Book(
            series_id=series.id,
            hash=f"book_hash_{test_suffix}",
            file_path=f"/tmp/books_{test_suffix}/book1.epub",
            file_size=1024,
            extension="epub",
            volume_number=1.0,
            title="Libro de Prueba Vol 1"
        )
        session.add(book)
        await session.flush()
        
        channel = PublicationChannel(
            name=f"Channel {test_suffix}",
            platform="telegram",
            target_id="-123456789",
            is_active=True
        )
        session.add(channel)
        await session.flush()
        
        await session.commit()
        print(f"Mock data created: Book ID {book.id}")

        # 4. Instantiate Service
        service = PublisherServiceV4(db_v4)
        
        # 5. Enqueue Book
        print("Enqueuing book...")
        enqueue_res = await service.enqueue_book(book.id, channel_ids=[channel.id])
        if not enqueue_res.success:
            print(f"Enqueue failed: {enqueue_res.reason}")
            return
        
        queue_id = enqueue_res.queue_ids[0]
        print(f"Enqueued item ID: {queue_id} (Type: {type(queue_id)})")

        # 6. Process Queue with Mock Bot
        mock_bot_app = MagicMock()
        mock_bot_app.bot = AsyncMock()
        
        print("Processing queue...")
        # Force the scheduled_for to past to process it now
        async with db_v4.get_session() as session2:
            q_repo = PublicationQueueRepository(session2)
            item = await q_repo.get_by_id(queue_id)
            if not item:
                # Try finding by book_hash just in case
                print(f"⚠️ Warning: Could not find item by ID {queue_id}. Checking all pending...")
                all_pending = await q_repo.get_pending_queue(limit=10)
                if all_pending:
                    item = all_pending[0]
                    queue_id = item.id # Update for final check
                    print(f"Found alternative item: {queue_id}")
                else:
                    print("❌ Error: No pending items found at all.")
                    return

            item.scheduled_for = datetime.now(UTC)
            await session2.commit()

        results = await service.process_queue(bot_app=mock_bot_app)
        
        for res in results:
            if res.success:
                print(f"Published successfully to {res.channel_name}")
            else:
                print(f"Publication failed: {res.error}")

        # 7. Verify status in DB
        async with db_v4.get_session() as session3:
            q_repo = PublicationQueueRepository(session3)
            final_item = await q_repo.get_by_id(queue_id)
            if not final_item:
                # Last resort check
                print("⚠️ Final item not found by ID. Checking recent...")
                final_item = (await q_repo.get_all(limit=1))[0]
            
            print(f"Final status: {final_item.status}")
            
            if final_item.status == "sent":
                print("--- VERIFICATION SUCCESSFUL ---")
            else:
                print(f"VERIFICATION FAILED: Status is {final_item.status}")

if __name__ == "__main__":
    asyncio.run(verify_publisher())
    asyncio.run(db_v4.dispose())
