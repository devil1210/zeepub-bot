import asyncio
from core.db_manager_pg import pg_manager
from sqlalchemy import text

async def main():
    await pg_manager.initialize()
    async with pg_manager.engine.connect() as conn:
        print("--- publication_channels ---")
        res = await conn.execute(text("SELECT id, name, target_id, platform, is_active FROM publication_channels"))
        for r in res.fetchall():
            print(r)
            
        print("\n--- discovered_chats ---")
        res2 = await conn.execute(text("SELECT id, chat_id, title, type FROM discovered_chats LIMIT 10"))
        for r in res2.fetchall():
            print(r)

if __name__ == "__main__":
    asyncio.run(main())
