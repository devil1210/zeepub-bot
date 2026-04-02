import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def find_bad_tags():
    async with pg_manager.get_session() as session:
        stmt = text("SELECT id, tags::text FROM series_metadata WHERE tags::text ILIKE '%\"Accion\"%'")
        res = await session.execute(stmt)
        rows = res.all()
        print(f"Found {len(rows)} rows with 'Accion'")
        for r_id, tags in rows:
            print(f"ID: {r_id} | Tags: {tags}")

if __name__ == "__main__":
    asyncio.run(find_bad_tags())
