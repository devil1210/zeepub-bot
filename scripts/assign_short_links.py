import asyncio
import os
import sys
import hashlib
import string

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.library_models import LocalBook

def hash_to_short_link(book_hash: str) -> str:
    """Convierte el hash de un libro en un short_link estable de 10 caracteres."""
    if not book_hash:
        return ""
    
    # Usamos los primeros 10 caracteres de un hash MD5 del hash original
    # (MD5 es suficiente para colisiones en 10 caracteres y da un set alfanumérico limpio)
    # Alphabet: a-z, A-Z, 0-9 para Base62-like stability
    alphabet = string.ascii_letters + string.digits
    
    # Derivamos un valor numérico del hash
    hash_int = int(hashlib.md5(book_hash.encode()).hexdigest(), 16)
    
    res = []
    temp_hash = hash_int
    for _ in range(10):
        res.append(alphabet[temp_hash % len(alphabet)])
        temp_hash //= len(alphabet)
    
    return "".join(res)

async def main():
    print("Iniciando asignación de short_links estables basados en hash...")
    
    # Forzar uso de localhost para ejecución local si falla el DNS de Docker
    if 'DATABASE_URL' in os.environ:
        os.environ['DATABASE_URL'] = os.environ['DATABASE_URL'].replace('@db:5432', '@localhost:5432')
    
    try:
        await pg_manager.initialize()
    except Exception as e:
        print(f"Error de conexión: {e}")
        print("Intentando con fallback a localhost...")
        # Intentar forzar la URL si no estaba en env
        os.environ['DATABASE_URL'] = "postgresql+asyncpg://postgres:postgres@localhost:5432/zeepub_bot"
        await pg_manager.initialize()

    async with pg_manager.get_session() as session:
        # Buscamos todos los libros (para asegurar que si el hash cambió o no tenían, se actualicen)
        stmt = select(LocalBook)
        result = await session.execute(stmt)
        books = result.scalars().all()

        if not books:
            print("No se encontraron libros en la base de datos.")
            await pg_manager.close()
            return

        print(f"Procesando {len(books)} libros...")

        updates = 0
        for book in books:
            new_link = hash_to_short_link(book.book_hash)
            if book.short_link != new_link:
                book.short_link = new_link
                updates += 1

        if updates > 0:
            await session.commit()
            print(f"✅ Se han actualizado/asignado {updates} short_links de forma estable.")
        else:
            print("✨ Todos los short_links ya eran consistentes con el hash.")

    await pg_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
