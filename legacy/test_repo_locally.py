
import asyncio
import logging
import sys
import os

# Mocking config and other things if needed, or just using them
sys.path.append(os.getcwd())

from core.db_manager_pg import pg_manager
from repositories.user_repository import UserRepository

logging.basicConfig(level=logging.INFO)

async def test_repo():
    # Force DATABASE_URL to use localhost since we are running locally via tunnel
    from config.config_settings import config
    config.DATABASE_URL = "postgresql://zeepub:zeepub@localhost:5432/zeepub"
    
    await pg_manager.initialize()
    repo = UserRepository()
    
    uid = 133994080
    test_email = "test@example.com"
    
    print(f"Probando update_user_email para UID {uid}...")
    success = await repo.update_user_email(uid, test_email)
    
    if success:
        print("✅ ÉXITO: El repositorio pudo actualizar el email.")
    else:
        print("❌ FALLO: El repositorio no pudo actualizar el email.")

if __name__ == "__main__":
    asyncio.run(test_repo())
