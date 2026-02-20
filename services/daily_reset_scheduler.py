import asyncio
import logging
from datetime import datetime, timedelta

from utils.download_limiter import reset_all_downloads

logger = logging.getLogger(__name__)


async def daily_reset_loop(bot=None):
    """
    Loop infinito que espera hasta la próxima medianoche para resetear las descargas.
    """
    logger.info("Daily reset scheduler started")
    while True:
        try:
            now = datetime.now()
            # Calcular próxima medianoche
            next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

            wait_seconds = (next_midnight - now).total_seconds()
            logger.info(f"Próximo reset de descargas en {wait_seconds:.0f} segundos ({next_midnight})")

            # Esperar hasta medianoche
            await asyncio.sleep(wait_seconds)

            # Ejecutar reporte antes del reset
            if bot:
                try:
                    from config.config_settings import config
                    from services.stats_service import get_daily_stats, reset_stats

                    data = await get_daily_stats()

                    # Formatear breakdown
                    by_role = data.get("by_role", {})
                    roles_txt = ""
                    if by_role:
                        roles_txt = "\n🏷️ <b>Por Nivel:</b>\n"
                        for r, count in by_role.items():
                            roles_txt += f"  • {r.capitalize()}: {count}\n"

                    report_text = (
                        "📊 <b>Reporte Diario Automático</b>\n\n"
                        f"👥 <b>Usuarios Únicos:</b> {data['unique_users']}\n"
                        f"⬇️ <b>Descargas Totales:</b> {data['total_downloads']}\n"
                        f"{roles_txt}"
                        "🔄 <i>Reseteando contadores...</i>"
                    )

                    for admin_id in config.ADMIN_USERS:
                        try:
                            await bot.send_message(chat_id=admin_id, text=report_text, parse_mode="HTML")
                        except Exception as e:
                            logger.error(f"Error enviando reporte a admin {admin_id}: {e}")

                    # Resetear stats
                    await reset_stats()
                except Exception as e:
                    logger.error(f"Error generando reporte diario: {e}")

            # Ejecutar reset descargas
            logger.info("Ejecutando reset diario de descargas...")
            reset_all_downloads()
            logger.info("Reset diario completado.")

            # Pequeña pausa para asegurar que no se ejecute dos veces en el mismo segundo (improbable pero seguro)
            await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Daily reset scheduler cancelled")
            break
        except Exception as e:
            logger.error(f"Error en daily_reset_loop: {e}", exc_info=True)
            # Esperar un poco antes de reintentar para evitar bucle rápido de errores
            await asyncio.sleep(60)


def start_daily_reset_scheduler(bot=None):
    """
    Inicia la tarea de reset diario en background.
    """
    asyncio.create_task(daily_reset_loop(bot))
    logger.info("Daily reset scheduler task created")
