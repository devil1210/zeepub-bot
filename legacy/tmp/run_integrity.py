
import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.db_manager_pg import pg_manager
from services.maintenance.integrity_tool import DatabaseIntegrityTool
from config.config_settings import config
import models.library
import models.user_models
import models.publication_models

async def trigger_fix():
    # Setup DB Link (Ensuring 127.0.0.1 for local script)
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/zeepub")
    if "@db:" in db_url: db_url = db_url.replace("@db:", "@127.0.0.1:")
    if "@localhost:" in db_url: db_url = db_url.replace("@localhost:", "@127.0.0.1:")
    
    # Force the URL in config
    config.DATABASE_URL = db_url

    await pg_manager.initialize()
    tool = DatabaseIntegrityTool()
    print(f"Running {tool.name}...")
    result = await tool.run()
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(trigger_fix())
