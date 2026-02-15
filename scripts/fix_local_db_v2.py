import asyncio

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()


async def run_migration():
    # Intentar varias URLs comunes para desarrollo
    urls = [
        "postgresql+asyncpg://zeepub:zeepub@127.0.0.1:5432/zeepub",
        "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub",
    ]

    success = False
    for db_url in urls:
        print(f"Probando conexión a: {db_url}")
        try:
            # Timeout corto para no esperar demasiado
            engine = create_async_engine(db_url, connect_args={"timeout": 5})
            async with engine.begin() as conn:
                print(f"¡Conectado exitosamente a {db_url}!")

                # Sincronizar columna extra_config
                await conn.execute(
                    text("""
                ALTER TABLE publication_templates ADD COLUMN IF NOT EXISTS extra_config JSONB;
                """)
                )
                print("Columna 'extra_config' verificada/agregada.")
                success = True
                break
        except Exception as e:
            print(f"Fallo conexión a {db_url}: {e}")

    if not success:
        print("\n❌ No se pudo conectar a PostgreSQL localmente.")
        print("Sugerencia: Ejecuta este comando SQL manualmente en tu base de datos:")
        print("ALTER TABLE publication_templates ADD COLUMN extra_config JSONB;")


if __name__ == "__main__":
    asyncio.run(run_migration())
