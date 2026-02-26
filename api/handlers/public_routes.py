import logging
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook

router = APIRouter(prefix="/s")
logger = logging.getLogger(__name__)


@router.get("/{short_link}")
async def secure_short_download(short_link: str):
    """
    Descarga segura de un libro mediante su short_link.
    Protege el VPS ocultando la ruta real del archivo.
    """
    if not short_link or len(short_link) != 10:
        logger.warning(f"Intento de acceso a short_link inválido: {short_link}")
        raise HTTPException(status_code=400, detail="Enlace inválido")

    try:
        async with pg_manager.get_session() as session:
            stmt = select(LocalBook).where(LocalBook.short_link == short_link)
            result = await session.execute(stmt)
            book = result.scalar_one_or_none()

            if not book:
                logger.warning(f"Short link no encontrado: {short_link}")
                raise HTTPException(status_code=404, detail="Libro no encontrado o enlace expirado")

            if not os.path.exists(book.filepath) or not os.path.isfile(book.filepath):
                logger.error(f"Archivo no encontrado en servidor para el libro ID {book.id}: {book.filepath}")
                raise HTTPException(status_code=404, detail="El archivo físico no se encuentra disponible")

            logger.info(f"Descarga segura iniciada para: {book.title} ({short_link})")

            # Sanitizar título para el nombre de descarga (remover caracteres problemáticos)
            import re

            safe_title = re.sub(r'[\\/*?:"<>|]', "", book.title)

            return FileResponse(
                path=book.filepath,
                media_type="application/epub+zip",
                filename=f"{safe_title}.epub",
                content_disposition_type="attachment",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando descarga segura para {short_link}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor") from e
