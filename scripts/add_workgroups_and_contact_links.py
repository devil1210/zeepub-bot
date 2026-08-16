import asyncio
import logging
from sqlalchemy import text
from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration_workgroups")


async def run_migration():
    """
    Crea las tablas y campos para Grupos Traductores y Enlaces de Contacto
    (ERD WORKGROUP y GROUP_CONTACT_LINK de zeepubs_server).
    """
    queries = [
        # 1. Asegurar tabla translators_groups y sus columnas
        """
        CREATE TABLE IF NOT EXISTS translators_groups (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            siglas VARCHAR(50),
            description TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        );
        """,
        """
        ALTER TABLE translators_groups ADD COLUMN IF NOT EXISTS description TEXT;
        """,
        """
        ALTER TABLE translators_groups ADD COLUMN IF NOT EXISTS siglas VARCHAR(50);
        """,
        # 2. Crear tabla group_contact_links
        """
        CREATE TABLE IF NOT EXISTS group_contact_links (
            id SERIAL PRIMARY KEY,
            group_id INTEGER NOT NULL REFERENCES translators_groups(id) ON DELETE CASCADE,
            platform VARCHAR(50) NOT NULL,
            url VARCHAR(1024) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_group_contact_links_group_id ON group_contact_links(group_id);
        """,
        # 3. Crear tabla asociativa book_workgroups por UUID de libro
        """
        CREATE TABLE IF NOT EXISTS book_workgroups (
            id SERIAL PRIMARY KEY,
            book_id VARCHAR(64) NOT NULL REFERENCES books(id) ON DELETE CASCADE,
            workgroup_id INTEGER NOT NULL REFERENCES translators_groups(id) ON DELETE CASCADE,
            role VARCHAR(50) NOT NULL DEFAULT 'translator',
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_book_workgroups_book_id ON book_workgroups(book_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_book_workgroups_workgroup_id ON book_workgroups(workgroup_id);
        """,
        # 4. Añadir columnas de vinculación directa a books / local_books
        """
        ALTER TABLE books ADD COLUMN IF NOT EXISTS editor VARCHAR(255);
        """,
        """
        ALTER TABLE books ADD COLUMN IF NOT EXISTS translator_group_id INTEGER REFERENCES translators_groups(id) ON DELETE SET NULL;
        """,
        """
        ALTER TABLE books ADD COLUMN IF NOT EXISTS editor_group_id INTEGER REFERENCES translators_groups(id) ON DELETE SET NULL;
        """,
        """
        ALTER TABLE books ADD COLUMN IF NOT EXISTS layout_group_id INTEGER REFERENCES translators_groups(id) ON DELETE SET NULL;
        """,
        """
        ALTER TABLE local_books ADD COLUMN IF NOT EXISTS editor VARCHAR(255);
        """,
        """
        ALTER TABLE local_books ADD COLUMN IF NOT EXISTS translator_group_id INTEGER REFERENCES translators_groups(id) ON DELETE SET NULL;
        """,
        """
        ALTER TABLE local_books ADD COLUMN IF NOT EXISTS editor_group_id INTEGER REFERENCES translators_groups(id) ON DELETE SET NULL;
        """,
        """
        ALTER TABLE local_books ADD COLUMN IF NOT EXISTS layout_group_id INTEGER REFERENCES translators_groups(id) ON DELETE SET NULL;
        """,
    ]

    try:
        await pg_manager.initialize()
        async with pg_manager.get_session() as session:
            for q in queries:
                try:
                    await session.execute(text(q))
                    await session.commit()
                except Exception as e:
                    logger.warning(f"Aviso ejecutando query: {e}")
        logger.info("✅ Migración de Grupos Traductores y Enlaces completada exitosamente.")
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
