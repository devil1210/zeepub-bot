import asyncio
import logging
import os

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from config.config_settings import config
from plugins.base_plugin import BasePlugin
from utils.helpers import get_thread_id
from utils.url_cache import (
    delete_url_mapping,
    get_broken_links,
    get_recent_links,
    get_stats,
    validate_and_update_url,
)

logger = logging.getLogger(__name__)


class LinksManagerPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "links_manager"

    @property
    def version(self) -> str:
        return "1.1.0"

    @property
    def description(self) -> str:
        return "Gestión, validación y limpieza de links acortados (PostgreSQL)."

    async def initialize(self, bot_instance) -> bool:
        self.enabled = os.getenv("ENABLE_LINKS_MANAGER", "True").lower() == "true"

        if not self.enabled:
            logger.info("Plugin LinksManager desactivado por configuración.")
            return False

        try:
            app = bot_instance
            app.add_handler(CommandHandler("status_links", self.status_links))
            app.add_handler(CommandHandler("link_list", self.link_list))
            app.add_handler(CommandHandler("purge_link", self.purge_link))

            logger.info("Plugin LinksManager: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin LinksManager: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    async def status_links(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra estado de los links acortados (solo publishers)."""
        uid = update.effective_user.id

        # Verificar permisos (solo publishers)
        if uid not in config.FACEBOOK_PUBLISHERS:
            await update.message.reply_text("⛔ No tienes permisos para usar este comando.")
            return

        thread_id = get_thread_id(update)

        # Enviar mensaje de "procesando"
        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🔄 Obteniendo estadísticas...",
            message_thread_id=thread_id,
        )

        try:
            # Validar solo 5 links recientes
            recent_links = get_recent_links(limit=5)

            # Validar con timeout de 10 segundos total
            if recent_links:
                try:
                    tasks = [validate_and_update_url(item[0], item[1]) for item in recent_links]
                    await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning("Timeout validating links in status_links")

            # Actualizar estadísticas después de la validación
            stats = get_stats()
            broken = get_broken_links(limit=5)

            # Construir reporte
            success_rate = (stats["valid"] / stats["total"] * 100) if stats["total"] > 0 else 0

            report = "🔍 <b>Estado de Links Acortados</b>\n\n"
            report += "📊 <b>Estadísticas:</b>\n"
            report += f"  • Total: {stats['total']} links\n"
            report += f"  ✅ Válidos: {stats['valid']}\n"
            report += f"  ❌ Rotos: {stats['broken']}\n"
            report += f"  ⚠️ En riesgo: {stats['at_risk']} (2 fallos)\n"
            report += f"  📈 Tasa de éxito: {success_rate:.1f}%\n"

            if broken:
                report += "\n⚠️ <b>Links Rotos (máximo 5):</b>\n"
                for hash_val, title, failed, _last_checked, created_at in broken:
                    title_short = (title[:40] + "...") if title and len(title) > 40 else (title or "Sin título")

                    created_date = created_at or "Desconocida"

                    report += f"  • {title_short}\n"
                    report += f"    Hash: <code>{hash_val}</code>\n"
                    report += f"    Creado: {created_date}\n"
                    report += f"    Fallos: {failed}/3\n"

            report += (
                "\n📄 <i>Nota: Se validaron los últimos 5 links. Para revisar todos usa el validador automático.</i>"
            )

            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=report,
                parse_mode="HTML",
            )

        except Exception as e:
            logger.error(f"Error en status_links: {e}", exc_info=True)
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=f"❌ Error al obtener estado de links: {str(e)}",
            )

    async def link_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra listado de links acortados recientes (solo publishers)."""
        uid = update.effective_user.id

        # Verificar permisos (solo publishers)
        if uid not in config.FACEBOOK_PUBLISHERS:
            await update.message.reply_text("⛔ No tienes permisos para usar este comando.")
            return

        thread_id = get_thread_id(update)

        # Determinar límite
        limit = 10  # default
        if context.args:
            try:
                limit = int(context.args[0])
                limit = min(max(limit, 1), 50)  # Entre 1 y 50
            except ValueError:
                await update.message.reply_text("❌ El límite debe ser un número. Uso: /link_list [número]")
                return

        try:
            recent_links = get_recent_links(limit=limit)

            if not recent_links:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="ℹ️ No hay links en la caché.",
                    message_thread_id=thread_id,
                )
                return

            # Construir mensaje
            report = f"📋 <b>Links Acortados Recientes</b> (últimos {len(recent_links)})\n\n"

            for i, (hash_val, _url, book_title, created_at) in enumerate(recent_links, 1):
                title_display = (
                    (book_title[:45] + "...") if book_title and len(book_title) > 45 else (book_title or "Sin título")
                )

                # Construir link acortado
                dl_domain = config.DL_DOMAIN.rstrip("/")
                if not dl_domain.startswith("http"):
                    dl_domain = f"https://{dl_domain}"
                short_link = f"{dl_domain}/api/dl/{hash_val}"

                report += f"{i}. <b>{title_display}</b>\n"
                report += f"   Hash: <code>{hash_val}</code>\n"
                report += f"   Link: {short_link}\n"
                report += f"   Creado: {created_at or 'Desconocido'}\n\n"

            report += "<i>💡 Usa /purge_link &lt;hash&gt; para eliminar un link específico.</i>"

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=report,
                parse_mode="HTML",
                message_thread_id=thread_id,
            )

        except Exception as e:
            logger.error(f"Error en link_list: {e}", exc_info=True)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ Error al obtener listado de links: {str(e)}",
                message_thread_id=thread_id,
            )

    async def purge_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Elimina un link acortado de la caché (solo publishers)."""
        uid = update.effective_user.id

        # Verificar que sea publisher
        if uid not in config.FACEBOOK_PUBLISHERS:
            await update.message.reply_text("⛔ No tienes permisos para usar este comando.")
            return

        # Verificar argumentos
        if not context.args or len(context.args) != 1:
            await update.message.reply_text("❌ Uso incorrecto.\nUso: /purge_link <hash>\nEjemplo: /purge_link abcdefg")
            return

        hash_to_purge = context.args[0]

        try:
            success = delete_url_mapping(hash_to_purge)

            if success:
                await update.message.reply_text(
                    f"✅ Link con hash <code>{hash_to_purge}</code> eliminado de la caché.",
                    parse_mode="HTML",
                )
                logger.info(f"Admin {uid} eliminó link {hash_to_purge} de la caché (PostgreSQL).")
            else:
                await update.message.reply_text(
                    f"ℹ️ No se encontró ningún link con hash <code>{hash_to_purge}</code> en la caché.",
                    parse_mode="HTML",
                )

        except Exception as e:
            logger.error(f"Error en purge_link para hash {hash_to_purge}: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error al intentar eliminar el link: {str(e)}")
