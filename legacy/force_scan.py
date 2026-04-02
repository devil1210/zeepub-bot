
import asyncio
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from services.scanner_service import ScannerService
from utils.library_db import Session
from models.library_models import Book

async def force_scan():
    print("--- FORCING MANUAL SCAN ---")
    try:
        # We manually pass the path to be sure
        lib_path = "C:/Users/charl/Downloads/epub"
        scanner = ScannerService(libraries={"Local EPUB": lib_path})
        
        print(f"Scanning path: {lib_path}")
        result = await scanner.sync_all(force_scan=True)
        
        print(f"Scan Result: {result}")
        
        # Verify count
        sess = Session()
        count = sess.query(Book).count()
        print(f"--- TOTAL BOOKS IN DB AFTER SCAN: {count} ---")
        
    except Exception as e:
        import traceback
        print(f"❌ Error during manual scan: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(force_scan())
