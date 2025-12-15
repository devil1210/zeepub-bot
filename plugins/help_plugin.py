import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from plugins.base_plugin import BasePlugin
from config.config_settings import config
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


class HelpPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "help_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Comando de ayuda y navegación interactiva."

    def __init__(self):
        self.enabled = False

    async def initialize(self, bot_instance) -> bool:
        self.enabled = config.ENABLE_HELP_PLUGIN

        if not self.enabled:
            logger.info("Plugin Help desactivado por configuración.")
            return False

        try:
            app = bot_instance
            app.add_handler(CommandHandler("help", self.help))
            app.add_handler(
                CallbackQueryHandler(self.help_navigation_callback, pattern=r"^help\|")
            )

            logger.info("Plugin Help: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin Help: {e}")
            return False

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help: muestra ayuda dinámica y paginada."""
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        help_data, is_admin, is_publisher = self._get_help_data(uid)

        # Mostrar categoría "home" por defecto
        cat_title, commands = help_data.get("home", ("Inicio", []))

        text = f"🤖 <b>Ayuda de ZeePub Bot</b>\n\n"
        text += f"📂 <b>Categoría: {cat_title}</b>\n\n"

        for cmd, desc in commands:
            safe_cmd = cmd.replace("<", "&lt;").replace(">", "&gt;")
            safe_desc = desc.replace("<", "&lt;").replace(">", "&gt;")
            text += f"<b>{safe_cmd}</b>\n   ╰ {safe_desc}\n"

        # Teclado dinámico
        keyboard = self._get_help_keyboard(is_admin, is_publisher)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
            message_thread_id=thread_id,
        )

    async def help_navigation_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Maneja la navegación del menú de ayuda."""
        query = update.callback_query
        uid = update.effective_user.id

        # Parse action from data: help|<action>|<arg>
        # Examples: help|nav|admin, help|back
        data = query.data.split("|")
        action = data[1] if len(data) > 1 else None

        help_data, is_admin, is_publisher = self._get_help_data(uid)

        if action == "nav":
            # Navegar a una categoría específica
            cat_key = data[2]
            cat_title, commands = help_data.get(cat_key, ("Categoría", []))

            text = f"🤖 <b>Ayuda de ZeePub Bot</b>\n\n"
            text += f"📂 <b>Categoría: {cat_title}</b>\n\n"

            for cmd, desc in commands:
                safe_cmd = cmd.replace("<", "&lt;").replace(">", "&gt;")
                safe_desc = desc.replace("<", "&lt;").replace(">", "&gt;")
                text += f"<b>{safe_cmd}</b>\n   ╰ {safe_desc}\n"

            # Back button to home
            keyboard = [
                [InlineKeyboardButton("🔙 Volver al Inicio", callback_data="help|back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text=text, parse_mode="HTML", reply_markup=reply_markup
            )
            await query.answer()

        elif action == "back":
            # Volver al inicio (Menú principal de ayuda)
            cat_title, commands = help_data.get("home", ("Inicio", []))

            text = f"🤖 <b>Ayuda de ZeePub Bot</b>\n\n"
            text += f"📂 <b>Categoría: {cat_title}</b>\n\n"

            for cmd, desc in commands:
                safe_cmd = cmd.replace("<", "&lt;").replace(">", "&gt;")
                safe_desc = desc.replace("<", "&lt;").replace(">", "&gt;")
                text += f"<b>{safe_cmd}</b>\n   ╰ {safe_desc}\n"

            reply_markup = self._get_help_keyboard(is_admin, is_publisher)

            await query.edit_message_text(
                text=text, parse_mode="HTML", reply_markup=reply_markup
            )
            await query.answer()

        else:
            await query.answer("Acción desconocida", show_alert=True)

    def _get_help_data(self, uid):
        is_admin = uid in config.ADMIN_USERS
        is_publisher = uid in config.FACEBOOK_PUBLISHERS

        # Staff check could be added if needed, leveraging config or db
        # For now relying on standard roles

        data = {}

        # 1. Home (Comandos básicos para todos)
        home_cmds = [
            ("/search <término>", "Buscar libros en la biblioteca."),
            ("/start", "Reiniciar el bot."),
            ("/status", "Ver tu estado y descargas."),
            ("/cancel", "Cancelar operación actual."),
        ]

        if config.ENABLE_GROUP_MANAGER:
            home_cmds.append(("/reglas", "Ver reglas del grupo."))

        data["home"] = ("Inicio", home_cmds)

        # 2. Admin commands
        if is_admin:
            admin_cmds = []
            if config.ENABLE_SYSTEM_MANAGER:
                admin_cmds.append(("/update_system [force]", "Actualizar bot."))
                admin_cmds.append(
                    ("/set_auto_delete_time <min>", "Configurar auto-borrado.")
                )
                admin_cmds.append(("/setlog [LEVEL]", "Cambiar nivel de logs."))

            if config.ENABLE_USER_MANAGER:
                admin_cmds.append(("/add_user <id> <rol>", "Agregar usuario."))
                admin_cmds.append(("/remove_user <id>", "Eliminar usuario."))
                admin_cmds.append(("/reset <id>", "Resetear descargas de usuario."))

            if config.ENABLE_STATS_PLUGIN:
                admin_cmds.append(("/stats", "Ver estadísticas."))

            if config.ENABLE_GROUP_MANAGER:
                admin_cmds.append(("/authorize_group", "Autorizar grupo."))

            admin_cmds.append(("/evil", "Entrar en modo Evil (Admin)."))
            data["admin"] = ("Administración", admin_cmds)

        # 3. Publisher/Staff commands (if applicable)
        # Assuming Publishers rely on /start flow mostly, but maybe evil

        return data, is_admin, is_publisher

    def _get_help_keyboard(self, is_admin: bool, is_publisher: bool):
        keyboard = []

        # Row 1: Admin (if admin)
        if is_admin:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🛠 Administración", callback_data="help|nav|admin"
                    )
                ]
            )

        # Possible Help links or Close button
        # keyboard.append([InlineKeyboardButton("❌ Cerrar", callback_data="close")]) # Using existing close handler?
        # Since this plugin manages its own callbacks, better to stick to help| prefix for navigation.
        # But 'close' is usually global.

        return InlineKeyboardMarkup(keyboard)
