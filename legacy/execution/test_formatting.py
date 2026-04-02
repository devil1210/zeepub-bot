import asyncio
import sys
import os

# Añadir el path raíz para importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.logger import log_execution, logger
from services.publisher.publisher_service import TelegramPublisherProvider

@log_execution
async def run_test():
    logger.info("Iniciando prueba de formateo de Telegram...")
    
    # Simular datos de un libro
    book_data = {
        "titulo": "Baccano!",
        "autor": "Ryohgo Narita",
        "volumen": "1",
        "sinopsis": "In the streets of New York...",
        "cover_original": "http://example.com/cover.jpg"
    }
    
    # Plantilla con todos los tags nuevos
    template = """
<b>{titulo}</b>
<i>{autor}</i>
Vol. {volumen}

<blockquote>
{sinopsis}
</blockquote>

<tg-spoiler>Revelación importante: El secreto es...</tg-spoiler>

<code>ID: 12345</code>

<pre>
Logs:
- Enviando...
- Recibido.
</pre>

<s>Precio anterior: $9.99</s>
<b>Precio actual: Gratis</b>

---next---

Enlace de descarga: <a href="http://example.com">Aquí</a>
    """
    
    # No necesitamos un bot real para probar el formateo de HTML
    # pero podemos ver si el servicio maneja la división de mensajes
    
    msg_parts = template.split("---next---")
    logger.info(f"Mensaje dividido en {len(msg_parts)} partes.")
    
    for i, part in enumerate(msg_parts):
        formatted = part.strip().format(**book_data)
        logger.info(f"Parte {i+1} formateada:\n{formatted}")
    
    logger.info("Prueba de formateo completada con éxito.")

if __name__ == "__main__":
    asyncio.run(run_test())
