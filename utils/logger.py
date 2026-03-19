import functools
import json
import logging
import os
import sys
import time

from models.agent_models import AgentExecution
from utils.library_db import get_session

# Configuración básica
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "execution.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("ZeePub-Agent")


def log_to_db(func_name, status, duration, error=None, metadata=None):
    """Registra la ejecución en PostgreSQL."""
    try:
        session = get_session()
        execution = AgentExecution(
            func_name=func_name,
            status=status,
            duration=duration,
            error=str(error) if error else None,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        session.add(execution)
        session.commit()
        session.close()
    except Exception as e:
        logger.error(f"Error logging to PostgreSQL: {e}")


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
            log_to_db(func_name, "SUCCESS", duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Error en {func_name} después de {duration:.2f}s: {str(e)}", exc_info=True)
            log_to_db(func_name, "ERROR", duration, error=e)
            raise

    return wrapper
