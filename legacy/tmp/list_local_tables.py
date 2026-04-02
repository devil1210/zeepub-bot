import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def list_tables():
    async with pg_manager.get_session() as session:
        result = await session.execute(text("""
            SELECT tablename 
            FROM pg_catalog.pg_tables 
            WHERE schemaname != 'pg_catalog' 
            AND schemaname != 'information_schema';
        """))
        tables = [row[0] for row in result]
        print("Tablas encontradas localmente:")
        for table in sorted(tables):
            print(f"- {table}")

if __name__ == "__main__":
    asyncio.run(list_tables())
