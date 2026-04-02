# plugins/stars_payment_plugin.py

import logging

from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes, MessageHandler, PreCheckoutQueryHandler, filters

from plugins.base_plugin import BasePlugin
from repositories.user_repository import user_repo
from services.user_service import invalidate_user_cache

logger = logging.getLogger(__name__)


class StarsPaymentPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "stars_payment"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Gestión de pagos con Telegram Stars"

    async def initialize(self, bot_instance) -> bool:
        self.bot = bot_instance.bot
        self.cms = bot_instance.plugin_manager.get_plugin("custom_messages")

        # Registrar handlers de pago
        bot_instance.add_handler(PreCheckoutQueryHandler(self.pre_checkout_handler))
        bot_instance.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.successful_payment_handler))

        logger.info("StarsPaymentPlugin inicializado y handlers registrados.")
        return True

    async def cleanup(self) -> None:
        pass

    async def pre_checkout_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Responde a la consulta previa al pago."""
        query = update.pre_checkout_query
        # Aquí podrías validar disponibilidad del nivel, etc.
        # Por ahora aceptamos todos
        await query.answer(ok=True)

    async def successful_payment_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el pago exitoso y actualiza el nivel del usuario."""
        payment = update.message.successful_payment
        user = update.effective_user

        # El payload contiene el nivel solicitado
        payload = payment.invoice_payload
        # Ejemplo payload: "upgrade_vip" o "upgrade_premium"

        new_role = "free"
        if "premium" in payload.lower():
            new_role = "premium"
        elif "vip" in payload.lower():
            new_role = "vip"
        elif "patrocinador" in payload.lower():
            new_role = "patrocinador"

        # Actualizar en la DB
        await user_repo.upsert(telegram_id=user.id, role=new_role, nickname=user.first_name)

        # Limpiar caché del servicio de usuario
        await invalidate_user_cache(user.id)

        # Enviar mensaje de éxito usando el sistema de plantillas
        if self.cms:
            text = await self.cms.get_text("star_payment_success", user=user, Nivel=new_role.capitalize())
        else:
            text = f"🌟 ¡Gracias {user.first_name}! Ahora eres nivel {new_role.capitalize()}."

        await context.bot.send_message(chat_id=user.id, text=text, parse_mode="HTML")

        logger.info(f"Usuario {user.id} mejorado a {new_role} vía Stars.")

    async def create_stars_invoice_link(self, title: str, description: str, payload: str, amount: int) -> str:
        """Genera un enlace de factura para Telegram Stars."""
        # "XTR" es el código de moneda para Telegram Stars
        prices = [LabeledPrice("Estrellas", amount)]

        # createInvoiceLink es el método para generar el enlace que se usa en la Mini App
        link = await self.bot.create_invoice_link(
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # Vacío para Stars
            currency="XTR",
            prices=prices,
        )
        return link
