
import asyncio
import os
import sys

# Probar diferentes URLs de conexión
URLS = [
    "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/zeepub",
    os.getenv("DATABASE_URL", "").replace("db:5432", "localhost:5432").replace("postgresql://", "postgresql+asyncpg://")
]

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

async def check_users():
    # Intentar importar el modelo User
    sys.path.append(os.getcwd())
    try:
        from models.users import User
    except ImportError as e:
        print(f"Error importando User: {e}")
        return

    for url in URLS:
        if not url or "asyncpg" not in url: continue
        print(f"Intentando conectar a: {url}")
        try:
            engine = create_async_engine(url, echo=False)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with async_session() as session:
                query = select(User)
                result = await session.execute(query)
                users = result.scalars().all()
                
                print(f"¡Conexión exitosa! Total usuarios: {len(users)}")
                print("-" * 50)
                for user in users:
                    print(f"ID: {user.telegram_id} | Name: {user.name} | Role: {user.role} | Descarga: {user.can_upload}")
                print("-" * 50)
                return # Salir si tiene éxito
        except Exception as e:
            print(f"Fallo con {url}: {e}")

if __name__ == "__main__":
    asyncio.run(check_users())
