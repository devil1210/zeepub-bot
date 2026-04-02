
import os
import asyncio
import logging

# Set DATABASE_URL before any imports that use it
os.environ["DATABASE_URL"] = "postgresql://zeepub:zeepub@localhost:5432/zeepub"

import sys
sys.path.append(os.getcwd())

from core.db_manager_pg import pg_manager
from repositories.user_repository import UserRepository

logging.basicConfig(level=logging.INFO)

async def test_repo():
    await pg_manager.initialize()
    repo = UserRepository()
    
    uid = 133994080
    test_email = "test_repofix@example.com"
    
    print(f"Probando update_user_email para UID {uid}...")
    try:
        success = await repo.update_user_email(uid, test_email)
        if success:
            print("✅ ÉXITO: El repositorio pudo actualizar el email.")
        else:
            print("❌ FALLO: El repositorio no pudo actualizar el email.")
    except Exception as e:
        print(f"🔥 EXCEPCIÓN: {e}")

if __name__ == "__main__":
    asyncio.run(test_repo())
