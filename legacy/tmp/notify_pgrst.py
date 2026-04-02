import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

async def notify_pgrst():
    supabase_db_url = os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL")
    if supabase_db_url.startswith("postgres://"):
        supabase_db_url = supabase_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif supabase_db_url.startswith("postgresql://") and "+asyncpg" not in supabase_db_url:
        supabase_db_url = supabase_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"Conectando a {supabase_db_url[:20]}...")
    engine = create_async_engine(supabase_db_url)
    async with engine.begin() as conn:
        print("Enviando NOTIFY pgrst, 'reload schema'...")
        await conn.execute(text("NOTIFY pgrst, 'reload schema'"))
        print("NOTIFY enviado.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(notify_pgrst())
