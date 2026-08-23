import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def inspect():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        res = await s.execute(text("""
            SELECT id, book_hash, series_hash, title, series, volume, filepath, uuid 
            FROM books 
            WHERE title ILIKE '%Baka%' OR series ILIKE '%Baka%' OR filepath ILIKE '%Baka%'
            LIMIT 10;
        """))
        for row in res.fetchall():
            print(f"ID: {row[0]}")
            print(f"  book_hash: {row[1]}")
            print(f"  series_hash: {row[2]}")
            print(f"  title: {row[3]}")
            print(f"  series: {row[4]}")
            print(f"  volume: {row[5]}")
            print(f"  filepath: {row[6]}")
            print(f"  uuid: {row[7]}")
    await pg_manager.close()

if __name__ == '__main__':
    asyncio.run(inspect())
