import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def apply_migration():
    async with pg_manager.get_session() as session:
        print("Aplicando migración: add_last_scanned_to_sources")
        await session.execute(text("ALTER TABLE library_sources ADD COLUMN IF NOT EXISTS last_scanned TIMESTAMPTZ;"))
        await session.commit()
        print("Migración completada exitosamente.")

if __name__ == "__main__":
    asyncio.run(apply_migration())
