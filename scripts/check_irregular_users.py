
import asyncio
from core.db_manager_pg import pg_manager
from sqlalchemy import text

async def check_users():
    async with pg_manager.get_session() as session:
        res = await session.execute(text("SELECT telegram_id, name, nickname, username FROM users WHERE username = 'unknown' OR username IS NULL OR name IS NULL OR nickname IS NULL"))
        rows = res.fetchall()
        print("--- Usuarios con datos incompletos ---")
        for r in rows:
            print(f"ID: {r[0]} | Name: {r[1]} | Nick: {r[2]} | Username: {r[3]}")

if __name__ == "__main__":
    asyncio.run(check_users())
