import logging
import httpx
import os
import asyncio
from config.config_settings import config

logger = logging.getLogger(__name__)


async def trigger_watchtower_update():
    """
    Envía una solicitud a la API de Watchtower para buscar actualizaciones.
    Usa httpx con reintentos para mejorar la resiliencia ante micro-cortes de red.
    Retorna (success, message).
    """
    token = os.getenv("WATCHTOWER_TOKEN")
    if not token:
        return False, "WATCHTOWER_TOKEN no configurado en .env"

    # Watchtower API endpoint (Docker internal network)
    url = "http://watchtower:8080/v1/update"
    headers = {"Authorization": f"Bearer {token}"}

    # Configuración de reintentos y timeouts
    max_retries = 3
    # Aumentamos timeout a 30s para conexión y 90s para el request total
    timeout_config = httpx.Timeout(90.0, connect=30.0)

    async with httpx.AsyncClient(headers=headers, timeout=timeout_config) as client:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    f"Intento {attempt}/{max_retries}: Solicitando actualización a Watchtower..."
                )
                # Watchtower usa POST para updates
                resp = await client.post(url)

                if resp.status_code == 200:
                    return (
                        True,
                        "✅ Solicitud de actualización enviada a Watchtower con éxito.",
                    )
                else:
                    return (
                        False,
                        f"❌ Error de Watchtower ({resp.status_code}): {resp.text}",
                    )

            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                logger.warning(
                    f"Intento {attempt} fallido (Error de conexión): {repr(e)}"
                )
                if attempt == max_retries:
                    return (
                        False,
                        f"⚠️ Error conexión ({type(e).__name__}) tras {max_retries} intentos. "
                        "Si el bot se reinicia solo, la actualización ha funcionado.",
                    )
                await asyncio.sleep(2 * attempt)  # Backoff exponencial simple

            except httpx.ReadTimeout as e:
                # El ReadTimeout suele indicar que Watchtower recibió la orden pero el bot perdió la
                # conexión porque fue matado por el propio Watchtower o el socket se cerró.
                logger.info(
                    f"ReadTimeout detectado: {repr(e)}. Es probable que la actualización esté en curso."
                )
                return (
                    True,
                    "✅ Orden enviada. Si el sistema se reinicia, la actualización fue exitosa.",
                )

            except Exception as e:
                logger.error(f"Error inesperado en attempt {attempt}: {repr(e)}")
                return False, f"❌ Error inesperado: {type(e).__name__}"

    return False, "Error desconocido en el proceso de actualización."
