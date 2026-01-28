import logging
import os

import httpx

logger = logging.getLogger(__name__)


async def trigger_watchtower_update():
    """
    Envía una solicitud a la API de Watchtower para buscar actualizaciones.
    Implementa un sistema de descubrimiento "inteligente" probando varias URLs
    comunes (Docker, localhost, Gateway) para maximizar la compatibilidad.
    """
    token = os.getenv("WATCHTOWER_TOKEN")
    if not token:
        return False, "WATCHTOWER_TOKEN no configurado en .env"

    # Lista de URLs potenciales para probar
    # 1. 'watchtower:8080' -> Estándar dentro de Docker Compose
    # 2. 'localhost:8081' -> Si el bot está en el host y mapeó el puerto (visto en compose)
    # 3. '192.168.1.1:8081' -> Si el bot está en LXC y Watchtower en el host Proxmox
    # 4. '172.17.0.1:8081' -> Si el bot está en Docker intentando llegar al host (gateway)

    potential_urls = [
        "http://watchtower:8080/v1/update",
        "http://localhost:8081/v1/update",
        "http://192.168.1.1:8081/v1/update",
        "http://172.17.0.1:8081/v1/update",
    ]

    # Permitir sobreescribir vía .env para casos especiales
    custom_url = os.getenv("WATCHTOWER_URL")
    if custom_url:
        potential_urls.insert(0, custom_url)

    headers = {"Authorization": f"Bearer {token}"}
    timeout_config = httpx.Timeout(15.0, connect=5.0)  # Menor timeout para fail-fast entre URLs

    last_error = ""

    async with httpx.AsyncClient(headers=headers, timeout=timeout_config) as client:
        for url in potential_urls:
            try:
                logger.info(f"Intentando conectar con Watchtower en: {url}...")
                resp = await client.post(url)

                if resp.status_code == 200:
                    logger.info(f"✅ Conexión exitosa con Watchtower vía {url}")
                    return True, f"✅ Solicitud enviada con éxito (vía {url})."
                else:
                    err = f"Error {resp.status_code} en {url}: {resp.text}"
                    logger.warning(err)
                    last_error = err

            except httpx.ConnectError:
                logger.debug(f"Servidor no disponible en {url} (ConnectError)")
                continue
            except httpx.ConnectTimeout:
                logger.debug(f"Servidor no disponible en {url} (Timeout)")
                continue
            except httpx.ReadTimeout:
                # El ReadTimeout suele indicar éxito si el sistema empieza a reiniciarse antes de responder
                logger.info(
                    f"ReadTimeout en {url}. Altas probabilidades de que la actualización esté iniciando."
                )
                return (
                    True,
                    "✅ Orden enviada. Si el sistema se reinicia, la actualización fue exitosa.",
                )
            except Exception as e:
                logger.error(f"Error inesperado probando {url}: {repr(e)}")
                last_error = str(e)

    # Si llegamos aquí, ninguno funcionó
    return False, (
        f"❌ No se pudo contactar con Watchtower en ninguna de las rutas.\n"
        f"Último error: {last_error or 'Host no encontrado'}.\n\n"
        "🔧 Tip: Verifica que Watchtower esté corriendo y sea accesible."
    )
