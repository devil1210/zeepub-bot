import os
import asyncio
import logging
from dotenv import load_dotenv

# Setup basic logging to see everything in terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("ScanTest")

async def test_scan():
    load_dotenv()
    
    from services.scanner_service import ScannerService
    
    libs_json = os.getenv("LOCAL_LIBRARIES")
    logger.info(f"Configured Libraries: {libs_json}")
    
    if not libs_json:
        logger.error("No LOCAL_LIBRARIES found in .env")
        return

    # Initialize scanner
    scanner = ScannerService(libs_json)
    
    logger.info("Starting manual scan...")
    # sync_all is the method that performs the scan
    # We'll run it in a thread since it might be blocking or call it directly if it's async
    # In miniapp_handlers it's called via asyncio.to_thread
    await asyncio.to_thread(scanner.sync_all, force_scan=True)
    logger.info("Scan completed.")

if __name__ == "__main__":
    asyncio.run(test_scan())
