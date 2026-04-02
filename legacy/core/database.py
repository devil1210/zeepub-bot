import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Supabase o Local Postgres (preferir variables de entorno)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/zeepub")

# Motor asíncrono de SQLAlchemy 2.0
engine = create_async_engine(DATABASE_URL, echo=False, future=True, pool_size=20, max_overflow=10, pool_pre_ping=True)

# Constructor de sesiones asíncronas
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


async def get_session() -> AsyncSession:
    """Dependency para obtener una sesión de base de datos."""
    async with async_session() as session:
        yield session
