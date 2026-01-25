import asyncio
import json
import logging

from telegram.ext import ContextTypes

# from repositories.user_repository import user_repo (moved to function to avoid circular import)
from services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)


async def job_weekly_recommendations(context: ContextTypes.DEFAULT_TYPE):
    """
    Tarea programada para enviar recomendaciones semanales.
    Se ejecuta una vez a la semana (configurado en BotInitializer).
    """
    logger.info("Iniciando envío de recomendaciones semanales...")

    # 1. Obtener todos los usuarios (Iterar es seguro para volumen bajo/medio)
    # Optimización: Podríamos buscar solo aquellos con settings LIKE '%recommendations_enabled": true%'
    # pero JSON en texto es frágil. Mejor iterar en Python o añadir columna dedicada si escala.
    try:
        from repositories.user_repository import user_repo
        
        # Recuperamos IDs y settings desde repo
        rows = await user_repo.get_all_user_ids_and_settings()

        count_sent = 0
        for uid, settings in rows:
            try:
                # settings is already a dict from PG JSON column or Repo mapping
                if isinstance(settings, str):
                    settings = json.loads(settings)
                
                settings = settings or {}
                if settings.get("recommendations_enabled", False):
                    # Generar y enviar
                    await send_recommendation_to_user(context, uid)
                    count_sent += 1
                    await asyncio.sleep(0.5)  # Throttle para no saturar
            except Exception as e:
                logger.error(f"Error procesando user {uid} para recomendaciones: {e}")

        logger.info(f"Recomendaciones semanales finalizadas. Enviadas: {count_sent}")

    except Exception as e:
        logger.error(f"Error general en job_weekly_recommendations: {e}", exc_info=True)


async def send_recommendation_to_user(context: ContextTypes.DEFAULT_TYPE, uid: int):
    recs = await RecommendationService.get_recommendations(uid, limit=3)
    if not recs:
        return

    text = "👋 <b>¡Tu resumen semanal de lecturas!</b>\n\nAquí tienes 3 historias seleccionadas para ti:"

    try:
        await context.bot.send_message(chat_id=uid, text=text, parse_mode="HTML")

        # Reutilizar lógica de visualización (simplificada)
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        for book in recs:
            caption = (
                f"📚 <b>{book['title']}</b>\n"
                f"👤 {book['author']}\n"
                f"⭐ {book.get('rating_average', 0):.1f}"
            )
            local_id = book.get("id")
            kb = []
            if local_id:
                kb = [[InlineKeyboardButton("📥 Ver", callback_data=f"lib|local_{local_id}")]]

            await context.bot.send_message(
                chat_id=uid,
                text=caption,
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="HTML",
            )

    except Exception as e:
        logger.debug(f"No se pudo enviar recomendación a {uid} (bloqueado?): {e}")


def start_recommendations_scheduler(application):
    """
    Inicia el scheduler si no está ya corriendo.
    Se añade al JobQueue del application.
    """
    if not application.job_queue:
        logger.warning("No JobQueue available for recommendations.")
        return

    # ... rest of the logic ...
    import datetime
    time_to_run = datetime.time(hour=17, minute=00)  # 5 PM

    # Check if job exists named 'weekly_recs'
    current_jobs = application.job_queue.get_jobs_by_name("weekly_recs")
    if not current_jobs:
        # Run every Friday (5)
        application.job_queue.run_daily(
            job_weekly_recommendations,
            time=time_to_run,
            days=(4,),  # 0=Monday, 4=Friday
            name="weekly_recs"
        )
        logger.info("Scheduler de recomendaciones (Viernes 17:00) configurado.")
