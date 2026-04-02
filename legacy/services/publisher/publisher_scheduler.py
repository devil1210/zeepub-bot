import logging

from telegram.ext import Application

logger = logging.getLogger(__name__)


def start_publisher_scheduler(application: Application):
    """
    Configura el procesamiento periódico de la cola de publicación
    usando la JobQueue de Telegram Bot.
    """
    if not application.job_queue:
        logger.warning("JobQueue no disponible. No se puede iniciar el scheduler de publicación.")
        return

    # Procesar cada 5 minutos
    # Usamos un intervalo corto para mayor precisión en la programación
    application.job_queue.run_repeating(
        callback=process_queue_job,
        interval=300,  # 5 minutos
        first=10,  # Iniciar a los 10 segundos del arranque
        name="publisher_queue_processor",
    )
    logger.info("🚀 Scheduler de publicación iniciado (intervalo: 5m)")


async def process_queue_job(context):
    """
    Job que invoca el procesamiento de la cola usando una sesión de DB.
    """
    from core.database import async_session
    from services.publisher import PublisherService

    try:
        async with async_session() as session:
            service = PublisherService(session)
            await service.process_queue()
    except Exception as e:
        logger.error(f"❌ Error en job de cola de publicación: {e}", exc_info=True)
