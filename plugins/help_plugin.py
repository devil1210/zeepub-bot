import logging
import os
import html
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
    "menu": {
        "cat": "home",
        "desc": "Menú interactivo",
        "long_desc": "Muestra un menú interactivo con botones para acceder rápidamente a las diferentes funciones del bot organizadas por categorías.",
        "usage": "/menu",
        "example": "/menu",
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
        "long_desc": "Envía un mensaje directo al equipo de staff. Úsalo para reportar errores, sugerir nuevas funciones o pedir libros específicos. Adjunta detalles para que podamos ayudarte mejor.",
        "usage": "/sugerencia <texto>",
        "example": "/sugerencia Hola, el libro 'Dune' tiene un error en el capítulo 3.",
    },
    # --- Content ---
    "search": {
        "cat": "content",
        "desc": "Buscar libros",
        "long_desc": "Busca libros en la biblioteca. Puedes buscar por Título, Autor o Serie. Los resultados mostrarán un botón para descargar.\n\nTip: Sé específico para mejores resultados.",
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
    # --- User Management ---
    "add_user": {
        "cat": "user_mgmt",
        "desc": "Agregar/Editar usuario",
        "long_desc": "Agrega un usuario a la base de datos o actualiza su rol (VIP, Premium, etc.) y duración de beneficios.",
        "usage": "/add_user <user_id> <rol> [dias]",
        "example": "/add_user 123456789 vip 30",
    },
    "remove_user": {
        "cat": "user_mgmt",
        "desc": "Remover usuario",
        "long_desc": "Revoca los privilegios especiales de un usuario, volviéndolo al estado 'Free'.",
        "usage": "/remove_user <user_id>",
        "example": "/remove_user 123456789",
    },
    "set_rol": {
        "cat": "user_mgmt",
        "desc": "Gestionar Staff/Rol",
        "long_desc": "Otorga o revoca el estado de 'Staff' a un usuario. Cambia el [Rol] funcional.",
        "usage": "/set_rol <user_id> <label>",
        "example": "/set_rol 123456789 Editor Jefe",
    },
    "set_apodo": {
        "cat": "user_mgmt",
        "desc": "Establecer Apodo",
        "long_desc": "Establece un apodo personalizado para un usuario, accesible via [Apodo].",
        "usage": "/set_apodo <user_id> <apodo>",
        "example": "/set_apodo 123456789 El Charly",
    },
    "reset": {
        "cat": "user_mgmt",
        "desc": "Resetear descargas",
        "long_desc": "Reinicia el contador de descargas diario de un usuario específico a 0.",
        "usage": "/reset <user_id>",
        "example": "/reset 123456789",
    },
    "id": {
        "cat": "user_mgmt",
        "desc": "Info ID",
        "long_desc": "Muestra el ID numérico del chat actual y del usuario que envía el mensaje.",
        "usage": "/id",
        "example": "/id",
    },
    "setlog": {
        "cat": "admin",
        "desc": "Nivel de log",
        "long_desc": "Cambia el nivel de verbosidad de los logs del sistema en tiempo real.",
        "usage": "/setlog <INFO|DEBUG|WARNING>",
        "example": "/setlog DEBUG",
    },
    "stats": {
        "cat": "admin",
        "desc": "Estadísticas",
        "long_desc": "Muestra estadísticas diarias del sistema o lista usuarios por rol (Admin/Staff only).",
        "usage": "/stats [rol]",
        "example": "/stats vip",
    },
    "evil": {
        "cat": "admin",
        "desc": "Modo Privado",
        "long_desc": "Inicia el modo privado (Evil) solicitando contraseña.",
        "usage": "/evil",
        "example": "/evil",
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
        "long_desc": "Muestra el estado interno completo de un usuario: historial de navegación OPDS temporal, buffer de descarga y variables de sesión. Útil para diagnosticar problemas de navegación.",
        "usage": "/debug_state <user_id>",
        "example": "/debug_state 123456789",
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
    "approve_donation": {
        "cat": "admin",
        "desc": "Aprobar donación",
        "long_desc": "Aprueba una donación, actualiza el nivel del usuario y envía notificación automática.",
        "usage": "/approve_donation <id> <rol> [meses]",
        "example": "/approve_donation 123456 vip 1",
    },
    "reject_donation": {
        "cat": "admin",
        "desc": "Rechazar donación",
        "long_desc": "Rechaza una donación y envía notificación automática al usuario.",
        "usage": "/reject_donation <id>",
        "example": "/reject_donation 123456",
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
    "reset_msge": {
        "cat": "plugins",
        "desc": "Resetear mensaje",
        "long_desc": "Borra un mensaje personalizado y restaura el original. Útil si te equivocaste al editar.",
        "usage": "/reset_msge <slug>",
        "example": "/reset_msge start_welcome_unlimited",
    },
    "list_msge": {
        "cat": "plugins",
        "desc": "Ver mensajes",
        "long_desc": "Lista todos los mensajes guardados. Si se da un ID, muestra una vista previa de ese mensaje.",
        "usage": "/list_msge [slug]",
        "example": "/list_msge bienvenida_v1",
    },
    "view_msge": {
        "cat": "plugins",
        "desc": "Previsualizar mensaje",
        "long_desc": "Muestra cómo se verá un template renderizado con HTML procesado (útil para ver el resultado final del template).",
        "usage": "/view_msge <slug>",
        "example": "/view_msge start_welcome_unlimited",
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
    "templates": {
        "cat": "admin",
        "desc": "Lista las plantillas disponibles",
        "long_desc": "Muestra todas las plantillas de mensajes registradas y las variables que aceptan.",
        "usage": "/templates",
        "example": "/templates",
    },
    "set_var": {
        "cat": "admin",
        "desc": "Define variable global",
        "long_desc": "Crea o actualiza una variable global que puede usarse en cualquier plantilla con [NombreVariable].",
        "usage": "/set_var <Variable> <Valor>",
        "example": "/set_var CanalOficial https://t.me/mi_canal",
    },
    "del_var": {
        "cat": "admin",
        "desc": "Elimina variable global",
        "long_desc": "Borra una variable global personalizada.",
        "usage": "/del_var <Variable>",
        "example": "/del_var CanalOficial",
    },
    "vars": {
        "cat": "admin",
        "desc": "Lista variables globales",
        "long_desc": "Muestra todas las variables globales disponibles (del sistema y personalizadas). Alías: /template_vars",
        "usage": "/vars",
        "example": "/vars",
    },
    "template_vars": {
        "cat": "admin",
        "desc": "Listar variables",
        "long_desc": "Lista las variables globales disponibles (como [Nombre], [Fecha]) para usar en cualquier plantilla.",
        "usage": "/template_vars",
        "example": "/template_vars",
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
        "long_desc": "Configura un mensaje de bienvenida personalizado para este grupo. Debes crear el mensaje primero con /add_msge.\n\n✨ <b>Personalización:</b> Si el mensaje guardado contiene <code>[Nombre]</code>, será reemplazado por el nombre del usuario nuevo.",
        "usage": "/set_group_welcome <slug>",
        "example": "/set_group_welcome bienvenida_grupo",
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
    "user_mgmt": "👥 Usuarios",
}


class HelpPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "help_plugin"

    @property
    def version(self) -> str:
        return "2.3.0"

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
            # New mapping
            app.add_handler(CommandHandler("help", self.help_simple))
            app.add_handler(CommandHandler("ayuda", self.help_simple))
            
            # Interactive mode
            app.add_handler(CommandHandler("menu", self.help_interactive))
            app.add_handler(CommandHandler("help_full", self.help_interactive))
            
            app.add_handler(
                CallbackQueryHandler(self.help_navigation_callback, pattern=r"^help\|")
            )

            logger.info("Plugin Help: Handlers registrados.")
            
            # Register Bot Commands Menu
            try:
                # We do this in a background task to not block initialization if many admins
                import asyncio
                asyncio.create_task(self.update_bot_commands(app.bot))
            except Exception as e:
                logger.warning(f"Error scheduling bot commands update: {e}")

            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin Help: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    async def _check_permissions(self, uid):
        # Check DB for role
        from services.user_service import get_effective_user
        user_data = await get_effective_user(uid)
        role = user_data.get("role", "free")
        custom_status = user_data.get("custom_status")

        is_admin = (role == "admin") or (uid in config.ADMIN_USERS)
        is_publisher = (role == "staff" and custom_status == "Publicador")
        
        return is_admin, is_publisher

    def _get_visible_categories(self, is_admin, is_publisher):
        visible = ["home", "content"]

        # Check env vars for feature flags
        enable_donations = os.getenv("ENABLE_DONATIONS", "True").lower() == "true"
        enable_links = os.getenv("ENABLE_LINKS_MANAGER", "True").lower() == "true"
        enable_maint = os.getenv("ENABLE_DB_MAINTENANCE", "True").lower() == "true"
        enable_custom = os.getenv("ENABLE_CUSTOM_MESSAGES", "True").lower() == "true"
        enable_group = config.ENABLE_GROUP_MANAGER

        if enable_donations:
            visible.append("donations")

        if is_admin:
            visible.append("admin")
            if enable_group:
                visible.append("group_manager")
            if enable_custom:
                visible.append("plugins")
            visible.append("user_mgmt")

        if enable_maint and (is_admin or is_publisher):
            visible.append("data")

        if enable_links and (is_admin or is_publisher):
            visible.append("links")

        return visible

    async def help_simple(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra una lista simple de comandos disponibles."""
        uid = update.effective_user.id
        thread_id = get_thread_id(update)
        
        is_admin, is_publisher = await self._check_permissions(uid)
        visible_cats = self._get_visible_categories(is_admin, is_publisher)
        
        text = "🤖 <b>Comandos Disponibles</b>\n\n"
        
        # Iterar categorias en orden deseado (definido en CATEGORIES o visible_cats order)
        # visible_cats tiene un orden basico
        
        for cat_key in visible_cats:
            cat_name = CATEGORIES.get(cat_key, cat_key)
            
            # Get commands for this cat
            cmds = [k for k, v in COMMANDS_REGISTRY.items() if v["cat"] == cat_key]
            cmds.sort()
            
            if not cmds:
                continue
                
            text += f"<b>{cat_name}</b>\n"
            for cmd in cmds:
                desc = COMMANDS_REGISTRY[cmd]["desc"]
                text += f"/{cmd} - {desc}\n"
            text += "\n"
            
        text += "💡 <i>Usa /menu para ver la ayuda interactiva.</i>"
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )

    async def help_interactive(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú principal de ayuda (Interactivo)."""
        uid = update.effective_user.id
        first_name = update.effective_user.first_name
        thread_id = get_thread_id(update)

        cms = context.application.plugin_manager.get_plugin("custom_messages")

        base_text = (
            "🤖 <b>Ayuda de ZeePub Bot</b>\n\n"
            "Bienvenido al sistema de ayuda interactiva. Selecciona una categoría abajo "
            "para ver los comandos disponibles y sus detalles."
        )
        text = base_text
        if cms and cms.enabled:
            text = await cms.get_text(
                "help_main_header", user=update.effective_user
            )

        # Pre-calc permissions for keyboard builder
        is_admin, is_publisher = await self._check_permissions(uid)
        keyboard = self._build_category_keyboard(is_admin, is_publisher)

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
        first_name = update.effective_user.first_name
        data = query.data.split("|")

        # Format: help | action | arg
        action = data[1]
        arg = data[2] if len(data) > 2 else None
        
        # Check permissions early
        is_admin, is_publisher = await self._check_permissions(uid)

        if action == "close":
            cms = context.application.plugin_manager.get_plugin("custom_messages")

            base_closing = "👋 Gracias por usar el bot."
            text_closing = base_closing
            if cms and cms.enabled:
                text_closing = await cms.get_text(
                    "bot_closing", Nombre=update.effective_user.mention_html()
                )

            await query.edit_message_text(text_closing)
            return

        if action == "home":
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_text = (
                "🤖 <b>Ayuda de ZeePub Bot</b>\n\n"
                "Selecciona una categoría para ver los comandos:"
            )
            text = base_text
            if cms and cms.enabled:
                text = await cms.get_text(
                    "help_main_header", Nombre=update.effective_user.mention_html()
                )

            keyboard = self._build_category_keyboard(is_admin, is_publisher)
            await query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )

        visible_cats = self._get_visible_categories(is_admin, is_publisher)

        if action == "cat":
            # View Category Commands
            cat_key = arg
            if cat_key not in visible_cats:
                await query.answer("⛔ No tienes permiso.", show_alert=True)
                return

            cat_name = CATEGORIES.get(cat_key, "Desconocido")
            
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            text = f"📂 <b>Categoría: {cat_name}</b>\n\nSelecciona un comando para ver detalles:"
            
            if cms and cms.enabled:
                text = await cms.get_text(
                   "help_cat_header", user=update.effective_user, Categoria=cat_name
                )

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

            # Try to get from template system
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            template_text = None
            if cms and cms.enabled:
                # Use update.effective_user or context.bot.get_chat(uid) if getting user object
                # We have 'update' here so:
                template_text = await cms.get_text(
                    f"help_cmd_{cmd_key}", user=update.effective_user
                )

            # Fallback if no template or plugin disabled (should match default registry content)
            if template_text:
                text = template_text
            else:
                usage_safe = html.escape(cmd_data["usage"])
                text = (
                    f"ℹ️ <b>Comando: /{cmd_key}</b>\n\n"
                    f"📝 <b>Descripción:</b>\n{cmd_data['long_desc']}\n\n"
                    f"⌨️ <b>Uso:</b> <code>{usage_safe}</code>\n"
                )
                if "example" in cmd_data:
                    ex_safe = html.escape(cmd_data["example"])
                    text += f"💡 <b>Ejemplo:</b> <code>{ex_safe}</code>"

            keyboard = self._build_detail_keyboard(cmd_data["cat"])
            await query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )

        await query.answer()

    def _build_category_keyboard(self, is_admin, is_publisher):
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

    async def update_bot_commands(self, bot):
        """Registra los comandos en el menú nativo de Telegram (/)."""
        from telegram import BotCommand, BotCommandScopeDefault, BotCommandScopeChat, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats, BotCommandScopeAllChatAdministrators
        try:
            # 1. Comandos para TODOS (Básicos)
            public_cmds = [
                BotCommand("start", "Iniciar bot"),
                BotCommand("help", "Ayuda simple"),
                BotCommand("menu", "Menú interactivo"),
                BotCommand("search", "Buscar libros"),
                BotCommand("donar", "Link donación"),
                BotCommand("niveles", "Info niveles"),
                BotCommand("status", "Mi estado"),
                BotCommand("cancel", "Cancelar acción"),
            ]
            
            # Forzar visibilidad en todos los contextos posibles para usuarios normales
            await bot.set_my_commands(public_cmds, scope=BotCommandScopeDefault())
            await bot.set_my_commands(public_cmds, scope=BotCommandScopeAllPrivateChats())
            await bot.set_my_commands(public_cmds, scope=BotCommandScopeAllGroupChats())
            logger.debug("Comandos básicos registrados en scopes globales.")

            # 2. Menú COMPLETO para Administradores configurados (en su privado)
            all_cmds = []
            for cmd_name in sorted(COMMANDS_REGISTRY.keys()):
                if len(all_cmds) >= 100: break
                data = COMMANDS_REGISTRY[cmd_name]
                all_cmds.append(BotCommand(cmd_name, data["desc"]))

            for admin_id in config.ADMIN_USERS:
                try:
                    await bot.set_my_commands(all_cmds, scope=BotCommandScopeChat(chat_id=admin_id))
                except Exception as e:
                    logger.debug(f"No se pudieron setear comandos completos para admin {admin_id}: {e}")
            
            logger.info("Menú de comandos actualizado con scopes específicos.")
        except Exception as e:
            logger.error(f"Error actualizando menú de comandos en Telegram: {e}")
