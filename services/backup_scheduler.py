import asyncio
import logging
import os
from datetime import datetime, timedelta
from config.config_settings import config
from services.backup_service import generate_backup_file
from services.library_backup_service import LibraryBackupService
from utils.library_db import DB_PATH as LIB_DB_PATH
from services.settings_service import get_setting

logger = logging.getLogger(__name__)


async def send_daily_backups(bot):
    """Genera y envía los backups diarios a los administradores."""
    cache_file = None
    lib_file = None
    try:
        logger.info("Iniciando generación de backups diarios (Cache + Library)...")

        # 1. Backup de URL Cache
        try:
            cache_file = await generate_backup_file()
        except Exception as e:
            logger.error(f"Error generando backup de URL Cache: {e}")

        # 2. Backup de Library
        try:
            # Importante: El path de la DB de la librería debe existir
            if os.path.exists(LIB_DB_PATH):
                lib_service = LibraryBackupService(db_path=LIB_DB_PATH)
                lib_file = lib_service.create_backup(compress=True)
            else:
                logger.warning(f"No se encontró DB de librería en {LIB_DB_PATH}")
        except Exception as e:
            logger.error(f"Error generando backup de Library: {e}")

        if not cache_file and not lib_file:
            logger.error("No se generó ningún archivo de backup válido")
            return

        sent_count = 0
        # Enviar a todos los admins
        for admin_id in config.ADMIN_USERS:
            try:
                # Enviar Cache
                if cache_file and os.path.exists(cache_file):
                    with open(cache_file, "rb") as f:
                        await bot.send_document(
                            chat_id=admin_id,
                            document=f,
                            filename=os.path.basename(cache_file),
                            caption=f"📦 <b>Backup Diario URL Cache</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                            parse_mode="HTML"
                        )

                # Enviar Library
                if lib_file and os.path.exists(lib_file):
                    with open(lib_file, "rb") as f:
                        await bot.send_document(
                            chat_id=admin_id,
                            document=f,
                            filename=os.path.basename(lib_file),
                            caption=f"📚 <b>Backup Diario Library</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                            parse_mode="HTML"
                        )

                sent_count += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error enviando backups a admin {admin_id}: {e}")

        logger.info(f"Backups diarios enviados a {sent_count} administradores")

    except Exception as e:
        logger.error(f"Error en send_daily_backups: {e}", exc_info=True)
    finally:
        # Limpiar cache_file temporal
        if cache_file and os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except Exception:
                pass
        # lib_file se mantiene en su carpeta de rotación configurada en LibraryBackupService


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
