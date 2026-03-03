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

        # --- Public Commands ---
        app.add_handler(CommandHandler(["help", "ayuda"], self.show_help))
        app.add_handler(CommandHandler(["menu", "inicio"], self.show_help))

        # --- Admin/Menu Management ---
        app.add_handler(CommandHandler("add_menu_cmd", self.add_menu_cmd))
        app.add_handler(CommandHandler("del_menu_cmd", self.del_menu_cmd))
        app.add_handler(CommandHandler("list_menu_cmd", self.list_menu_cmd))
        app.add_handler(CommandHandler("move_menu_cmd", self.move_menu_cmd))
        app.add_handler(CommandHandler("refresh_menu", self.refresh_menu))
        app.add_handler(CommandHandler("set_bot_avatar", self.set_bot_avatar))

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
        """Muestra el menú de ayuda principal."""
        user = await get_effective_user(update.effective_user.id)
        role = user.get("role", "user") if user else "user"
        thread_id = get_thread_id(update)

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
            raw_cmds = get_setting("menu_public_commands")
            if raw_cmds:
                cmd_list = [c.strip() for c in raw_cmds.split(",") if c.strip()]
                public_cmds = []
                for c_name in cmd_list:
                    fallback_desc = COMMANDS_REGISTRY.get(c_name, {}).get("desc", "Comando bot")
                    desc = fallback_desc
                    if cms and cms.enabled:
                        desc = await cms.get_text(f"cmd_menu_desc_{c_name}", default_text=fallback_desc)
                    public_cmds.append(BotCommand(c_name, desc))
            else:
                public_cmds = await self._get_default_public_cmds_dynamic(cms)

            await bot.set_my_commands(public_cmds, scope=BotCommandScopeDefault())
            await bot.set_my_commands(public_cmds, scope=BotCommandScopeAllPrivateChats())
            await bot.set_my_commands(public_cmds, scope=BotCommandScopeAllGroupChats())
            await bot.set_my_commands(public_cmds, scope=BotCommandScopeAllChatAdministrators())

            # 2. Complete Menu for Admins
            admin_cmds = []
            for cmd_name in sorted(COMMANDS_REGISTRY.keys()):
                if len(admin_cmds) >= 95:
                    break

                # Exclude specific non-interactive or internal commands if needed
                fallback_desc = COMMANDS_REGISTRY[cmd_name]["desc"]
                desc = fallback_desc
                if cms and cms.enabled:
                    desc = await cms.get_text(f"cmd_menu_desc_{cmd_name}", default_text=fallback_desc)
                admin_cmds.append(BotCommand(cmd_name, desc))

            for admin_id in config.ADMIN_USERS:
                try:
                    await bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=admin_id))
                    await asyncio.sleep(0.5)
                except Exception:
                    pass

            logger.info("Menus de comandos actualizados en Telegram.")
        except Exception as e:
            logger.error(f"Error actualizando menú de comandos en Telegram: {e}")

    async def _get_default_public_cmds_dynamic(self, cms=None):
        from telegram import BotCommand

        defaults = ["start", "help", "menu", "search", "donar", "niveles", "status", "cancel"]
        cmds = []
        for c_name in defaults:
            fallback = COMMANDS_REGISTRY.get(c_name, {}).get("desc", "Comando")
            desc = fallback
            if cms and cms.enabled:
                desc = await cms.get_text(f"cmd_menu_desc_{c_name}", default_text=fallback)
            cmds.append(BotCommand(c_name, desc))
        return cmds

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
        except:
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
