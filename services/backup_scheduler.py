import asyncio
import logging
import os
from datetime import datetime, timedelta

from config.config_settings import config
from services.backup_service import BackupService
from services.settings_service import get_setting

logger = logging.getLogger(__name__)


async def send_daily_backups(bot):
    """Genera y envía el backup diario unificado a los administradores."""
    db_file = None
    try:
        logger.info("Iniciando generación de backup diario unificado (PostgreSQL)...")

        # 1. Generar Backup
        try:
            db_file = await BackupService.generate_backup_file(compress=True)
        except Exception as e:
            logger.error(f"Error generando backup unificado: {e}")
            return

        if not db_file or not os.path.exists(db_file):
            logger.error("No se generó ningún archivo de backup válido")
            return

        sent_count = 0
        # Enviar a todos los admins
        for admin_id in config.ADMIN_USERS:
            try:
                with open(db_file, "rb") as f:
                    await bot.send_document(
                        chat_id=admin_id,
                        document=f,
                        filename=os.path.basename(db_file),
                        caption=f"📦 <b>Backup Diario Unificado (PG)</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="HTML",
                    )

                sent_count += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error enviando backup a admin {admin_id}: {e}")

        logger.info(f"Backup diario enviado a {sent_count} administradores")

    except Exception as e:
        logger.error(f"Error en send_daily_backups: {e}", exc_info=True)


async def daily_backup_scheduler(bot):
    """Tarea que ejecuta el backup diario según la configuración."""
    logger.info("Unified backup scheduler started")

    while True:
        try:
            # Obtener hora configurada (HH:MM), por defecto 04:00
            export_time = get_setting("export_time", "04:00")
            try:
                hour_str, minute_str = export_time.split(":")
                hour = int(hour_str)
                minute = int(minute_str)
            except Exception:
                logger.warning(f"Formato de export_time inválido '{export_time}', usando 04:00")
                hour, minute = 4, 0

            now = datetime.now()
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if next_run <= now:
                next_run += timedelta(days=1)

            wait_seconds = (next_run - now).total_seconds()
            logger.info(
                f"Próxima exportación diaria programada para: {next_run.strftime('%Y-%m-%d %H:%M')}"
            )

            await asyncio.sleep(wait_seconds)

            # Ejecutar backup
            logger.info("Ejecutando exportación diaria programada")
            await send_daily_backups(bot)

            # Esperar 1 minuto para evitar re-ejecución inmediata si el reloj es impreciso
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Error en daily_backup_scheduler: {e}", exc_info=True)
            await asyncio.sleep(3600)  # Reintentar en 1 hora si falla


def start_backup_scheduler(bot):
    """Inicia el scheduler unificado en background."""
    asyncio.create_task(daily_backup_scheduler(bot))
    logger.info("Unified backup scheduler task created")
