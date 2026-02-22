import logging
import os
import functools
import time
from datetime import datetime

# Configuración básica
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "execution.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ZeePub-Agent")

def log_execution(func):
    """Decorador para registrar la ejecución de scripts/funciones en la Capa 3."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__
        logger.info(f"🚀 Iniciando ejecución: {func_name}")
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"✅ Éxito en {func_name} (Duración: {duration:.2f}s)")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Error en {func_name} después de {duration:.2f}s: {str(e)}", exc_info=True)
            raise
    return wrapper
