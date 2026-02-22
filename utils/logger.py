import logging
import os
import functools
import time
import sqlite3
import json
from datetime import datetime

# Configuración básica
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "execution.log")
DB_FILE = os.path.join(LOG_DIR, "antigravity.db")

# Inicializar DB si no existe
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS executions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  func_name TEXT,
                  status TEXT,
                  duration REAL,
                  error TEXT,
                  metadata TEXT)''')
    conn.commit()
    conn.close()

init_db()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ZeePub-Agent")

def log_to_db(func_name, status, duration, error=None, metadata=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO executions (timestamp, func_name, status, duration, error, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                  (datetime.now().isoformat(), func_name, status, duration, str(error) if error else None, json.dumps(metadata) if metadata else None))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging to DB: {e}")

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
