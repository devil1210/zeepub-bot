import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.db_manager_pg import pg_manager
from sqlalchemy import text

async def notify_pgrst():
    await pg_manager.initialize()
    if not pg_manager.engine:
        print("Engine is None!")
        return
        
    async with pg_manager.engine.begin() as conn:
        print("Enviando NOTIFY pgrst, 'reload schema'...")
        await conn.execute(text("NOTIFY pgrst, 'reload schema'"))
        print("NOTIFY enviado.")
        
    await pg_manager.close()

if __name__ == "__main__":
    asyncio.run(notify_pgrst())
