import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.engine import make_url

from config.config_settings import config

logger = logging.getLogger(__name__)

BACKUP_DIR = Path("backups/database")
MAX_BACKUPS = 10


class BackupService:
    @staticmethod
    async def generate_backup_file(compress: bool = True) -> str:
        """
        Generates a database backup file using pg_dump (Async).
        Returns the path to the generated file.
        """
        if not config.DATABASE_URL:
            raise Exception(
                "DATABASE_URL no está configurada. PostgreSQL es obligatorio para backups."
            )

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_zeepub_{timestamp}.sql"
        if compress:
            filename += ".gz"

        filepath = BACKUP_DIR / filename

        # Get credentials
        pg_user = os.getenv("POSTGRES_USER")
        pg_password = os.getenv("POSTGRES_PASSWORD")
        pg_db = os.getenv("POSTGRES_DB")
        pg_host = os.getenv("POSTGRES_HOST", "db")

        try:
            url = make_url(config.DATABASE_URL)
            pg_user = pg_user or url.username
            pg_password = pg_password or url.password
            if url.host:
                pg_host = url.host
            pg_db = pg_db or url.database
        except Exception as e:
            logger.error(f"Error parsing DATABASE_URL: {e}")

        if not pg_user or not pg_password:
            raise Exception("No se encontraron credenciales de base de datos.")

        # Configure env for pg_dump
        env = os.environ.copy()
        env["PGPASSWORD"] = pg_password

        # Command construction
        if compress:
            # Pipe pg_dump to gzip
            cmd = f'pg_dump -h {pg_host} -U {pg_user} -d {pg_db} --clean --if-exists | gzip > "{filepath}"'
            logger.info(f"Iniciando backup DB (comprimido): {filepath}")

            proc = await asyncio.create_subprocess_shell(
                cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            cmd = [
                "pg_dump",
                "-h",
                pg_host,
                "-U",
                pg_user,
                "-d",
                pg_db,
                "-f",
                str(filepath),
                "--clean",
                "--if-exists",
            ]
            logger.info(f"Iniciando backup DB: {filepath}")

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise Exception("pg_dump timed out") from None

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="ignore")
            logger.error(f"pg_dump error: {err_msg}")
            raise Exception(f"pg_dump failed: {err_msg}")

        if not filepath.exists() or filepath.stat().st_size == 0:
            raise Exception("El archivo de backup se creó vacío o no existe.")

        logger.info(f"Backup creado: {filepath} ({filepath.stat().st_size} bytes)")

        await BackupService.rotate_backups()
        return str(filepath)

    @staticmethod
    async def rotate_backups():
        """Elimina backups antiguos manteniendo solo los últimos MAX_BACKUPS."""
        backups = sorted(BACKUP_DIR.glob("backup_zeepub_*.sql*"), reverse=True)
        for old_backup in backups[MAX_BACKUPS:]:
            try:
                old_backup.unlink()
                logger.info(f"Rotated old backup: {old_backup.name}")
            except Exception as e:
                logger.error(f"Error rotating backup {old_backup}: {e}")

    @staticmethod
    def list_backups() -> list[dict[str, Any]]:
        """Lista todos los backups disponibles."""
        backups = []
        if not BACKUP_DIR.exists():
            return []

        for f in sorted(BACKUP_DIR.glob("backup_zeepub_*.sql*"), reverse=True):
            stat = f.stat()
            backups.append(
                {
                    "filename": f.name,
                    "path": str(f),
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "compressed": f.suffix == ".gz",
                }
            )
        return backups

    @staticmethod
    def delete_backup(filename: str) -> bool:
        """Elimina un backup específico."""
        filepath = BACKUP_DIR / filename
        if filepath.exists() and filepath.parent == BACKUP_DIR:
            filepath.unlink()
            return True
        return False

    @staticmethod
    def get_backup_stats() -> dict[str, Any]:
        """Obtiene estadísticas de backups."""
        backups = BackupService.list_backups()
        total_size = sum(b["size_bytes"] for b in backups)
        return {
            "total_backups": len(backups),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_backups": MAX_BACKUPS,
        }
