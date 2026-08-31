import asyncio
import logging

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from config.config_settings import config
from plugins.base_plugin import BasePlugin
from services.help_service import HelpService
from services.settings_service import get_setting, set_setting
from services.user_service import get_effective_user
from utils.command_registry import COMMANDS_REGISTRY
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


class HelpPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "help"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "Menú de ayuda interactivo y gestión de comandos del bot."

    def __init__(self):
        self.help_service = HelpService()

    async def initialize(self, bot_instance) -> bool:
        app = bot_instance

        # --- Public Help Command ---
        app.add_handler(CommandHandler(["help", "ayuda"], self.show_help))

        # --- Callbacks ---
        app.add_handler(CallbackQueryHandler(self.handle_help_callbacks, pattern=r"^help_"))

        # Register commands in Telegram menu (async/background)
        asyncio.create_task(self.update_bot_commands(app.bot))

        return True

    async def cleanup(self) -> None:
        pass

    async def _is_bot_admin(self, user_id: int) -> bool:
        if user_id in config.ADMIN_USERS:
            return True
        user = await get_effective_user(user_id)
        return user and user.get("role") == "admin"

    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú de ayuda con Rich Blocks y Glass UI."""
        user = await get_effective_user(update.effective_user.id)
        role = user.get("role", "user") if user else "user"
        is_staff = role in ("admin", "staff") or update.effective_user.id in config.ADMIN_USERS
        thread_id = get_thread_id(update)

        from services.library_ui import build_help_rich_blocks
        from services.rich_message_service import RichMessageService

        blocks = build_help_rich_blocks(
            user_rank=role.capitalize(),
            is_staff=is_staff,
        )

        res = await RichMessageService.send_rich_message(
            chat_id=update.effective_chat.id,
            blocks=blocks,
            message_thread_id=thread_id,
        )

        if not res or not res.get("ok"):
            text = self.help_service.build_main_help_text()
            keyboard = self.help_service.get_main_help_keyboard(role)
            if update.callback_query:
                await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await update.message.reply_text(
                    text=text, reply_markup=keyboard, parse_mode="HTML", message_thread_id=thread_id
                )

    async def handle_help_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa las interacciones con el menú de ayuda."""
        query = update.callback_query
        await query.answer()

        data = query.data.split(":")
        action = data[0]

        user = await get_effective_user(update.effective_user.id)
        role = user.get("role", "user") if user else "user"

        if action == "help_main":
            text = self.help_service.build_main_help_text()
            keyboard = self.help_service.get_main_help_keyboard(role)
        elif action == "help_cat":
            cat_key = data[1]
            text = self.help_service.build_category_help_text(cat_key)
            keyboard = self.help_service.get_category_keyboard(cat_key, role)
        elif action == "help_cmd":
            cmd_name = data[1]
            text = self.help_service.build_command_detail_text(cmd_name)
            keyboard = self.help_service.get_command_detail_keyboard(cmd_name)
        else:
            return

        try:
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Error updating help menu: {e}")

    # --- Telegram Bot Menu (/) Registration ---

    async def update_bot_commands(self, bot):
        """Registra los comandos en el menú nativo de Telegram (/)."""
        await asyncio.sleep(5)  # Wait for stabilization

        from telegram import (
            BotCommand,
            BotCommandScopeAllChatAdministrators,
            BotCommandScopeAllGroupChats,
            BotCommandScopeAllPrivateChats,
            BotCommandScopeChat,
            BotCommandScopeDefault,
        )

        try:
            cms = None
            try:
                from plugins.plugin_manager import manager

                cms = manager.get_plugin("custom_messages")
            except Exception:
                pass

            # 1. Public Commands
            public_cmds = [
                BotCommand("start", "🏠 Iniciar bot y menú principal"),
                BotCommand("buscar", "🔍 Buscar novelas por título o autor"),
                BotCommand("catalogo", "📚 Explorar catálogo completo"),
                BotCommand("series", "📖 Explorar catálogo por series"),
                BotCommand("status", "👤 Ver perfil y descargas restantes"),
                BotCommand("donar", "⭐ Información de membresías VIP"),
                BotCommand("ayuda", "ℹ️ Guía de uso y comandos"),
                BotCommand("cancel", "❌ Cancelar acción activa"),
            ]

            await bot.set_my_commands(public_cmds, scope=BotCommandScopeDefault())
            await bot.set_my_commands(public_cmds, scope=BotCommandScopeAllPrivateChats())
            await bot.set_my_commands(public_cmds, scope=BotCommandScopeAllGroupChats())
            await bot.set_my_commands(public_cmds, scope=BotCommandScopeAllChatAdministrators())

            # 2. Curated Menu for Admins / Staff
            admin_cmds = list(public_cmds) + [
                BotCommand("stats", "📊 Estadísticas globales del sistema"),
                BotCommand("id", "🆔 Ver ID de usuario, chat y tema actual"),
                BotCommand("upload_epub", "📤 Subir libro a la biblioteca"),
                BotCommand("broadcast", "📢 Enviar mensaje global a usuarios"),
            ]

            for admin_id in getattr(config, "ADMIN_USERS", []):
                try:
                    await bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=admin_id))
                    await asyncio.sleep(0.2)
                except Exception:
                    pass

            logger.info("Menus de comandos actualizados en Telegram.")
        except Exception as e:
            logger.error(f"Error actualizando menú de comandos en Telegram: {e}")

    # --- Admin Command Handlers ---

    async def add_menu_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._is_bot_admin(update.effective_user.id):
            return
        cmd = context.args[0].lower().replace("/", "") if context.args else None
        if not cmd or cmd not in COMMANDS_REGISTRY:
            await update.message.reply_text("❌ Comando inexistente o no especificado.")
            return

        current = get_setting("menu_public_commands", "")
        cmds = [c.strip() for c in current.split(",") if c.strip()]
        if cmd in cmds:
            await update.message.reply_text(f"ℹ️ /<code>{cmd}</code> ya está en el menú.")
            return

        cmds.append(cmd)
        set_setting("menu_public_commands", ",".join(cmds))
        await update.message.reply_text(f"✅ /<code>{cmd}</code> añadido.")
        await self.update_bot_commands(context.bot)

    async def del_menu_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._is_bot_admin(update.effective_user.id):
            return
        cmd = context.args[0].lower().replace("/", "") if context.args else None

        current = get_setting("menu_public_commands", "")
        cmds = [c.strip() for c in current.split(",") if c.strip()]
        if cmd not in cmds:
            await update.message.reply_text(f"❌ /<code>{cmd}</code> no está en el menú.")
            return

        cmds.remove(cmd)
        set_setting("menu_public_commands", ",".join(cmds))
        await update.message.reply_text(f"✅ /<code>{cmd}</code> eliminado.")
        await self.update_bot_commands(context.bot)

    async def list_menu_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._is_bot_admin(update.effective_user.id):
            return
        current = get_setting("menu_public_commands", "")
        cmds = [c.strip() for c in current.split(",") if c.strip()] if current else ["start", "help", "menu", "..."]
        text = "📋 <b>Menú Público Actual:</b>\n\n" + "\n".join([f"• /<code>{c}</code>" for c in cmds])
        await update.message.reply_text(text, parse_mode="HTML")

    async def move_menu_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._is_bot_admin(update.effective_user.id) or len(context.args) < 2:
            return
        cmd = context.args[0].lower().replace("/", "")
        try:
            pos = int(context.args[1]) - 1
        except (ValueError, IndexError):
            return

        current = get_setting("menu_public_commands", "")
        cmds = [c.strip() for c in current.split(",") if c.strip()]
        if cmd not in cmds or pos < 0 or pos >= len(cmds):
            await update.message.reply_text("❌ Comando no encontrado o posición inválida.")
            return

        cmds.remove(cmd)
        cmds.insert(pos, cmd)
        set_setting("menu_public_commands", ",".join(cmds))
        await update.message.reply_text(f"✅ /<code>{cmd}</code> movido.")
        await self.update_bot_commands(context.bot)

    async def refresh_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._is_bot_admin(update.effective_user.id):
            return
        await self.update_bot_commands(context.bot)
        await update.message.reply_text("🔄 Menú refrescado.")

    async def set_bot_avatar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._is_bot_admin(update.effective_user.id):
            return
        url = None
        if update.message.reply_to_message and update.message.reply_to_message.photo:
            file = await context.bot.get_file(update.message.reply_to_message.photo[-1].file_id)
            url = file.file_path
        elif context.args:
            url = context.args[0]

        if url:
            set_setting("bot_avatar", url)
            await update.message.reply_text(f"✅ Avatar actualizado: {url}")
        else:
            await update.message.reply_text("❌ Proporciona una URL o responde a una foto.")
