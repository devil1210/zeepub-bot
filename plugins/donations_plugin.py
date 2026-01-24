import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes

from config.config_settings import config
from plugins.base_plugin import BasePlugin
from services.settings_service import get_setting, set_setting
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


class DonationsPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "donations"

    @property
    def version(self) -> str:
        return "1.1.1"

    @property
    def description(self) -> str:
        return "Sistema de donaciones, niveles de usuario y precios configurables."

    def __init__(self):
        self.custom_msg_engine = None
        self.CustomMsgSession = None
        self.enabled = False

    async def initialize(self, bot_instance) -> bool:
        self.enabled = os.getenv("ENABLE_DONATIONS", "True").lower() == "true"

        if not self.enabled:
            logger.info("Plugin Donations desactivado por configuración.")
            return False

        # Initialize Connection to CustomMessages DB
        self._init_custom_msg_db()

        try:
            app = bot_instance
            app.add_handler(CommandHandler("donar", self.donate))
            app.add_handler(CommandHandler("donate", self.donate))
            app.add_handler(CommandHandler("niveles", self.niveles))
            app.add_handler(CommandHandler("levels", self.niveles))
            app.add_handler(CommandHandler("set_price", self.set_price))

            logger.info("Plugin Donations: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin Donations: {e}")
            return False

    def _init_custom_msg_db(self):
        db_url = config.DATABASE_URL
        if not db_url:
            logger.warning("DATABASE_URL no configurada. DonationsPlugin no puede conectar a CustomMessages DB.")
            return

        try:
            # Reusing standard driver logic
            if "postgresql" in db_url or "postgres" in db_url:
                db_url = db_url.replace("postgres://", "postgresql://")
                db_url = db_url.replace("+asyncpg", "")
                if "+psycopg2" not in db_url:
                    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")

            self.custom_msg_engine = create_engine(db_url, future=True)
            self.CustomMsgSession = sessionmaker(bind=self.custom_msg_engine)
        except Exception as e:
            logger.warning(f"DonationsPlugin no pudo conectar a CustomMessages DB: {e}")

    async def cleanup(self) -> None:
        pass

    async def donate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /donar: envía link de donación."""
        thread_id = get_thread_id(update)
        user_name = update.effective_user.first_name

        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_text = (
            "☕ <b>Apóyanos en Ko-fi</b>\n\n"
            f"Hola {user_name}, gracias por considerar apoyarnos. "
            "Tu ayuda nos permite mantener activo tanto el <b>Bot</b> como el servidor <b>Kavita</b> "
            "y mejorarlos constantemente.\n\n"
            "📝 <b>Instrucciones:</b>\n"
            "1. Haz tu donación en Ko-fi.\n"
            "2. En el mensaje de la donación, puedes incluir un saludo.\n"
            "3. Vuelve aquí y presiona el botón de abajo para avisarnos.\n\n"
            f"👉 <a href='{config.DONATION_URL}'>Haz clic aquí para donar</a>"
        )

        text = base_text
        if cms and cms.enabled:
            # We pass donation_url as a variable just in case they want to use it
            text = await cms.get_text(
                "donate_message",
                user=update.effective_user,
                DonationUrl=config.DONATION_URL,
            )

        uid = update.effective_user.id
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Ya realicé la donación", callback_data=f"notificar_donacion|{uid}"
                )
            ],
            [InlineKeyboardButton("⏳ Donar más tarde", callback_data=f"cerrar_donacion|{uid}")],
        ]

        msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="HTML",
            message_thread_id=thread_id,
            disable_web_page_preview=False,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        # Programar auto-borrado en 2 minutos (120s)
        if context.job_queue:
            context.job_queue.run_once(
                self._delete_message_delayed,
                120,
                data={"chat_id": update.effective_chat.id, "message_id": msg.message_id},
                name=f"del_donate_cmd_{msg.message_id}"
            )

    async def _delete_message_delayed(self, context: ContextTypes.DEFAULT_TYPE):
        """Helper para borrar mensajes programados."""
        job = context.job
        data = job.data
        try:
            await context.bot.delete_message(chat_id=data["chat_id"], message_id=data["message_id"])
        except Exception as e:
            logger.debug(f"DonationPlugin: Auto-delete failed: {e}")

    async def niveles(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /niveles: explica niveles de usuario y beneficios."""
        thread_id = get_thread_id(update)

        # Obtener precios dinámicos (con defaults)
        p_white = get_setting("price_whitelist", "5")
        p_vip = get_setting("price_vip", "10")
        p_premium = get_setting("price_premium", "20")
        months = get_setting("benefit_duration_months", "6")

        cms = context.application.plugin_manager.get_plugin("custom_messages")

        # Fallback Hardcoded
        base_text = (
            "🌟 <b>Niveles de Usuario y Beneficios</b> 🌟\n\n"
            "Las donaciones nos ayudan a cubrir los costos del servidor. "
            f"Como agradecimiento, otorgamos beneficios por <b>{months} meses</b>.\n\n"
            "🔹 <b>Lector (Gratis)</b>\n"
            f"• {config.MAX_DOWNLOADS_PER_DAY} descargas diarias\n"
            "• Acceso a búsqueda básica\n\n"
            "🔹 <b>Patrocinador</b>\n"
            f"• Donación desde: <b>${p_white} USD</b>\n"
            f"• {config.WHITELIST_DOWNLOADS_PER_DAY} descargas diarias\n"
            "• Acceso prioritario\n\n"
            "🔹 <b>VIP</b>\n"
            f"• Donación desde: <b>${p_vip} USD</b>\n"
            f"• {config.VIP_DOWNLOADS_PER_DAY} descargas diarias\n"
            "• Soporte directo\n"
            "• 📱 Acceso a Mini App\n\n"
            "🔹 <b>Premium</b>\n"
            f"• Donación desde: <b>${p_premium} USD</b>\n"
            "• ♾️ <b>Descargas Ilimitadas</b>\n"
            "• 📱 Acceso a Mini App\n"
            "• Acceso a funciones exclusivas futuras\n\n"
            "💳 Usa /donar para obtener el link de Ko-fi.\n"
            "<i>(Los montos ayudan a mantener el proyecto vivo ❤️)</i>"
        )

        text = base_text
        if cms and cms.enabled:
            # We map the brackets style variables to the kwargs style used by get_text if possible,
            # OR we just pass them as kwargs and let get_text handle [Key] replacement.
            # get_text replaces [Key] with value.
            # Our variables here are: white, vip, premium, duration
            text = await cms.get_text(
                "levels_message",
                white=p_white,
                vip=p_vip,
                premium=p_premium,
                duration=months,
            )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )

    async def set_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Configura el precio de donación para un nivel (solo admins)."""
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            await update.message.reply_text("⛔ No tienes permisos.")
            return

        if not context.args or len(context.args) != 2:
            await update.message.reply_text(
                "❌ Uso: /set_price <nivel> <monto>\n"
                "Niveles: white, vip, premium, meses\n"
                "Ejemplo: /set_price vip 15"
            )
            return

        level = context.args[0].lower()
        amount = context.args[1]

        # Validar que amount sea número (o al menos string razonable)
        if not amount.isdigit() and not amount.replace(".", "", 1).isdigit():
            await update.message.reply_text("❌ El monto debe ser un número.")
            return

        key_map = {
            "white": "price_whitelist",
            "patrocinador": "price_whitelist",
            "vip": "price_vip",
            "premium": "price_premium",
            "meses": "benefit_duration_months",
            "duration": "benefit_duration_months",
        }

        if level not in key_map:
            await update.message.reply_text(
                "❌ Nivel inválido. Usa: white, vip, premium, meses"
            )
            return

        set_setting(key_map[level], amount)

        if level in ("meses", "duration"):
            msg_text = f"✅ Duración de beneficios actualizada a: <b>{amount} meses</b>"
        else:
            msg_text = (
                f"✅ Precio para <b>{level}</b> actualizado a: <b>${amount} USD</b>"
            )

        await update.message.reply_text(msg_text, parse_mode="HTML")
