# plugins/verification_plugin.py

import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from plugins.base_plugin import BasePlugin
from config.config_settings import config

logger = logging.getLogger(__name__)


class VerificationPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "verification"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Comando /verify para verificación de usuarios (API 9.3)"

    async def initialize(self, bot_instance) -> bool:
        # Registrar comando /verify
        bot_instance.add_handler(CommandHandler("verify", self.verify_command))
        logger.info("VerificationPlugin inicializado.")
        return True

    async def cleanup(self) -> None:
        pass

    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /verify <user_id> [true|false]"""
        user_id = update.effective_user.id

        # Solo admisn
        if user_id not in config.ADMIN_USERS:
            return

        args = context.args
        if not args:
            await update.message.reply_text("Uso: /verify <user_id> [true|false]")
            return

        try:
            target_id = int(args[0])
            verify = True
            if len(args) > 1:
                verify = args[1].lower() == "true"

            # API 9.3: verifyUser (nuevo método)
            # Como PTB podría no tenerlo aún, usamos raw request
            payload = {
                "user_id": target_id,
                "is_verified": verify
            }

            # Intentamos usar el método si existe o raw
            try:
                if hasattr(context.bot, "verify_user"):
                    await context.bot.verify_user(user_id=target_id, is_verified=verify)
                else:
                    await context.bot.do_api_request("verifyUser", payload)

                status = "verificado" if verify else "desverificado"
                await update.message.reply_text(f"✅ Usuario {target_id} {status} correctamente.")
            except Exception as e:
                await update.message.reply_text(f"❌ Error al verificar usuario: {e}")

        except ValueError:
            await update.message.reply_text("ID de usuario inválido.")
