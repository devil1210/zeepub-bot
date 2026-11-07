import logging
import os

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from config.config_settings import config
from plugins.base_plugin import BasePlugin
from services.library_ui import build_donations_rich_blocks
from services.rich_message_service import RichMessageService
from services.settings_service import get_setting
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


class DonationsPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "donations"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "Sistema de donaciones, membresías VIP/Premium y beneficios."

    def __init__(self):
        super().__init__()
        self.enabled = False

    async def initialize(self, bot_instance) -> bool:
        self.enabled = os.getenv("ENABLE_DONATIONS", "True").lower() == "true"

        if not self.enabled:
            logger.info("Plugin Donations desactivado por configuración.")
            return False

        try:
            app = bot_instance
            app.add_handler(CommandHandler(["donar", "donate", "niveles", "levels"], self.donate))
            app.add_handler(CommandHandler(["verificar_donacion", "reclamar_donacion"], self.claim_donation))
            app.add_handler(CommandHandler(["link_donacion", "vincular_donacion"], self.admin_link_donation))
            logger.info("Plugin Donations: Handlers registrados.")
            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error registrando handlers del plugin Donations: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    async def donate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /donar y /niveles: envía ficha interactiva con beneficios y enlaces de donación."""
        thread_id = get_thread_id(update)
        user_name = update.effective_user.first_name or "Lector"
        uid = update.effective_user.id

        p_white = get_setting("price_whitelist", "5")
        p_vip = get_setting("price_vip", "10")
        p_premium = get_setting("price_premium", "20")
        months = get_setting("benefit_duration_months", "6")

        donation_url = getattr(config, "DONATION_URL", "https://ko-fi.com/zeepubs")

        blocks = build_donations_rich_blocks(
            user_name=user_name,
            donation_url=donation_url,
            p_white=p_white,
            p_vip=p_vip,
            p_premium=p_premium,
            duration_months=months,
        )

        rich_kwargs = {}
        es_grupo = update.effective_chat and update.effective_chat.type in ("group", "supergroup")
        if es_grupo:
            rich_kwargs["receiver_user_id"] = uid

        res = await RichMessageService.send_rich_message(
            chat_id=update.effective_chat.id,
            blocks=blocks,
            message_thread_id=thread_id,
            **rich_kwargs,
        )

        if not res or not res.get("ok"):
            fallback_text = (
                f"☕ <b>Membresías y Donaciones • ZeePubs</b>\n\n"
                f"Hola <b>{user_name}</b>, gracias por apoyar nuestro proyecto.\n\n"
                f"• 🤍 <b>Whitelist (${p_white} USD):</b> 10 descargas/día\n"
                f"• ⭐ <b>VIP (${p_vip} USD):</b> Descargas Ilimitadas\n"
                f"• 💎 <b>Premium (${p_premium} USD):</b> Ilimitadas + Prioridad\n\n"
                f"👉 <a href='{donation_url}'>Donar en Ko-fi</a>"
            )
            api_kwargs = {"receiver_user_id": uid} if es_grupo else None
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=fallback_text,
                parse_mode="HTML",
                message_thread_id=thread_id,
                api_kwargs=api_kwargs,
            )

    async def claim_donation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Permite a un usuario vincular una donación de Ko-fi no reclamada ingresando su correo o ID de transacción.
        Uso: /verificar_donacion <correo o kofi_transaction_id>
        """
        user = update.effective_user
        if not user:
            return

        thread_id = get_thread_id(update)
        args = context.args or []
        if not args:
            await update.message.reply_text(
                "ℹ️ <b>¿Cómo verificar tu donación de Ko-fi?</b>\n\n"
                "Si realizaste una donación sin indicar tu ID de Telegram en el mensaje, puedes reclamarla con:\n\n"
                "<code>/verificar_donacion tu_correo@ejemplo.com</code>\n"
                "o con el ID de transacción:\n"
                "<code>/verificar_donacion 00000000-1111-2222-3333-444444444444</code>",
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
            return

        query = " ".join(args).strip()
        from repositories.donation_repository import donation_repo
        from repositories.user_repository import user_repo
        from services.cache_service import cache_manager
        from services.kofi_service import kofi_service
        from services.tier_service import tier_service

        matches = await donation_repo.find_unlinked_by_query(query)
        if not matches:
            await update.message.reply_text(
                f"❌ No se encontró ninguna donación pendiente de vincular para: <code>{query}</code>.\n\n"
                "Verifica que hayas escrito exactamente el correo o ID de transacción usado en Ko-fi.",
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
            return

        # Tomar la donación no vinculada más reciente
        donation = matches[0]
        tier, days = await kofi_service._determine_tier_and_duration(
            amount=float(donation.amount or 0.0),
            tier_name=donation.tier_name,
            is_subscription=donation.is_subscription,
        )

        # Actualizar usuario
        await user_repo.update_user_level(user.id, tier, days=days)
        await cache_manager.delete_user(user.id)
        await tier_service.invalidate_caches()

        # Marcar donación como procesada y asociada
        await donation_repo.update_transaction(
            donation.message_id,
            {
                "status": "processed",
                "telegram_id": user.id,
                "user_display_name": user.first_name or user.username or f"User_{user.id}",
                "tier_granted": tier,
                "duration_days": days,
            },
        )

        await update.message.reply_text(
            f"🎉 <b>¡Donación verificada con éxito!</b>\n\n"
            f"• <b>Monto:</b> {donation.amount} {donation.currency}\n"
            f"• <b>Nivel activado:</b> ⭐ <b>{tier.upper()}</b>\n"
            f"• <b>Duración:</b> {days} días\n\n"
            f"¡Muchas gracias por apoyar a ZeePub!",
            parse_mode="HTML",
            message_thread_id=thread_id,
        )

    async def admin_link_donation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando de administración para vincular manualmente una donación de Ko-fi a cualquier usuario.
        Uso: /link_donacion <transaction_id_o_message_id> <telegram_id> [tier]
        """
        user = update.effective_user
        if not user or (user.id not in config.ADMIN_USERS and user.id != config.SUPER_ADMIN_ID):
            return

        thread_id = get_thread_id(update)
        args = context.args or []
        if len(args) < 2:
            await update.message.reply_text(
                "Uso de administrador:\n<code>/link_donacion &lt;tx_id_o_msg_id&gt; &lt;telegram_id&gt; [tier]</code>",
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
            return

        tx_query = args[0].strip()
        try:
            target_tg_id = int(args[1].strip())
        except ValueError:
            await update.message.reply_text("❌ El telegram_id debe ser un número entero.")
            return

        custom_tier = args[2].strip().lower() if len(args) >= 3 else None

        from repositories.donation_repository import donation_repo
        from repositories.user_repository import user_repo
        from services.cache_service import cache_manager
        from services.kofi_service import kofi_service
        from services.tier_service import tier_service

        tx = await donation_repo.get_by_message_id(tx_query)
        if not tx:
            tx = await donation_repo.get_by_transaction_id(tx_query)
        if not tx:
            unlinked = await donation_repo.find_unlinked_by_query(tx_query)
            if unlinked:
                tx = unlinked[0]

        if not tx:
            await update.message.reply_text(f"❌ Transacción no encontrada para: {tx_query}")
            return

        tier = custom_tier
        if not tier:
            tier, days = await kofi_service._determine_tier_and_duration(
                amount=float(tx.amount or 0.0),
                tier_name=tx.tier_name,
                is_subscription=tx.is_subscription,
            )
        else:
            days = 30 if tx.is_subscription else 180

        await user_repo.update_user_level(target_tg_id, tier, days=days)
        await cache_manager.delete_user(target_tg_id)
        await tier_service.invalidate_caches()

        await donation_repo.update_transaction(
            tx.message_id,
            {
                "status": "processed",
                "telegram_id": target_tg_id,
                "tier_granted": tier,
                "duration_days": days,
            },
        )

        await update.message.reply_text(
            f"✅ Transacción <code>{tx.message_id}</code> vinculada exitosamente al usuario <code>{target_tg_id}</code>.\n"
            f"Nivel: ⭐ <b>{tier.upper()}</b> ({days} días).",
            parse_mode="HTML",
            message_thread_id=thread_id,
        )


