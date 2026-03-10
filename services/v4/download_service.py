"""
services/v4/download_service.py
---------------------------------
DownloadService: orquesta la verificación de límites, recuperación del archivo
y registro de la descarga. Es el servicio más crítico del bot.

Flujo:
  1. Obtener libro por book_hash (LibraryService)
  2. Verificar que el archivo existe en disco (StorageService)
  3. Verificar límite diario del usuario (DownloadRepository)
  4. Registrar la descarga (DownloadRepository)
  5. Devolver la ruta del archivo para que el handler la envíe vía Telegram
"""

from dataclasses import dataclass
from pathlib import Path

from repositories.download_repository import DownloadRepository
from repositories.library_repository import BookRepository
from repositories.user_repository import UserRepository

from .base_service import BaseService
from .storage_service import StorageService


@dataclass
class DownloadResult:
    """DTO devuelto por DownloadService.prepare_download()."""

    success: bool
    filepath: Path | None = None
    filename: str | None = None
    book_title: str | None = None
    book_hash: str | None = None
    file_size: int | None = None
    # Si success=False, el motivo del rechazo
    reason: str | None = None
    downloads_today: int = 0
    daily_limit: int = 0


class DownloadService(BaseService):
    """
    Orquesta el flujo completo de descarga de un EPUB.
    El handler sólo llama a prepare_download() y envía el archivo.
    """

    def __init__(self, db_manager=None):
        super().__init__(db_manager)
        self.storage = StorageService()

    async def prepare_download(
        self,
        telegram_id: int,
        book_hash: str,
        chat_id: int | None = None,
    ) -> DownloadResult:
        """
        Verifica límites, localiza el archivo y registra la descarga.
        Devuelve un DownloadResult con success=True y la ruta lista para send_document.
        """
        async with self.db.get_session() as session:
            # ── 1. Obtener libro ──────────────────────────────────────
            book_repo = BookRepository(session)
            book = await book_repo.get_by_hash(book_hash)

            if not book:
                return DownloadResult(
                    success=False,
                    reason="book_not_found",
                )

            # ── 2. Verificar que el archivo existe en disco ───────────
            filepath = await self.storage.get_filepath(book.filepath)
            if filepath is None:
                self.logger.warning(f"Archivo no encontrado en disco: {book.filepath}")
                return DownloadResult(
                    success=False,
                    book_title=book.title,
                    book_hash=book_hash,
                    reason="file_not_found",
                )

            # ── 3. Verificar usuario y límite diario ──────────────────
            user_repo = UserRepository(session)
            dl_repo = DownloadRepository(session)

            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                return DownloadResult(success=False, reason="user_not_found")

            lvl = user.level_info

            # Admins tienen límite ilimitado (daily_downloads = -1 convención)
            is_unlimited = (user.role == "admin") or (lvl and lvl.daily_downloads < 0)
            daily_limit = -1 if is_unlimited else (lvl.daily_downloads if lvl else 5)

            if not is_unlimited:
                downloads_today = await dl_repo.count_today(telegram_id)
                if downloads_today >= daily_limit:
                    return DownloadResult(
                        success=False,
                        reason="daily_limit_reached",
                        downloads_today=downloads_today,
                        daily_limit=daily_limit,
                        book_title=book.title,
                    )

            # ── 4. Registrar descarga ─────────────────────────────────
            await dl_repo.log_download(
                telegram_id=telegram_id,
                book_hash=book_hash,
                book_title=book.title,
                chat_id=chat_id,
            )

            file_size = await self.storage.get_file_size(book.filepath)

            self.logger.info(f"[DL] user={telegram_id} book={book_hash} file={filepath.name} size={file_size}")

            return DownloadResult(
                success=True,
                filepath=filepath,
                filename=filepath.name,
                book_title=book.title,
                book_hash=book_hash,
                file_size=file_size,
                daily_limit=daily_limit,
            )
