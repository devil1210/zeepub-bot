"""
services/v4/scheduler.py
--------------------------
Scheduler V4: integra PublisherService con PTB JobQueue.

Uso en bot.py / main.py:
    from services.v4.scheduler import register_jobs
    register_jobs(application)

La cola de publicación se procesa cada 60 segundos.
"""

import logging

from telegram.ext import Application

logger = logging.getLogger(__name__)


async def _process_publication_queue(context) -> None:
    """Job que procesa la cola de publicación pendiente."""
    from services.v4.publisher_service import PublisherService

    logger.info("Starting publication queue processor...")
    try:
        from core.db_manager_pg import pg_manager

        publisher = PublisherService(db_manager=pg_manager)
        results = await publisher.process_queue(bot_app=context.application)
        if results:
            sent = sum(1 for r in results if r.success)
            failed = sum(1 for r in results if not r.success)
            logger.info(f"[SCHEDULER] Cola procesada: {sent} enviados, {failed} fallidos")
    except Exception as e:
        logger.error(f"[SCHEDULER] Error procesando cola: {e}")


def register_jobs(app: Application, interval_seconds: int = 60) -> None:
    """
    Registra los jobs periódicos del scheduler en la JobQueue de PTB.
    Llamar después de Application.initialize().
    """
    job_queue = app.job_queue
    if not job_queue:
        logger.warning("JobQueue no disponible. El scheduler no se registrará.")
        return

    job_queue.run_repeating(
        _process_publication_queue,
        interval=interval_seconds,
        first=30,  # Primer run a los 30s del arranque
        name="publication_queue_processor",
    )
    logger.info(f"[SCHEDULER] publication_queue_processor registrado (cada {interval_seconds}s)")
