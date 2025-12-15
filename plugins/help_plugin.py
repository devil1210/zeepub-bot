import logging
import os
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

    async def cleanup(self) -> None:
        pass

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

        # Parse action from data: help|<cat>
        try:
            _, target_cat = query.data.split("|", 1)
        except ValueError:
            target_cat = "home"

        # Handle 'close' if it was part of the legacy logic (though legacy usually had a separate close handler, 
        # checking the screenshot showing 'Cerrar' button which likely emits 'close' or similar. 
        # But wait, legacy code used 'help|...' or just top level?
        # The legacy _get_help_keyboard didn't seem to have a 'close' button in the snippet I read?
        # Wait, the screenshot SHOWS 'Cerrar'. 
        # Let me re-read the snippet in step 1730... 
        # It ends abruptly at "if os.getenv...". I missed reading the end of _get_help_keyboard!
        # I should assume there was a Close button. I will add one.

        if target_cat == "close":
            try:
                await query.message.delete()
            except Exception:
                await query.answer("No se pudo borrar", show_alert=True)
            return

        help_data, is_admin, is_publisher = self._get_help_data(uid)

        # Validar acceso a categorías restringidas
        if target_cat in ("admin", "plugins") and not is_admin:
            await query.answer("⛔ Acceso restringido", show_alert=True)
            return
        if target_cat == "data" and not (is_admin or is_publisher):
            await query.answer("⛔ Acceso restringido", show_alert=True)
            return
        if target_cat == "links" and not (is_admin or is_publisher):
            await query.answer("⛔ Acceso restringido", show_alert=True)
            return
        
        # Construir texto
        cat_title, commands = help_data.get(target_cat, ("Desconocido", []))

        text = f"🤖 <b>Ayuda de ZeePub Bot</b>\n\n"
        text += f"📂 <b>Categoría: {cat_title}</b>\n\n"

        for cmd, desc in commands:
            safe_cmd = cmd.replace("<", "&lt;").replace(">", "&gt;")
            safe_desc = desc.replace("<", "&lt;").replace(">", "&gt;")
            text += f"<b>{safe_cmd}</b>\n   ╰ {safe_desc}\n"

        reply_markup = self._get_help_keyboard(is_admin, is_publisher)

        try:
            await query.edit_message_text(
                text=text, reply_markup=reply_markup, parse_mode="HTML"
            )
        except Exception:
            pass 
        await query.answer()

    def _get_help_data(self, uid):
        """Genera la estructura de ayuda y el teclado según el rol del usuario."""
        is_admin = uid in config.ADMIN_USERS
        is_publisher = uid in config.FACEBOOK_PUBLISHERS

        # 1. Inicio (Todos)
        cat_home = [
            ("📚 /start", "Menú Principal"),
            ("❓ /help", "Ver este mensaje"),
            ("💡 /sugerencia <txt>", "Enviar sugerencia"),
            ("📊 /status", "Ver tu estado y descargas"),
            ("❌ /cancel", "Cancelar acción actual"),
        ]
        if config.ENABLE_GROUP_MANAGER:
             cat_home.append(("📋 /reglas", "Ver reglas del grupo"))

        # 2. Contenido / Herramientas (Mixed)
        cat_content = [
            ("🔍 /search", "Buscar libros"),
        ]
        if is_publisher or is_admin:
            cat_content.extend(
                [
                    ("📤 /export_db", "Exportar mapeo de URLs a CSV"),
                ]
            )

        # 3. Admin (Admin only)
        cat_admin = []
        if is_admin:
            cat_admin = [
                ("➕ /add_user", "Agregar/Editar usuario"),
                ("➖ /remove_user", "Remover usuario"),
                ("🏷️ /set_staff_status", "Definir status de Staff"),
                ("⏲️ /set_auto_delete_time", "Tiempo auto-borrado"),
                ("📊 /stats <rol>", "Ver stats o listar usuarios"),
                ("🔄 /reset", "Resetear descargas"),
                ("🐞 /debug_state", "Info debug usuario"),
                ("🔧 /setlog", "Configurar logs"),
                ("🆔 /id", "Info ID chat/user"),
                ("🆕 /update_system", "Actualizar sistema"),
                ("⚠️ /update_system force", "Forzar reinstalación"),
                ("🧩 /plugins", "Listar plugins"),
            ]

        # 4. Datos / Backup (Admin only)
        cat_data = []
        enable_maint = os.getenv("ENABLE_DB_MAINTENANCE", "True").lower() == "true"
        if enable_maint:
            if is_admin:
                cat_data.extend(
                    [
                        ("📦 /backup_db", "Backup DB"),
                        ("♻️ /restore_db", "Restaurar DB desde archivo"),
                        ("📚 /import_history", "Importar historial JSON"),
                        ("🆕 /latest_books", "Ver últimos libros"),
                        ("🗑️ /clear_history", "Borrar historial"),
                    ]
                )
            if is_admin or is_publisher:
                cat_data.extend(
                    [
                        ("📤 /export_db", "Exportar DB CSV"),
                        ("📤 /export_history", "Exportar historial CSV"),
                    ]
                )

        # 5. Plugins (Custom Messages)
        cat_plugins = []
        enable_custom = os.getenv("ENABLE_CUSTOM_MESSAGES", "False").lower() == "true"
        if is_admin and enable_custom:
            cat_plugins = [
                ("📝 /add_msge <id>", "Guardar mensaje respondido"),
                ("📂 /list_msge [id]", "Listar o ver mensaje"),
                ("📨 /send_msge <id> <chat>", "Enviar mensaje guardado"),
                ("👋 /saludo <chat> <id|txt>", "Enviar saludo/mensaje"),
                ("🚪 /set_welcome <id|off>", "Configurar bienvenida"),
            ]

        # 6. Plugins (Donations)
        cat_donations = []
        enable_donations = os.getenv("ENABLE_DONATIONS", "True").lower() == "true"
        if enable_donations:
            cat_donations = [
                ("☕ /donar", "Link de donación"),
                ("🌟 /niveles", "Info de niveles de usuario"),
            ]
            if is_admin:
                cat_donations.append(("💲 /set_price", "Configurar precio donación"))

        # 7. Plugins (Links Manager)
        cat_links = []
        enable_links = os.getenv("ENABLE_LINKS_MANAGER", "True").lower() == "true"
        if enable_links and (is_publisher or is_admin):
            cat_links = [
                ("📈 /status_links", "Ver estado de links"),
                ("📋 /link_list", "Listar links recientes"),
                ("🗑️ /purge_link", "Eliminar un link"),
            ]

        return (
            {
                "home": ("🏠 Inicio", cat_home),
                "content": ("📚 Content", cat_content),
                "admin": ("🛠 Admin", cat_admin),
                "data": ("💾 Datos", cat_data),
                "plugins": ("🧩 Mensajes", cat_plugins),
                "donations": ("💸 Donaciones", cat_donations),
                "links": ("🔗 Links", cat_links),
            },
            is_admin,
            is_publisher,
        )

    def _get_help_keyboard(self, is_admin: bool, is_publisher: bool):
        """Genera el teclado de ayuda dinámicamente."""
        row1 = [
            InlineKeyboardButton("🏠 Inicio", callback_data="help|home"),
            InlineKeyboardButton("📚 Content", callback_data="help|content"),
        ]

        if os.getenv("ENABLE_DONATIONS", "True").lower() == "true":
            row1.append(
                InlineKeyboardButton("💸 Donaciones", callback_data="help|donations")
            )

        keyboard = [row1]

        row2 = []
        enable_links = os.getenv("ENABLE_LINKS_MANAGER", "True").lower() == "true"
        enable_maint = os.getenv("ENABLE_DB_MAINTENANCE", "True").lower() == "true"

        if enable_links and (is_admin or is_publisher):
            row2.append(InlineKeyboardButton("🔗 Links", callback_data="help|links"))

        if is_admin:
            row2.append(InlineKeyboardButton("🛠 Admin", callback_data="help|admin"))

        if enable_maint and (is_admin or is_publisher):
            row2.append(InlineKeyboardButton("💾 Datos", callback_data="help|data"))
        
        if row2:
            keyboard.append(row2)
            
        row3 = []
        if is_admin:
             if os.getenv("ENABLE_CUSTOM_MESSAGES", "False").lower() == "true":
                  row3.append(InlineKeyboardButton("🧩 Mensajes", callback_data="help|plugins"))

        if row3:
            keyboard.append(row3)

        # Add Close button as per screenshot
        keyboard.append([InlineKeyboardButton("❌ Cerrar", callback_data="help|close")])

        return InlineKeyboardMarkup(keyboard)
