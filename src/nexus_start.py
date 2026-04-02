# src/nexus_start.py
import asyncio
import logging
import uvicorn
from src.api.main_api import app
from src.bot.main_bot import create_bot_app
from src.core.db import db_manager
from src.core.config import settings

# Configuración de Logging centralizada
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
)
logger = logging.getLogger("NexusOrchestrator")

async def run_bot():
    """Ejecuta el bot de Telegram de forma concurrente con la API."""
    bot_app = create_bot_app()
    if not bot_app:
        logger.error("❌ NexusBot: No se pudo crear la aplicación del bot.")
        return
        
    try:
        logger.info("NexusBot: Inicializando servicios...")
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling()
        logger.info("NexusBot: Escuchando mensajes (Polling activo).")
        
        # Mantener el loop de eventos vivo para el bot indefinitely
        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        logger.error(f"❌ NexusBot: Error fatal en el proceso del bot: {e}")

async def main():
    """Orquestador principal Zeepub-Nexus."""
    print("Zeepub-Nexus: Iniciando Orquestador...")
    
    # 1. Asegurar persistencia y esquemas (Foundation)
    print(f"Nexus: Conectando a {settings.DATABASE_URL}...")
    await db_manager.initialize()
    print("Nexus: Base de Datos Inicializada.")
    
    # 2. Configurar servidor API
    print("NexusAPI: Configurando servidor en puerto 8000...")
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        access_log=True
    )
    server = uvicorn.Server(config)
    
    # 3. Lanzar Bot y API en paralelo
    print("Nexus: Lanzando Bot y API concurrentemente...")
    try:
        await asyncio.gather(
            run_bot(),
            server.serve()
        )
    except Exception as e:
        print(f"❌ Nexus Error: {e}")
    finally:
        print("🛑 Nexus: Apagando sistema...")
        await db_manager.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Nexus: Interrumpido por el usuario.")
