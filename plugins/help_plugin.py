import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from plugins.base_plugin import BasePlugin
from config.config_settings import config
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)

# --- Command Registry ---
# Structure:
# {
#   "command_name": {
#       "cat": "category_key",
#       "desc": "Short description",
#       "long_desc": "Detailed description",
#       "usage": "/command <args>",
#       "example": "/command example"
#   }
# }

COMMANDS_REGISTRY = {
    # --- Home / General ---
    "start": {
        "cat": "home",
        "desc": "Inicia el bot",
        "long_desc": "Inicia el bot, registra al usuario en la base de datos si es nuevo y muestra el menú principal o las descargas disponibles.",
        "usage": "/start",
        "example": "/start",
    },
    "help": {
        "cat": "home",
        "desc": "Muestra este menú",
        "long_desc": "Muestra el menú de ayuda interactivo con categorías y detalles de comandos.",
        "usage": "/help",
        "example": "/help",
    },
    "status": {
        "cat": "home",
        "desc": "Ver tu estado",
        "long_desc": "Muestra información sobre tu cuenta: nivel de usuario (Free, VIP, etc.), descargas restantes hoy y tiempo para el reinicio.",
        "usage": "/status",
        "example": "/status",
    },
    "cancel": {
        "cat": "home",
        "desc": "Cancelar acción",
        "long_desc": "Cancela cualquier operación en curso, como búsquedas pendientes o navegación de menús, y limpia el estado temporal.",
        "usage": "/cancel",
        "example": "/cancel",
    },
    "sugerencia": {
        "cat": "home",
        "desc": "Enviar sugerencia",
        "long_desc": "Envía un mensaje directo al equipo de staff con tu sugerencia, reporte de error o comentario.",
        "usage": "/sugerencia <texto>",
        "example": "/sugerencia Me gustaría ver más libros de ciencia ficción.",
    },
    # --- Content ---
    "search": {
        "cat": "content",
        "desc": "Buscar libros",
        "long_desc": "Busca libros en la biblioteca por título o autor. Puedes escribir solo el comando para iniciar un modo de búsqueda.",
        "usage": "/search <término>",
        "example": "/search Brandon Sanderson",
    },
    # --- Donations ---
    "donar": {
        "cat": "donations",
        "desc": "Link de donación",
        "long_desc": "Genera un enlace para realizar donaciones a través de Ko-fi y apoyar el proyecto.",
        "usage": "/donar",
        "example": "/donar",
    },
    "niveles": {
        "cat": "donations",
        "desc": "Info niveles",
        "long_desc": "Muestra la tabla de niveles de donación y los beneficios asociados a cada uno (VIP, Premium, etc.).",
        "usage": "/niveles",
        "example": "/niveles",
    },
    # --- Group Manager ---
    "reglas": {
        "cat": "home",  # Visible to all
        "desc": "Ver reglas",
        "long_desc": "Muestra las reglas configuradas para el grupo actual.",
        "usage": "/reglas",
        "example": "/reglas",
    },
    # --- Admin ---
    "add_user": {
        "cat": "admin",
        "desc": "Agregar/Editar usuario",
        "long_desc": "Agrega un usuario a la base de datos o actualiza su rol (VIP, Premium, etc.) y duración de beneficios.",
        "usage": "/add_user <user_id> <rol> [dias]",
        "example": "/add_user 123456789 vip 30",
    },
    "remove_user": {
        "cat": "admin",
        "desc": "Remover usuario",
        "long_desc": "Revoca los privilegios especiales de un usuario, volviéndolo al estado 'Free'.",
        "usage": "/remove_user <user_id>",
        "example": "/remove_user 123456789",
    },
    "set_staff_status": {
        "cat": "admin",
        "desc": "Gestionar Staff",
        "long_desc": "Otorga o revoca el estado de 'Staff' a un usuario.",
        "usage": "/set_staff_status <user_id> <on|off>",
        "example": "/set_staff_status 123456789 on",
    },
    "stats": {
        "cat": "admin",
        "desc": "Ver estadísticas",
        "long_desc": "Muestra estadísticas del bot. Si no se especifican argumentos, muestra resumen general. Si se especifica rol, lista usuarios.",
        "usage": "/stats [rol]",
        "example": "/stats vip",
    },
    "reset": {
        "cat": "admin",
        "desc": "Resetear descargas",
        "long_desc": "Reinicia el contador de descargas diario de un usuario específico a 0.",
        "usage": "/reset <user_id>",
        "example": "/reset 123456789",
    },
    "setlog": {
        "cat": "admin",
        "desc": "Nivel de log",
        "long_desc": "Cambia el nivel de verbosidad de los logs del sistema en tiempo real.",
        "usage": "/setlog <INFO|DEBUG|WARNING>",
        "example": "/setlog DEBUG",
    },
    "set_auto_delete_time": {
        "cat": "admin",
        "desc": "Tiempo auto-borrado",
        "long_desc": "Configura el tiempo (en minutos) antes de que los libros enviados se eliminen automáticamente.",
        "usage": "/set_auto_delete_time <minutos>",
        "example": "/set_auto_delete_time 60",
    },
    "debug_state": {
        "cat": "admin",
        "desc": "Info debug",
        "long_desc": "Muestra el estado interno de un usuario (buffer de descarga, historial, etc.) para depuración.",
        "usage": "/debug_state <user_id>",
        "example": "/debug_state 123456789",
    },
    "id": {
        "cat": "admin",
        "desc": "Info ID",
        "long_desc": "Muestra el ID numérico del chat actual y del usuario que envía el mensaje.",
        "usage": "/id",
        "example": "/id",
    },
    "update_system": {
        "cat": "admin",
        "desc": "Actualizar bot",
        "long_desc": "Ejecuta un 'git pull' y reinicia el contenedor para actualizar el bot. Use 'force' para sobrescribir cambios locales.",
        "usage": "/update_system [force]",
        "example": "/update_system force",
    },
    "plugins": {
        "cat": "admin",
        "desc": "Listar plugins",
        "long_desc": "Lista todos los plugins cargados y sus versiones.",
        "usage": "/plugins",
        "example": "/plugins",
    },
    "set_price": {
        "cat": "admin",  # Technically donations plugin but admin only
        "desc": "Configurar precios",
        "long_desc": "Configura el precio base para los niveles de donación.",
        "usage": "/set_price <nivel> <monto>",
        "example": "/set_price vip 10",
    },
    # --- Data / Maintenance ---
    "backup_db": {
        "cat": "data",
        "desc": "Backup DB",
        "long_desc": "Genera y envía un archivo de respaldo de la base de datos principal.",
        "usage": "/backup_db",
        "example": "/backup_db",
    },
    "restore_db": {
        "cat": "data",
        "desc": "Restaurar DB",
        "long_desc": "Restaura la base de datos desde un archivo adjunto. Debe responder al mensaje del archivo.",
        "usage": "Responder a archivo con /restore_db",
        "example": "/restore_db",
    },
    "import_history": {
        "cat": "data",
        "desc": "Importar historial",
        "long_desc": "Importa historial de publicaciones desde un JSON exportado de Telegram.",
        "usage": "Responder a archivo JSON con /import_history",
        "example": "/import_history",
    },
    "latest_books": {
        "cat": "data",
        "desc": "Libros recientes",
        "long_desc": "Muestra una lista de los últimos libros añadidos al historial de publicaciones.",
        "usage": "/latest_books [chat_id]",
        "example": "/latest_books -100123456",
    },
    "clear_history": {
        "cat": "data",
        "desc": "Borrar historial",
        "long_desc": "Elimina todos los registros de libros publicados del historial. Requiere confirmación.",
        "usage": "/clear_history",
        "example": "/clear_history",
    },
    "export_db": {
        "cat": "data",
        "desc": "Exportar mappings",
        "long_desc": "Exporta el mapeo de IDs a base de datos en formato CSV.",
        "usage": "/export_db",
        "example": "/export_db",
    },
    "export_history": {
        "cat": "data",
        "desc": "Exportar historial",
        "long_desc": "Exporta el historial completo de libros publicados a un archivo CSV.",
        "usage": "/export_history",
        "example": "/export_history",
    },
    # --- Custom Messages (Plugins) ---
    "add_msge": {
        "cat": "plugins",
        "desc": "Guardar mensaje",
        "long_desc": "Guarda el contenido del mensaje al que se responde para usarlo posteriormente. Requiere un ID único (slug).",
        "usage": "Responder con /add_msge <slug>",
        "example": "/add_msge bienvenida_v1",
    },
    "list_msge": {
        "cat": "plugins",
        "desc": "Ver mensajes",
        "long_desc": "Lista todos los mensajes guardados. Si se da un ID, muestra una vista previa de ese mensaje.",
        "usage": "/list_msge [slug]",
        "example": "/list_msge bienvenida_v1",
    },
    "send_msge": {
        "cat": "plugins",
        "desc": "Enviar guardado",
        "long_desc": "Envía una copia exacta de un mensaje guardado a un chat específico.",
        "usage": "/send_msge <slug> <chat_id>",
        "example": "/send_msge bienvenida_v1 -1001234567",
    },
    "saludo": {
        "cat": "plugins",
        "desc": "Enviar saludo",
        "long_desc": "Envía un mensaje de texto o un mensaje guardado a un chat.",
        "usage": "/saludo <chat_id> <texto|slug>",
        "example": "/saludo -100123 Hola!",
    },
    "set_welcome": {
        "cat": "plugins",
        "desc": "Configurar bienvenida",
        "long_desc": "Define qué mensaje guardado se usará como bienvenida automática global (si aplica).",
        "usage": "/set_welcome <slug|off>",
        "example": "/set_welcome bienvenida_v1",
    },
    # --- Links ---
    "status_links": {
        "cat": "links",
        "desc": "Estado links",
        "long_desc": "Muestra estadísticas sobre los enlaces generados y su estado.",
        "usage": "/status_links",
        "example": "/status_links",
    },
    "link_list": {
        "cat": "links",
        "desc": "Listar links",
        "long_desc": "Muestra una lista de los enlaces generados recientemente.",
        "usage": "/link_list",
        "example": "/link_list",
    },
    "purge_link": {
        "cat": "links",
        "desc": "Borrar link",
        "long_desc": "Elimina un enlace generado de la base de datos.",
        "usage": "/purge_link <id>",
        "example": "/purge_link 123",
    },
    "authorize_group": {
        "cat": "group_manager",
        "desc": "Autorizar grupo",
        "long_desc": "Autoriza al bot a funcionar en el grupo especificado.",
        "usage": "/authorize_group [chat_id]",
        "example": "/authorize_group -100123456",
    },
    "revoke_group": {
        "cat": "group_manager",
        "desc": "Revocar grupo",
        "long_desc": "Revoca la autorización del bot en un grupo.",
        "usage": "/revoke_group [chat_id]",
        "example": "/revoke_group",
    },
    "set_group_welcome": {
        "cat": "group_manager",
        "desc": "Bienvenida grupo",
        "long_desc": "Configura un mensaje de bienvenida específico para el grupo actual.",
        "usage": "/set_group_welcome <slug>",
        "example": "/set_group_welcome saludo_grupo",
    },
}

