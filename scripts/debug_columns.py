import asyncio

from sqlalchemy import text


async def check():
    from config.config_settings import config

    db_url = config.DATABASE_URL
    if "@db:" in db_url:
        db_url = db_url.replace("@db:", "@localhost:", 1)
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(db_url)

    print(f"Checking database columns for series_metadata at {db_url.split('@')[-1]}...")
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'series_metadata'"
                )
            )
            columns = [row[0] for row in result.fetchall()]
            print(f"Columns in series_metadata: {columns}")

            if "spanish_title" in columns:
                print("✅ Column spanish_title exists!")
            else:
                print("❌ Column spanish_title is MISSING!")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(check())
