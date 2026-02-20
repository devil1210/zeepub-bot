import asyncio

from sqlalchemy import text

from core.db_manager_pg import pg_manager


async def cleanup_unknowns():
    async with pg_manager.get_session() as session:
        # Update usernames that are literally 'unknown' or 'None'
        res = await session.execute(
            text("UPDATE users SET username = NULL WHERE LOWER(username) IN ('unknown', 'none', '')")
        )
        print(f"Usernames cleaned: {res.rowcount}")

        # Update names that are literally 'unknown' or 'None'
        res_name = await session.execute(
            text("UPDATE users SET name = NULL WHERE LOWER(name) IN ('unknown', 'none', '')")
        )
        print(f"Names cleaned: {res_name.rowcount}")

        # Update nicknames that are literally 'unknown' or 'None'
        res_nick = await session.execute(
            text("UPDATE users SET nickname = NULL WHERE LOWER(nickname) IN ('unknown', 'none', '')")
        )
        print(f"Nicknames cleaned: {res_nick.rowcount}")

        await session.commit()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(cleanup_unknowns())