CATEGORIES = {
    "home": "🏠 Inicio",
    "content": "📚 Contenido",
    "admin": "🛠 Admin",
    "data": "💾 Datos",
    "plugins": "🧩 Mensajes",
    "donations": "💸 Donaciones",
    "links": "🔗 Links",
    "group_manager": "👥 Grupos",
}


class HelpPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "help_plugin"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "Ayuda avanzada con navegación interactiva y detalles."

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
            app.add_handler(CommandHandler("ayuda", self.help))
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

    def _check_permissions(self, uid):
        is_admin = uid in config.ADMIN_USERS
        is_publisher = uid in config.FACEBOOK_PUBLISHERS
        return is_admin, is_publisher

    def _get_visible_categories(self, is_admin, is_publisher):
        visible = ["home", "content"]

        # Check env vars for feature flags
        enable_donations = os.getenv("ENABLE_DONATIONS", "True").lower() == "true"
        enable_links = os.getenv("ENABLE_LINKS_MANAGER", "True").lower() == "true"
        enable_maint = os.getenv("ENABLE_DB_MAINTENANCE", "True").lower() == "true"
        enable_custom = os.getenv("ENABLE_CUSTOM_MESSAGES", "False").lower() == "true"
        enable_group = config.ENABLE_GROUP_MANAGER

        if enable_donations:
            visible.append("donations")

        if is_admin:
            visible.append("admin")
            if enable_group:
                visible.append("group_manager")
            if enable_custom:
                visible.append("plugins")

        if enable_maint and (is_admin or is_publisher):
            visible.append("data")

        if enable_links and (is_admin or is_publisher):
            visible.append("links")

        return visible

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú principal de ayuda."""
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        text = (
            "🤖 <b>Ayuda de ZeePub Bot</b>\n\n"
            "Bienvenido al sistema de ayuda interactiva. Selecciona una categoría abajo "
            "para ver los comandos disponibles y sus detalles."
        )

        keyboard = self._build_category_keyboard(uid)

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
        query = update.callback_query
        uid = update.effective_user.id
        data = query.data.split("|")

        # Format: help | action | arg
        action = data[1]
        arg = data[2] if len(data) > 2 else None

        if action == "close":
            await query.message.delete()
            return

        if action == "home":
            text = (
                "🤖 <b>Ayuda de ZeePub Bot</b>\n\n"
                "Selecciona una categoría para ver los comandos:"
            )
            keyboard = self._build_category_keyboard(uid)
            await query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )
            return

        is_admin, is_publisher = self._check_permissions(uid)
        visible_cats = self._get_visible_categories(is_admin, is_publisher)

        if action == "cat":
            # View Category Commands
            cat_key = arg
            if cat_key not in visible_cats:
                await query.answer("⛔ No tienes permiso.", show_alert=True)
                return

            cat_name = CATEGORIES.get(cat_key, "Desconocido")
            text = f"📂 <b>Categoría: {cat_name}</b>\n\nSelecciona un comando para ver detalles:"

            keyboard = self._build_commands_keyboard(cat_key)
            await query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )

        elif action == "cmd":
            # View Command Detail
            cmd_key = arg
            cmd_data = COMMANDS_REGISTRY.get(cmd_key)

            if not cmd_data:
                await query.answer("Comando no encontrado.", show_alert=True)
                return

            # Logic check: is the command in a visible category?
            # (Strictly speaking we could skip this check if we trust the menu flow,
            # but good for safety if someone crafts a payload)
            if (
                cmd_data["cat"] not in visible_cats and cmd_data["cat"] != "home"
            ):  # Home always visible
                await query.answer("⛔ No tienes permiso.", show_alert=True)
                return

            text = (
                f"ℹ️ <b>Comando: /{cmd_key}</b>\n\n"
                f"📝 <b>Descripción:</b>\n{cmd_data['long_desc']}\n\n"
                f"⌨️ <b>Uso:</b> <code>{cmd_data['usage']}</code>\n"
            )
            if "example" in cmd_data:
                text += f"💡 <b>Ejemplo:</b> <code>{cmd_data['example']}</code>"

            keyboard = self._build_detail_keyboard(cmd_data["cat"])
            await query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )

        await query.answer()

    def _build_category_keyboard(self, uid):
        is_admin, is_publisher = self._check_permissions(uid)
        visible = self._get_visible_categories(is_admin, is_publisher)

        buttons = []
        row = []
        for cat in visible:
            label = CATEGORIES.get(cat, cat)
            row.append(InlineKeyboardButton(label, callback_data=f"help|cat|{cat}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        buttons.append([InlineKeyboardButton("❌ Cerrar", callback_data="help|close")])
        return InlineKeyboardMarkup(buttons)

    def _build_commands_keyboard(self, cat_key):
        # Filter commands by category
        cmds = [k for k, v in COMMANDS_REGISTRY.items() if v["cat"] == cat_key]
        cmds.sort()

        buttons = []
        row = []
        for cmd in cmds:
            desc = COMMANDS_REGISTRY[cmd]["desc"]
            # To save space, button label is just the command or command + short desc?
            # "search" vs "/search - Buscar"
            # Let's try "/search" to keep it clean, user already sees context.
            label = f"/{cmd}"
            row.append(InlineKeyboardButton(label, callback_data=f"help|cmd|{cmd}"))
            if len(row) == 2:  # 2 cols
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        # Back button
        buttons.append(
            [InlineKeyboardButton("🔙 Volver al Inicio", callback_data="help|home")]
        )
        return InlineKeyboardMarkup(buttons)

    def _build_detail_keyboard(self, cat_key):
        buttons = [
            [
                InlineKeyboardButton(
                    "🔙 Volver a Categoría", callback_data=f"help|cat|{cat_key}"
                ),
                InlineKeyboardButton("🏠 Inicio", callback_data="help|home"),
            ]
        ]
        return InlineKeyboardMarkup(buttons)
