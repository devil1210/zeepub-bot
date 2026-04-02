
import asyncio
import logging
import sys
import os

# Asegurar que el directorio raíz está en el path para importar módulos
sys.path.append(os.getcwd())

from config.config_settings import config
from services.notion_service import notion_service

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_notion_integration():
    print(f"Testing Notion Integration...")
    print(f"Token: {config.NOTION_TOKEN[:5]}...*****")
    print(f"Database ID: {config.NOTION_DATABASE_ID}")

    # Datos de prueba
    user_name = "Test User 🤖"
    book_title = "Libro de Prueba"
    series_name = "Serie Test"
    volume = "1"
    author = "Autor Test"

    print(f"\nEnviando log de lectura para: {book_title}...")
    
    success = await notion_service.log_reading(
        user_name=user_name,
        book_title=book_title,
        series_name=series_name,
        volume=volume,
        author=author
    )

    if success:
        print("\n✅ ÉXITO: El log debería aparecer en tu página de Notion ahora mismo.")
    else:
        print("\n❌ FALLO: Revisa los logs de error arriba.")

if __name__ == "__main__":
    asyncio.run(test_notion_integration())
