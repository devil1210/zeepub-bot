import os
import logging
import asyncio
from datetime import datetime
from sqlalchemy.engine import make_url
from config.config_settings import config

logger = logging.getLogger(__name__)


async def generate_backup_file() -> str:
    """
    Generates a database backup file.
    Returns the path to the generated file.
    Raises Exception on failure.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Determine if using PostgreSQL or SQLite
    if config.DATABASE_URL:
        # --- PostgreSQL Logic ---
        filename = f"backup_zeepub_{timestamp}.sql"

        # Get credentials
        pg_user = os.getenv("POSTGRES_USER")
        pg_password = os.getenv("POSTGRES_PASSWORD")
        pg_db = os.getenv("POSTGRES_DB")
        pg_host = os.getenv("POSTGRES_HOST", "db")  # Default to 'db' service in docker

        # If not in env, try parsing DATABASE_URL
        if not pg_user and config.DATABASE_URL:
            try:
                url = make_url(config.DATABASE_URL)
                pg_user = url.username
                pg_password = url.password
                if url.host:
                    pg_host = url.host
                pg_db = url.database
            except Exception as e:
                logger.error(f"Error parsing DATABASE_URL: {e}")

        if not pg_user or not pg_password:
            raise Exception(
                "No se encontraron credenciales de base de datos (POSTGRES_USER/PASSWORD o DATABASE_URL)."
            )

        # Configure env for pg_dump
        env = os.environ.copy()
        env["PGPASSWORD"] = pg_password

        # pg_dump command
        cmd = ["pg_dump", "-h", pg_host, "-U", pg_user, "-d", pg_db, "-f", filename]

        logger.info(f"Iniciando backup DB: host={pg_host}, user={pg_user}, db={pg_db}")

        # Execute pg_dump
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise Exception("pg_dump timed out (120s)")

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="ignore")
            logger.error(f"pg_dump error: {err_msg}")
            raise Exception(f"pg_dump failed: {err_msg}")

        # Verify file size
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            raise Exception("El archivo de backup se creó vacío o no existe.")

        logger.info(
            f"Backup creado exitosamente: {filename} ({os.path.getsize(filename)} bytes)"
        )
        return filename

    else:
        # --- SQLite Logic ---
        db_path = config.URL_CACHE_DB_PATH
        if not os.path.exists(db_path):
            raise Exception(f"No se encontró la base de datos SQLite en: {db_path}")

        # Create a copy with timestamp
        sqlite_filename = f"backup_zeepub_sqlite_{timestamp}.db"

        # Use asyncio to copy file to avoid blocking
        def copy_file():
            import shutil

            shutil.copy2(db_path, sqlite_filename)

        await asyncio.to_thread(copy_file)

        return sqlite_filename
