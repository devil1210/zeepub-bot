
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def check_db():
    async with pg_manager.get_session() as session:
        # Check tables
        tables_query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        result = await session.execute(tables_query)
        tables = [row[0] for row in result.fetchall()]
        print(f"Tables in DB: {tables}")
        
        for table in ['publication_channels', 'group_settings', 'active_chats', 'discovered_chats']:
            if table in tables:
                count_query = text(f"SELECT count(*) FROM {table}")
                count_result = await session.execute(count_query)
                count = count_result.scalar()
                print(f"Table '{table}' has {count} rows")
            else:
                print(f"Table '{table}' DOES NOT EXIST")

if __name__ == "__main__":
    asyncio.run(check_db())
