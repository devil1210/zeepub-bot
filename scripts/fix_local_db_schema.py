import asyncio

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()


async def run_migration():
    # URL local forzada
    # Usamos la config de .env pero forzando localhost
    db_url = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"

    print(f"Propuesta de conexión a: {db_url}")

    try:
        engine = create_async_engine(db_url)
        print("Intentando conectar a Localhost...")
        async with engine.begin() as conn:
            print("¡Conectado! Aplicando parche de esquema...")

            # 1. Crear tabla si no existe
            await conn.execute(
                text("""
            CREATE TABLE IF NOT EXISTS publication_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                content TEXT NOT NULL,
                platform VARCHAR(20) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """)
            )

            # 2. Agregar la columna extra_config (JSONB para PostgreSQL)
            try:
                await conn.execute(text("ALTER TABLE publication_templates ADD COLUMN extra_config JSONB;"))
                print("Columna 'extra_config' agregada exitosamente.")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("La columna 'extra_config' ya existe.")
                else:
                    print(f"Aviso durante ALTER: {e}")

            print("Sincronización de esquema local completada.")
    except Exception as e:
        print(f"Error fatal: {e}")


if __name__ == "__main__":
    asyncio.run(run_migration())
