
import logging
import aiohttp
import os
from config.config_settings import config

logger = logging.getLogger(__name__)

async def trigger_watchtower_update():
    """
    Envía una solicitud a la API de Watchtower para buscar actualizaciones.
    Retorna (success, message).
    """
    token = os.getenv("WATCHTOWER_TOKEN")
    if not token:
        return False, "WATCHTOWER_TOKEN no configurado en .env"

    # Watchtower API endpoint
    # Como estamos en docker network, hostname es 'watchtower'
    url = "http://watchtower:8080/v1/update"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        async with aiohttp.ClientSession() as session:
            # Watchtower usa POST para updates
            async with session.post(url, headers=headers, timeout=60) as resp:
                if resp.status == 200:
                    return True, "✅ Solicitud de actualización enviada a Watchtower."
                else:
                    text = await resp.text()
                    return False, f"❌ Error de Watchtower ({resp.status}): {text}"
    except Exception as e:
        logger.error(f"Error trigger_watchtower_update: {repr(e)}")
        # Si el error es de conexión pero Watchtower recibió el request (como suele pasar),
        # podríamos informar "Posible éxito".
        return False, f"⚠️ Error conexión ({type(e).__name__}): {e}. Si Watchtower se reinició, la update funcionó."
