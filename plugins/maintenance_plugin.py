import logging
import os
import asyncio
import sqlite3
import csv
import io
import shutil
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from plugins.base_plugin import BasePlugin
from config.config_settings import config
from utils.helpers import get_thread_id
from core.state_manager import state_manager
from utils.url_cache import DB_PATH  # For usage in export_db/restore_db (SQLite)

logger = logging.getLogger(__name__)


class MaintenancePlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "maintenance_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Herramientas de mantenimiento de base de datos e historial."

    async def initialize(self, bot_instance) -> bool:
        self.enabled = os.getenv("ENABLE_DB_MAINTENANCE", "True").lower() == "true"

        if not self.enabled:
            logger.info("Plugin Maintenance desactivado por configuración.")
            return False

        try:
            app = bot_instance
            # Admin only commands
            app.add_handler(CommandHandler("backup_db", self.backup_db))
            app.add_handler(CommandHandler("restore_db", self.restore_db))
            app.add_handler(CommandHandler("import_history", self.import_history))
            app.add_handler(CommandHandler("latest_books", self.latest_books))
            app.add_handler(CommandHandler("clear_history", self.clear_history))
            app.add_handler(CommandHandler("scan_library", self.scan_library, block=False))
            app.add_handler(CommandHandler("reset_stats", self.reset_stats))
            app.add_handler(CommandHandler("reset_library", self.reset_library))

            # Publisher/Admin commands
            app.add_handler(CommandHandler("export_db", self.export_db))
            app.add_handler(CommandHandler("export_history", self.export_history))
            app.add_handler(CommandHandler("set_export_time", self.set_export_time))

            logger.info("Plugin Maintenance: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin Maintenance: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    async def backup_db(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Realiza un backup de la base de datos (solo admins)."""
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            await update.message.reply_text(
                "⛔ No tienes permisos para usar este comando."
            )
            return

        thread_id = get_thread_id(update)
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_prep = "⏳ Generando backup..."
        text_prep = (
            await cms.get_text("maint_backup_preparing")
            if (cms and cms.enabled)
            else base_prep
        )
        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text_prep,
            message_thread_id=thread_id,
        )

        try:
            from services.backup_service import generate_backup_file

            filename = await generate_backup_file()

            # Enviar archivo
            base_caption = f"📦 Backup de base de datos\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            caption = (
                await cms.get_text("maint_backup_caption", Fecha=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                if (cms and cms.enabled)
                else base_caption
            )
            with open(filename, "rb") as f:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=f,
                    filename=filename,
                    caption=caption,
                    message_thread_id=thread_id,
                )

            # Limpiar
            try:
                os.remove(filename)
            except Exception:
                logger.debug("No se pudo eliminar backup temporal: %s", filename)

            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=msg.message_id
            )

        except Exception as e:
            logger.error(f"Error en backup_db: {e}", exc_info=True)
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=f"❌ Error al generar backup: {str(e)}",
            )

    async def restore_db(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Restaura la base de datos desde un archivo (solo admins)."""
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            await update.message.reply_text(
                "⛔ No tienes permisos para usar este comando."
            )
            return

        if (
            not update.message.reply_to_message
            or not update.message.reply_to_message.document
        ):
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_err = "⚠️ Debes responder a un mensaje con el archivo .sql de backup para restaurarlo."
            text_err = (
                await cms.get_text("maint_restore_error_no_doc")
                if (cms and cms.enabled)
                else base_err
            )
            await update.message.reply_text(text_err)
            return

        doc = update.message.reply_to_message.document
        thread_id = get_thread_id(update)
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_prep = "⏳ Descargando y restaurando backup... (Esto borrará los datos actuales)"
        text_prep = (
            await cms.get_text("maint_restore_preparing")
            if (cms and cms.enabled)
            else base_prep
        )
        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text_prep,
            message_thread_id=thread_id,
        )

        try:
            # Descargar archivo
            file = await doc.get_file()

            if config.DATABASE_URL:
                # --- Lógica PostgreSQL ---
                if not doc.file_name.endswith(".sql"):
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=msg.message_id,
                        text="⚠️ Para PostgreSQL, el archivo debe ser un .sql",
                    )
                    return

                filename = f"restore_{doc.file_name}"
                await file.download_to_drive(filename)

                # Obtener credenciales
                pg_user = os.getenv("POSTGRES_USER")
                pg_password = os.getenv("POSTGRES_PASSWORD")
                pg_db = os.getenv("POSTGRES_DB")
                pg_host = "db"

                if not pg_user:
                    try:
                        from sqlalchemy.engine import make_url

                        url = make_url(config.DATABASE_URL)
                        pg_user = url.username
                        pg_password = url.password
                        if url.host:
                            pg_host = url.host
                        pg_db = url.database
                    except Exception:
                        pass

                if not pg_user or not pg_password:
                    raise Exception("No se encontraron credenciales de base de datos.")

                # Configurar entorno
                env = os.environ.copy()
                env["PGPASSWORD"] = pg_password

                # Comando psql para restaurar
                cmd = [
                    "psql",
                    "-h",
                    pg_host,
                    "-U",
                    pg_user,
                    "-d",
                    pg_db,
                    "-f",
                    filename,
                ]

                # Use asyncio subprocess
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(), timeout=180
                    )
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    raise Exception("psql restore timed out")
                if proc.returncode != 0:
                    raise Exception(f"Restore failed: {stderr.decode(errors='ignore')}")

                try:
                    os.remove(filename)
                except Exception:
                    logger.debug(
                        "No se pudo eliminar archivo temporal de restore: %s", filename
                    )

            else:
                # --- Lógica SQLite ---
                if not (
                    doc.file_name.endswith(".db") or doc.file_name.endswith(".sqlite")
                ):
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=msg.message_id,
                        text="⚠️ Para SQLite, el archivo debe ser .db o .sqlite",
                    )
                    return

                # Sobrescribir el archivo de base de datos
                # Backup de seguridad antes de sobrescribir
                if os.path.exists(DB_PATH):
                    backup_path = f"{DB_PATH}.bak"
                    shutil.copy2(DB_PATH, backup_path)

                await file.download_to_drive(DB_PATH)

            base_success = "✅ Base de datos restaurada exitosamente."
            text_success = (
                await cms.get_text("maint_restore_success")
                if (cms and cms.enabled)
                else base_success
            )
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=text_success,
            )
            logger.info(f"Admin {uid} restauró la base de datos desde {doc.file_name}")

        except Exception as e:
            logger.error(f"Error en restore_db: {e}", exc_info=True)
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=f"❌ Error al restaurar backup: {str(e)}",
            )

    async def export_db(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Exporta la base de datos a CSV (solo publishers)."""
        uid = update.effective_user.id
        if uid not in config.FACEBOOK_PUBLISHERS:
            await update.message.reply_text(
                "⛔ No tienes permisos para usar este comando."
            )
            return

        thread_id = get_thread_id(update)
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_prep = "⏳ Generando CSV de la base de datos..."
        text_prep = (
            await cms.get_text("maint_export_preparing")
            if (cms and cms.enabled)
            else base_prep
        )
        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text_prep,
            message_thread_id=thread_id,
        )

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_db_{timestamp}.csv"

            # Determinar si usar PostgreSQL o SQLite
            if config.DATABASE_URL:
                # PostgreSQL usando SQLAlchemy
                from sqlalchemy import create_engine, text

                engine = create_engine(config.DATABASE_URL)

                with engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT * FROM url_mappings ORDER BY created_at DESC")
                    )
                    rows = result.fetchall()
                    columns = result.keys()

                # Escribir CSV en thread pool
                def _write_csv(path, columns, rows):
                    with open(path, "w", newline="", encoding="utf-8") as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(columns)
                        writer.writerows(rows)

                await asyncio.to_thread(_write_csv, filename, columns, rows)

            else:
                # SQLite
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM url_mappings ORDER BY created_at DESC")
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                conn.close()

                # Escribir CSV en thread pool
                def _write_csv(path, columns, rows):
                    with open(path, "w", newline="", encoding="utf-8") as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(columns)
                        writer.writerows(rows)

                await asyncio.to_thread(_write_csv, filename, columns, rows)

            # Enviar archivo
            base_caption = f"📊 Exportación de base de datos\n📅 {timestamp}\n📦 {len(rows)} registros"
            caption = (
                await cms.get_text("maint_export_caption", Fecha=timestamp, Registros=len(rows))
                if (cms and cms.enabled)
                else base_caption
            )
            with open(filename, "rb") as f:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=f,
                    filename=filename,
                    caption=caption,
                    message_thread_id=thread_id,
                )

            try:
                os.remove(filename)
            except Exception:
                logger.debug("No se pudo eliminar CSV temporal: %s", filename)
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=msg.message_id
            )

        except Exception as e:
            logger.error(f"Error en export_db: {e}", exc_info=True)
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=f"❌ Error al generar CSV: {str(e)}",
            )

    async def import_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Activa el modo de importación de historial (solo admins)."""
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            await update.message.reply_text(
                "⛔ No tienes permisos para usar este comando."
            )
            return

        st = state_manager.get_user_state(uid)
        st["waiting_for_history_json"] = True
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_instr = (
            "📂 <b>Modo de Importación Activado</b>\n\n"
            "Por favor, envía ahora el archivo <code>result.json</code> exportado de Telegram Desktop.\n"
            "El bot procesará el archivo y guardará el historial de libros publicados.\n\n"
            "<i>Este modo se desactivará automáticamente después de recibir el archivo.</i>"
        )
        text_instr = (
            await cms.get_text("maint_import_instructions")
            if (cms and cms.enabled)
            else base_instr
        )

        await update.message.reply_text(
            text_instr,
            parse_mode="HTML",
        )

    async def latest_books(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra los últimos 10 libros importados/publicados (solo admins)."""
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            await update.message.reply_text(
                "⛔ No tienes permisos para usar este comando."
            )
            return

        try:
            from services.history_service import get_latest_books

            # Parse argumentos: chat_id opcional
            channel_filter = None
            if context.args and len(context.args) > 0:
                try:
                    channel_filter = int(context.args[0])
                except ValueError:
                    await update.message.reply_text(
                        "❌ Chat ID inválido. Uso: /latest_books [chat_id]\n"
                        "Ejemplo: /latest_books -1001234567890"
                    )
                    return

            books = get_latest_books(limit=10, channel_id=channel_filter)

            if not books:
                if channel_filter:
                    await update.message.reply_text(
                        f"📚 No hay libros registrados en el chat {channel_filter}."
                    )
                else:
                    await update.message.reply_text(
                        "📚 No hay libros registrados en el historial."
                    )
                return

            if channel_filter:
                text = f"📚 <b>Últimos 10 Libros en Chat {channel_filter}</b>\n\n"
            else:
                text = "📚 <b>Últimos 10 Libros Publicados</b>\n\n"

            for b in books:
                title = b.title or "Sin título"
                author = b.author or "Desconocido"
                series = f" ({b.series})" if b.series else ""
                date_str = (
                    b.date_published.strftime("%Y-%m-%d %H:%M")
                    if b.date_published
                    else "?"
                )

                text += f"🔹 <b>{title}</b>{series}\n"
                text += f"   ✍️ {author}\n"
                text += f"   📅 {date_str} | #{b.slug}\n"

                if not channel_filter and hasattr(b, "channel_id") and b.channel_id:
                    text += f"   📍 Chat: {b.channel_id}\n"

                text += "\n"

            await update.message.reply_text(text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Error in latest_books: {e}")
            await update.message.reply_text("❌ Error al obtener el historial.")

    async def clear_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Borra todo el historial de libros publicados (solo admin)."""
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            await update.message.reply_text(
                "⛔ No tienes permisos para usar este comando."
            )
            return

        if not context.args or context.args[0] != "confirm":
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_confirm = (
                "⚠️ <b>¡ATENCIÓN!</b> Esto borrará TODO el historial de libros publicados.\n"
                "Para confirmar, usa: <code>/clear_history confirm</code>"
            )
            text_confirm = (
                await cms.get_text("maint_history_clear_confirm")
                if (cms and cms.enabled)
                else base_confirm
            )
            await update.message.reply_text(
                text_confirm,
                parse_mode="HTML",
            )
            return

        try:
            from services.history_service import clear_history

            if clear_history():
                cms = context.application.plugin_manager.get_plugin("custom_messages")
                base_success = "✅ Historial borrado exitosamente."
                text_success = (
                    await cms.get_text("maint_history_cleared")
                    if (cms and cms.enabled)
                    else base_success
                )
                await update.message.reply_text(text_success)
            else:
                await update.message.reply_text("❌ Error al borrar el historial.")
        except Exception as e:
            logger.error(f"Error en clear_history: {e}")
            await update.message.reply_text(
                "❌ Error interno al intentar borrar historial."
            )

    async def export_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Exporta el historial de libros publicados a CSV."""
        uid = update.effective_user.id
        # Allow publishers and admins
        if uid not in config.ADMIN_USERS and uid not in config.PUBLISHER_USERS:
            await update.message.reply_text(
                "⛔ No tienes permisos para usar este comando."
            )
            return

        try:
            from services.history_service import get_latest_books

            books = get_latest_books(limit=10000)

            if not books:
                await update.message.reply_text(
                    "📚 No hay libros registrados en el historial."
                )
                return

            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(
                [
                    "Título",
                    "Maquetado por",
                    "Demografía",
                    "Géneros",
                    "Autor",
                    "Serie",
                    "Slug",
                    "Ilustrador",
                    "Traducción",
                    "Fecha Publicación",
                    "Tamaño",
                ]
            )

            # Data
            for b in books:
                file_size_str = ""
                if hasattr(b, "file_size") and b.file_size:
                    file_size_mb = b.file_size / (1024 * 1024)
                    file_size_str = f"{file_size_mb:.2f} MB"

                writer.writerow(
                    [
                        b.title or "Unknown",
                        b.maquetado_por or "" if hasattr(b, "maquetado_por") else "",
                        b.demografia or "" if hasattr(b, "demografia") else "",
                        b.generos or "" if hasattr(b, "generos") else "",
                        b.author or "Desconocido",
                        b.series or "",
                        b.slug or "",
                        b.ilustrador or "" if hasattr(b, "ilustrador") else "",
                        b.traduccion or "" if hasattr(b, "traduccion") else "",
                        (
                            b.date_published.strftime("%Y-%m-%d %H:%M")
                            if b.date_published
                            else ""
                        ),
                        file_size_str,
                    ]
                )

            # Send file
            output.seek(0)
            # Encode to bytes
            csv_bytes = output.getvalue().encode("utf-8")

            # Timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"history_export_{timestamp}.csv"

            thread_id = get_thread_id(update)
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=csv_bytes,
                filename=filename,
                caption=f"📊 Exportación de Historial\n📅 {timestamp}\n📚 {len(books)} libros",
                message_thread_id=thread_id,
            )

        except Exception as e:
            logger.error(f"Error en export_history: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Error generando exportación de historial."
            )

    async def scan_library(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia el escaneo de la biblioteca local (solo admins)."""
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            await update.message.reply_text("⛔ No tienes permisos para usar este comando.")
            return

        force = context.args and context.args[0].lower() == "force"
        thread_id = get_thread_id(update)

        scan_type = " (FORZADO)" if force else ""
        msg = await update.message.reply_text(
            f"🔍 <b>Iniciando escaneo de biblioteca local{scan_type}...</b>\nEsto puede tardar unos minutos.",
            parse_mode="HTML",
            message_thread_id=thread_id
        )

        try:
            from services.scanner_service import ScannerService

            libs_json = os.getenv("LOCAL_LIBRARIES")
            if not libs_json:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=msg.message_id,
                    text="❌ No se ha configurado la variable <code>LOCAL_LIBRARIES</code>.",
                    parse_mode="HTML"
                )
                return

            # Ejecutar escaneo en un hilo separado para no bloquear el bot
            scanner = ScannerService(libs_json)
            await asyncio.to_thread(scanner.sync_all, force_scan=force)

            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text="✅ <b>Escaneo completado con éxito.</b>\nLa base de datos local ha sido actualizada.",
                parse_mode="HTML"
            )
            logger.info(f"Admin {uid} inició y completó escaneo de biblioteca.")

        except Exception as e:
            logger.error(f"Error en scan_library: {e}", exc_info=True)
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=f"❌ Error durante el escaneo: {str(e)}"
            )

    async def set_export_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Configura la hora de la exportación diaria (solo admins)."""
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            await update.message.reply_text("⛔ No tienes permisos para usar este comando.")
            return

        if not context.args:
            await update.message.reply_text("⚠️ Uso: /set_export_time HH:MM (ej: 04:00)")
            return

        time_str = context.args[0]
        # Validar formato HH:MM
        if not re.match(r"^\d{2}:\d{2}$", time_str):
            await update.message.reply_text("❌ Formato inválido. Usa HH:MM (ej: 04:30).")
            return

        try:
            from services.settings_service import set_setting
            set_setting("export_time", time_str)

            await update.message.reply_text(
                f"✅ Hora de exportación configurada a las <b>{time_str}</b>.",
                parse_mode="HTML"
            )
            logger.info(f"Admin {uid} cambió la hora de exportación a {time_str}")
        except Exception as e:
            logger.error(f"Error en set_export_time: {e}")
            await update.message.reply_text("❌ Error al guardar la configuración.")
    async def reset_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reinicia globalmente los contadores de descarga y valoraciones (solo admins)."""
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            await update.message.reply_text("⛔ No tienes permisos para usar este comando.")
            return

        if not context.args or context.args[0].lower() != "confirm":
            await update.message.reply_text(
                "⚠️ <b>¡ATENCIÓN!</b> Esto borrará TODO el historial de descargas y valoraciones.\n"
                "Para confirmar, usa: <code>/reset_stats confirm</code>",
                parse_mode="HTML"
            )
            return

        try:
            from core.db_manager import db_manager
            from utils.library_db import get_session
            from models.library_models import LocalBook

            # 1. Clear Download History (zeepub.db)
            async with db_manager.connection() as conn:
                await conn.execute("DELETE FROM download_history")
                await conn.commit()

            # 2. Clear Ratings (library.db)
            session = get_session()
            try:
                # Actualizar todos los libros a 0
                session.query(LocalBook).update({
                    "rating_average": 0,
                    "rating_count": 0
                })
                # También borrar la tabla de valoraciones si existe (asumiendo BookRating model)
                try:
                    from models.library_models import BookRating
                    session.query(BookRating).delete()
                except ImportError:
                    pass
                
                session.commit()
            finally:
                session.close()

            await update.message.reply_text("✅ <b>Contadores y valoraciones reiniciados exitosamente.</b>", parse_mode="HTML")
            logger.info(f"Admin {uid} reinició contadores y valoraciones globalmente.")
        except Exception as e:
            logger.error(f"Error en reset_stats: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error al reiniciar: {str(e)}")

    async def reset_library(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando: /reset_library
        Resetea completamente la base de datos local de la biblioteca.
        Solo para admin. Requiere confirmación.
        """
        user_id = update.effective_user.id
        tid = get_thread_id(update)

        # Verificar que el usuario sea admin
        if user_id not in config.ADMIN_IDS:
            await update.message.reply_text(
                "❌ <b>Acceso Denegado</b>\n\n"
                "Este comando solo está disponible para administradores.",
                parse_mode="HTML",
                message_thread_id=tid
            )
            return

        # Verificar si hay argumento de confirmación
        if not context.args or context.args[0].upper() != "CONFIRMAR":
            await update.message.reply_text(
                "⚠️ <b>ADVERTENCIA: Reset de Base de Datos Local</b>\n\n"
                "Este comando eliminará:\n"
                "• Toda la base de datos local (<code>library.db</code>)\n"
                "• Todas las portadas generadas\n"
                "• Todos los thumbnails móviles\n"
                "• Todas las fuentes de biblioteca configuradas\n\n"
                "Necesitarás volver a escanear tu biblioteca después de esto.\n\n"
                "⚠️ <b>Para confirmar, ejecuta:</b>\n"
                "<code>/reset_library CONFIRMAR</code>",
                parse_mode="HTML",
                message_thread_id=tid
            )
            return

        msg = await update.message.reply_text(
            "🔄 <b>Reseteando base de datos local...</b>",
            parse_mode="HTML",
            message_thread_id=tid
        )

        try:
            from utils.library_db import DB_PATH, COVERS_DIR
            
            items_deleted = []
            
            # 1. Eliminar base de datos
            if os.path.exists(DB_PATH):
                try:
                    os.remove(DB_PATH)
                    items_deleted.append("✅ Base de datos eliminada")
                except Exception as e:
                    logger.error(f"Error eliminando DB: {e}")
                    await msg.edit_text(
                        f"❌ <b>Error eliminando base de datos:</b>\n<code>{e}</code>",
                        parse_mode="HTML"
                    )
                    return
            else:
                items_deleted.append("ℹ️ Base de datos no existía")
            
            # 2. Eliminar directorio de portadas
            cover_count = 0
            if os.path.exists(COVERS_DIR):
                try:
                    # Contar archivos
                    cover_count = len([f for f in os.listdir(COVERS_DIR) if os.path.isfile(os.path.join(COVERS_DIR, f))])
                    
                    shutil.rmtree(COVERS_DIR)
                    items_deleted.append(f"✅ {cover_count} portadas eliminadas")
                except Exception as e:
                    logger.error(f"Error eliminando portadas: {e}")
                    items_deleted.append(f"⚠️ Error eliminando portadas: {e}")
            else:
                items_deleted.append("ℹ️ Directorio de portadas no existía")
            
            # 3. Recrear directorio de portadas vacío
            try:
                os.makedirs(COVERS_DIR, exist_ok=True)
                items_deleted.append("✅ Directorio de portadas recreado")
            except Exception as e:
                logger.error(f"Error recreando directorio: {e}")
                items_deleted.append(f"⚠️ Error recreando directorio: {e}")
            
            # Mensaje de éxito
            summary = "\n".join(items_deleted)
            await msg.edit_text(
                f"✨ <b>Base de Datos Local Reseteada</b>\n\n"
                f"<b>Resumen:</b>\n{summary}\n\n"
                f"📝 <b>Próximo paso:</b>\n"
                f"Ejecuta <code>/scan_library</code> para reindexar tus libros.",
                parse_mode="HTML"
            )
            
            logger.info(f"Admin {user_id} reseted library database. {cover_count} covers deleted.")
            
        except Exception as e:
            logger.error(f"Error en reset_library: {e}")
            await msg.edit_text(
                f"❌ <b>Error durante el reset:</b>\n<code>{e}</code>",
                parse_mode="HTML"
            )
