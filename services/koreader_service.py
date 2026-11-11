import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.library import Book
from models.reading import KoreaderBookHash, ReadingProgress
from utils.koreader_hasher import calculate_koreader_fast_digest

logger = logging.getLogger(__name__)


class KoreaderService:
    """
    Servicio unificado de sincronización de lectura para KOReader y Web Reader.
    Garantiza sincronización bidireccional continua entre la Web App y e-readers físicos.
    """

    @staticmethod
    def compute_hash(filepath: Path | str) -> str | None:
        """Calcula el hash parcial de KOReader de forma segura."""
        try:
            return calculate_koreader_fast_digest(filepath)
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"No se pudo calcular hash KOReader para {filepath}: {e}")
            return None

    @classmethod
    async def index_book_koreader_hash(
        cls, session: AsyncSession, book_id: str, filepath: str
    ) -> str | None:
        """
        Calcula y almacena el hash de KOReader tanto en el modelo Book
        como en la tabla de mapeo koreader_book_hashes.
        """
        k_hash = cls.compute_hash(filepath)
        if not k_hash:
            return None

        try:
            # 1. Guardar en tabla koreader_book_hashes (Upsert PostgreSQL)
            stmt = (
                insert(KoreaderBookHash)
                .values(
                    koreader_hash=k_hash,
                    book_id=book_id,
                    created_at=datetime.now(UTC),
                )
                .on_conflict_do_update(
                    index_elements=["koreader_hash"],
                    set_={"book_id": book_id},
                )
            )
            await session.execute(stmt)

            # 2. Actualizar columna en modelo Book
            book = await session.get(Book, book_id)
            if book:
                book.koreader_hash = k_hash

            return k_hash
        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"Error al indexar hash KOReader para libro {book_id}: {e}")
            return None

    @classmethod
    async def get_book_by_koreader_hash(
        cls, session: AsyncSession, koreader_hash: str
    ) -> str | None:
        """Resuelve el book_id de ZeePub a partir de un hash parcial de KOReader."""
        # 1. Búsqueda en tabla de mapeo
        stmt = select(KoreaderBookHash.book_id).where(
            KoreaderBookHash.koreader_hash == koreader_hash
        )
        res = await session.execute(stmt)
        book_id = res.scalar_one_or_none()
        if book_id:
            return book_id

        # 2. Búsqueda directa en tabla books
        stmt_book = select(Book.id).where(Book.koreader_hash == koreader_hash)
        res_book = await session.execute(stmt_book)
        return res_book.scalar_one_or_none()

    @classmethod
    async def save_progress(
        cls,
        session: AsyncSession,
        user_id: int,
        book_id: str,
        progress_cfi: str,
        percentage: float,
        device_name: str | None = None,
        device_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Guarda o actualiza el progreso de lectura de un usuario para un libro.
        Utilizado directamente por el Web Reader (Foliate-js) o por la API de KOReader.
        """
        now = datetime.now(UTC)
        record_id = f"{user_id}_{book_id}"

        stmt = (
            insert(ReadingProgress)
            .values(
                id=record_id,
                user_id=user_id,
                book_id=book_id,
                progress_cfi=progress_cfi,
                percentage=percentage,
                device_name=device_name or "Web Reader",
                device_id=device_id or "web",
                updated_at=now,
            )
            .on_conflict_do_update(
                constraint="uq_user_book_reading_progress",
                set_={
                    "progress_cfi": progress_cfi,
                    "percentage": percentage,
                    "device_name": device_name or "Web Reader",
                    "device_id": device_id or "web",
                    "updated_at": now,
                },
            )
        )
        await session.execute(stmt)
        await session.commit()

        return {
            "book_id": book_id,
            "progress_cfi": progress_cfi,
            "percentage": percentage,
            "timestamp": int(now.timestamp()),
        }

    @classmethod
    async def get_progress_by_book_id(
        cls, session: AsyncSession, user_id: int, book_id: str
    ) -> dict[str, Any] | None:
        """Obtiene el progreso guardado de un libro para un usuario."""
        stmt = select(ReadingProgress).where(
            ReadingProgress.user_id == user_id,
            ReadingProgress.book_id == book_id,
        )
        res = await session.execute(stmt)
        prog = res.scalar_one_or_none()
        if not prog:
            return {
                "book_id": book_id,
                "percentage": 0.0,
                "progress_cfi": "",
                "timestamp": int(datetime.now(UTC).timestamp()),
            }

        return {
            "book_id": prog.book_id,
            "progress_cfi": prog.progress_cfi or "",
            "percentage": prog.percentage,
            "device": prog.device_name or "Web Reader",
            "device_id": prog.device_id or "",
            "timestamp": int(prog.updated_at.timestamp()),
        }

    @classmethod
    async def update_koreader_progress(
        cls,
        session: AsyncSession,
        user_id: int,
        koreader_hash: str,
        progress_cfi: str,
        percentage: float,
        device_name: str | None = None,
        device_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Actualiza el progreso invocado desde la API kosync."""
        book_id = await cls.get_book_by_koreader_hash(session, koreader_hash)
        if not book_id:
            logger.warning(f"Documento KOReader {koreader_hash} no indexado")
            return None

        result = await cls.save_progress(
            session=session,
            user_id=user_id,
            book_id=book_id,
            progress_cfi=progress_cfi,
            percentage=percentage,
            device_name=device_name or "KOReader",
            device_id=device_id or "koreader-device",
        )
        result["document"] = koreader_hash
        return result

    @classmethod
    async def get_koreader_progress(
        cls, session: AsyncSession, user_id: int, koreader_hash: str
    ) -> dict[str, Any] | None:
        """Obtiene el progreso formateado para el protocolo kosync."""
        book_id = await cls.get_book_by_koreader_hash(session, koreader_hash)
        if not book_id:
            return None

        prog_data = await cls.get_progress_by_book_id(session, user_id, book_id)
        if not prog_data:
            return None

        return {
            "document": koreader_hash,
            "progress": prog_data.get("progress_cfi", ""),
            "percentage": prog_data.get("percentage", 0.0),
            "device": prog_data.get("device", "KOReader"),
            "device_id": prog_data.get("device_id", ""),
            "timestamp": prog_data.get("timestamp", int(datetime.now(UTC).timestamp())),
        }
