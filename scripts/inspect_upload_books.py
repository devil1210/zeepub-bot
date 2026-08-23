import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def chk():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        res = await s.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'upload_books'
            ORDER BY ordinal_position;
        """))
        for row in res.fetchall():
            print(f"{row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
    await pg_manager.close()

if __name__ == '__main__':
    asyncio.run(chk())
