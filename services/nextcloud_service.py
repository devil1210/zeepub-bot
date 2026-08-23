import logging
import os
from pathlib import Path
from urllib.parse import quote
import httpx

logger = logging.getLogger(__name__)


class NextcloudService:
    """
    Servicio Premium para interactuar con Nextcloud a través de WebDAV.
    Permite crear carpetas de forma recursiva y subir archivos de forma asíncrona y eficiente.
    """

    def __init__(self):
        # Cargar credenciales desde las variables de entorno
        self.url = os.getenv("NEXTCLOUD_URL")
        self.user = os.getenv("NEXTCLOUD_USER")
        self.password = os.getenv("NEXTCLOUD_PASSWORD")
        # Carpeta raíz base de subidas, por defecto "ZeePubs/01 En Revisión/Bot [Revisar]"
        raw_upload_path = os.getenv(
            "NEXTCLOUD_UPLOAD_PATH", "ZeePubs/01 En Revisión/Bot [Revisar]"
        )
        self.base_path = raw_upload_path.replace("\\", "/").strip("/")

    @property
    def is_active(self) -> bool:
        """Determina si el servicio está configurado y activo."""
        return bool(self.url and self.user and self.password)

    async def upload_file(self, local_path: Path, suggested_path: str) -> bool:
        """
        Sube un archivo local a Nextcloud de forma asíncrona vía WebDAV.
        suggested_path representa la ruta interna de la serie y volumen, por ejemplo:
        "Fujino Omori - DanMachi [NL]/DanMachi - V01.epub"
        """
        if not self.is_active:
            logger.warning(
                "⚠️ NextcloudService no está configurado en las variables de entorno."
            )
            return False

        if not local_path.exists():
            logger.error(
                f"❌ El archivo local no existe para subir a Nextcloud: {local_path}"
            )
            return False

        # Sanitizar y normalizar la ruta remota
        clean_suggested = suggested_path.replace("\\", "/").strip("/")
        remote_rel_path = (
            f"{self.base_path}/{clean_suggested}" if self.base_path else clean_suggested
        )

        # Construir endpoint WebDAV de Nextcloud
        # https://<nextcloud-domain>/remote.php/dav/files/<username>/<path>
        base_url = self.url.rstrip("/")
        webdav_url = (
            f"{base_url}/remote.php/dav/files/{self.user}/{quote(remote_rel_path)}"
        )

        logger.info(f"☁️ Subiendo archivo a Nextcloud: {remote_rel_path}")

        async with httpx.AsyncClient(timeout=120.0) as client:
            auth = (self.user, self.password)

            # 1. Asegurar directorios de forma secuencial y recursiva
            # Si subimos a "02-Publicaciones/Español/Serie/Libro.epub",
            # dir_parts será ["02-Publicaciones", "Español", "Serie"]
            dir_parts = remote_rel_path.rsplit("/", 1)[0].split("/")
            current_path = ""

            for part in dir_parts:
                if not part:
                    continue
                current_path = f"{current_path}/{part}" if current_path else part
                dir_url = (
                    f"{base_url}/remote.php/dav/files/{self.user}/{quote(current_path)}"
                )

                try:
                    logger.debug(f"Asegurando directorio en Nextcloud: {current_path}")
                    res = await client.request("MKCOL", dir_url, auth=auth)
                    # 201 Created = Éxito, 405 Method Not Allowed = Ya existe
                    if res.status_code not in (201, 405):
                        logger.warning(
                            f"Aviso al crear directorio '{current_path}' (HTTP {res.status_code})"
                        )
                except Exception as e:
                    logger.warning(
                        f"Excepción al asegurar directorio '{current_path}': {e}"
                    )

            # 2. Subir el archivo mediante PUT asíncrono
            try:
                # Leemos en stream binario para un rendimiento óptimo de memoria en archivos grandes
                with open(local_path, "rb") as f:
                    res = await client.put(webdav_url, content=f, auth=auth)

                # 201 (Created) o 204 (No Content/Actualizado con éxito)
                if res.status_code in (201, 204):
                    logger.info(
                        f"✅ Archivo subido exitosamente a Nextcloud: {remote_rel_path}"
                    )
                    return True
                else:
                    logger.error(
                        f"❌ Error subiendo a Nextcloud (HTTP {res.status_code}): {res.text}"
                    )
                    return False

            except Exception as e:
                logger.error(
                    f"❌ Excepción crítica al subir archivo a Nextcloud: {e}",
                    exc_info=True,
                )
                return False


# Instancia singleton del servicio para su importación y uso
nextcloud_service = NextcloudService()
