import os
import shutil
import gzip
from datetime import datetime
from pathlib import Path
from typing import List


class LibraryBackupService:
    """
    Servicio para gestionar backups de la base de datos de la biblioteca local.
    """

    def __init__(
        self, db_path: str, backup_dir: str = "library_backups", max_backups: int = 10
    ):
        """
        Args:
            db_path: Ruta al archivo de base de datos SQLite de la biblioteca
            backup_dir: Directorio donde se guardarán los backups
            max_backups: Número máximo de backups a mantener
        """
        self.db_path = db_path
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups

        # Crear directorio de backups si no existe
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, compress: bool = True) -> str:
        """
        Crea un backup de la base de datos.

        Args:
            compress: Si True, comprime el backup con gzip

        Returns:
            Ruta al archivo de backup creado
        """
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

        # Generar nombre del backup con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"library_backup_{timestamp}.db"

        if compress:
            backup_name += ".gz"
            backup_path = self.backup_dir / backup_name

            # Copiar y comprimir
            with open(self.db_path, "rb") as f_in:
                with gzip.open(backup_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            backup_path = self.backup_dir / backup_name
            shutil.copy2(self.db_path, backup_path)

        # Rotar backups antiguos
        self._rotate_backups()

        return str(backup_path)

    def list_backups(self) -> List[dict]:
        """
        Lista todos los backups disponibles.

        Returns:
            Lista de diccionarios con información de cada backup
        """
        backups = []

        for backup_file in sorted(
            self.backup_dir.glob("library_backup_*.db*"), reverse=True
        ):
            stat = backup_file.stat()
            backups.append(
                {
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "compressed": backup_file.suffix == ".gz",
                }
            )

        return backups

    def restore_backup(self, backup_filename: str) -> bool:
        """
        Restaura la base de datos desde un backup.

        Args:
            backup_filename: Nombre del archivo de backup

        Returns:
            True si la restauración fue exitosa
        """
        backup_path = self.backup_dir / backup_filename

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_filename}")

        # Crear backup de seguridad antes de restaurar
        safety_backup = f"{self.db_path}.before_restore"
        shutil.copy2(self.db_path, safety_backup)

        try:
            if backup_path.suffix == ".gz":
                # Descomprimir y restaurar
                with gzip.open(backup_path, "rb") as f_in:
                    with open(self.db_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # Restaurar directamente
                shutil.copy2(backup_path, self.db_path)

            return True
        except Exception as e:
            # Si falla, restaurar el backup de seguridad
            shutil.copy2(safety_backup, self.db_path)
            raise e
        finally:
            # Limpiar backup de seguridad
            if os.path.exists(safety_backup):
                os.remove(safety_backup)

    def delete_backup(self, backup_filename: str) -> bool:
        """
        Elimina un backup específico.

        Args:
            backup_filename: Nombre del archivo de backup

        Returns:
            True si se eliminó correctamente
        """
        backup_path = self.backup_dir / backup_filename

        if backup_path.exists():
            backup_path.unlink()
            return True

        return False

    def _rotate_backups(self):
        """
        Elimina backups antiguos manteniendo solo los últimos max_backups.
        """
        backups = sorted(self.backup_dir.glob("library_backup_*.db*"), reverse=True)

        # Eliminar backups excedentes
        for old_backup in backups[self.max_backups :]:
            old_backup.unlink()
            print(f"Rotated old backup: {old_backup.name}")

    def get_backup_stats(self) -> dict:
        """
        Obtiene estadísticas sobre los backups.

        Returns:
            Diccionario con estadísticas
        """
        backups = self.list_backups()

        total_size = sum(b["size_bytes"] for b in backups)

        return {
            "total_backups": len(backups),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_backup": backups[-1]["created_at"] if backups else None,
            "newest_backup": backups[0]["created_at"] if backups else None,
            "max_backups": self.max_backups,
        }
