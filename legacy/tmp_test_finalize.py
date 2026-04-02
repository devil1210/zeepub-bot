
import asyncio
import os
from pathlib import Path
from services.upload_service import upload_service
from core.db_manager_pg import pg_manager

async def test_finalize():
    await pg_manager.initialize()
    try:
        # Create a fake epub
        temp_file = Path("tmp_test_upload.epub")
        with open(temp_file, "wb") as f:
            f.write(b"fake data")
        
        metadata = {
            "title": "Test Book",
            "author": "Test Author",
            "series": "Test Series",
            "volume": 1,
            "book_hash": "test_hash_123",
            "series_hash": "test_series_hash",
            "book_type": "NL",
            "description": "Test desc"
        }
        
        # This will likely fail if /library is not writable or if scan fails
        success = await upload_service.finalize_upload(temp_file, "Test/test.epub", metadata)
        print(f"Finalize success: {success}")
        
        if temp_file.exists():
            temp_file.unlink()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await pg_manager.close()

if __name__ == "__main__":
    asyncio.run(test_finalize())
