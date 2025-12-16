import logging
import os
import html
import re
from datetime import datetime
from typing import Dict, Callable, List, Optional, Any
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    BigInteger,
    Text,
    DateTime,
)
from sqlalchemy.sql import text  # Importar text explícitamente
from sqlalchemy.orm import declarative_base, sessionmaker
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    ChatMemberHandler,
    CallbackQueryHandler,
)
from plugins.base_plugin import BasePlugin
from config.config_settings import config
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)
Base = declarative_base()


class StoredMessage(Base):
    __tablename__ = "stored_messages"
    slug = Column(String(64), primary_key=True)
    source_chat_id = Column(BigInteger, nullable=False)
    source_message_id = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    text_content = Column(
        Text, nullable=True
    )  # Contenido capturado para reemplazo de variables
    created_at = Column(DateTime, default=datetime.utcnow)


class PluginSettings(Base):
    __tablename__ = "custom_messages_settings"
    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=True)


class GlobalVariable(Base):
    __tablename__ = "global_variables"
    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=True)


# Registry for available templates
TEMPLATE_REGISTRY = {
    "banned_message": {
        "desc": "Mensaje para usuario baneado",
        "vars": ["[Fecha]"],
        "default": "⛔ Estás <b>baneado</b> del bot.{{if Fecha}} Hasta: <b>[Fecha]</b>{{endif}}",
    },
    "evil_password_success": {
        "desc": "Contraseña correcta (Modo Evil)",
        "vars": [],
        "default": "✅ Contraseña correcta. Elige destino:",
    },
    "evil_password_fail": {
        "desc": "Contraseña incorrecta (Modo Evil)",
        "vars": [],
        "default": "❌ Contraseña incorrecta.",
    },
    "search_no_results": {
        "desc": "Búsqueda sin resultados",
        "vars": ["[Termino]"],
        "default": "🔍 Mmm, no encontré nada para: [Termino]",
    },
    "private_default_fallback": {
        "desc": "Respuesta por defecto en chat privado",
        "vars": [],
        "default": "Usa /start para comenzar o selecciona una opción del menú.",
    },
    "start_welcome_unlimited": {
        "desc": "Bienvenida /start (Ilimitado)",
        "vars": ["[Nombre]"],
        "default": "👋 ¡Hola [Nombre]! Comencemos.\n\n✅ Tienes descargas ilimitadas.",
    },
    "start_welcome_limited": {
        "desc": "Bienvenida /start (Limitado)",
        "vars": ["[Nombre]", "[Descargas]"],
        "default": "👋 ¡Hola [Nombre]! Comencemos.\n\n⚡️ Te quedan [Descargas] descargas hoy.",
    },
    "evil_mode_prompt": {
        "desc": "Pregunta de destino (Admin -> Evil)",
        "vars": [],
        "default": "🔧 Modo Evil: ¿Dónde quieres publicar?",
    },
    "evil_password_prompt": {
        "desc": "Solicitud de contraseña",
        "vars": [],
        "default": "🔒 Modo Privado. Por favor, ingresa la contraseña:",
    },
    "cancel_confirmation": {
        "desc": "Confirmación de cancelación",
        "vars": [],
        "default": "✅ ¡Entendido! Operación cancelada.",
    },
    "donate_message": {
        "desc": "Mensaje comando /donar",
        "vars": ["[Nombre]", "[DonationUrl]"],
        "default": "💸 <b>Apoya el Mantenimiento del Bot</b>\n\nHola [Nombre], si te gusta el servicio, considera apoyar con una donación para cubrir los costos del servidor.\n\n<a href='[DonationUrl]'>☕ Invítame un café en Ko-fi</a>\n\n¡Gracias por tu apoyo!",
    },
    "levels_message": {
        "desc": "Mensaje comando /niveles",
        "vars": ["[white]", "[vip]", "[premium]", "[duration]"],
        "default": "📊 <b>Niveles de Usuario</b>\n\n⬜ <b>White</b>: [white] descargas/día\n⭐ <b>VIP</b>: [vip] descargas/día\n✨ <b>Premium</b>: [premium] descargas/día\n\nDuración Premium: [duration] días por donación.",
    },
    "bot_closing": {
        "desc": "Mensaje al cerrar menú",
        "vars": ["[Nombre]"],
        "default": "👋 Gracias por usar el bot.",
    },
    "donation_success": {
        "desc": "Confirmación de donación reportada",
        "vars": ["[Nombre]"],
        "default": "✅ <b>Notificación enviada</b>\n\nUn administrador revisará tu donación pronto y actualizará tu nivel.\n¡Muchas gracias por tu apoyo! ❤️",
    },
    "donation_admin_alert": {
        "desc": "Alerta a adminds sobre donación",
        "vars": ["[Nombre]", "[Alias]", "[ID]"],
        "default": "💰 <b>Nueva Donación Reportada</b>\n\n👤 <b>Usuario:</b> [Nombre]\n{{if Alias}}🔗 <b>Alias:</b> @[Alias]\n{{endif}}🆔 <b>ID:</b> <code>[ID]</code>\n\nEl usuario ha indicado que realizó una donación en Ko-fi.\nPor favor verifica y usa <code>/nivel</code> (si existiera) o actualiza manualmente.",
    },
    "search_instructions_legacy": {
        "desc": "Instrucciones de búsqueda (Usuario normal)",
        "vars": [],
        "default": "🔍 Para buscar, usa el comando:\n\n<code>/search término de búsqueda</code>\n\nEjemplo: <code>/search harry potter</code>",
    },
    "help_main_header": {
        "desc": "Encabezado principal de /help",
        "vars": ["[Nombre]"],
        "default": "👋 <b>Centro de Ayuda</b>\nHola [Nombre], aquí tienes los comandos disponibles:",
    },
    "status_message": {
        "desc": "Mensaje de estado (/status)",
        "vars": ["[Nivel]", "[Descargas]", "[ResetTime]", "[Expires]"],
        "default": "🤖 <b>ZeePub Bot</b> [VersionBot]\n\n📊 <b>Tu Estado</b>\n\n👤 <b>Usuario:</b> [Nombre]\n🆔 <b>ID:</b> [ID]\n⭐ <b>Nivel:</b> [Nivel]\n{{if Rol}}👨🏻‍💻 <b>Rol:</b> [Rol]\n{{endif}}{{if Apodo}}👨🏻‍💻 <b>Apodo:</b> [Apodo]\n{{endif}}{{if Expires}}📅 <b>Vence:</b> [Expires]\n{{endif}}📉 <b>Descargas:</b> [Descargas]\n{{if ResetTime}}⏳ <b>Reinicio en:</b> [ResetTime]\n{{endif}}",
    },
    "help_cat_header": {
        "desc": "Encabezado de categoría en /help",
        "vars": ["[Categoria]"],
        "default": "📂 <b>Categoría: [Categoria]</b>\n\nSelecciona un comando para ver detalles:",
    },
    # --- Help Command Templates ---
    "help_cmd_start": {
        "desc": "Ayuda: /start",
        "vars": [],
        "default": "ℹ️ <b>Comando: /start</b>\n\n📝 <b>Descripción:</b>\nInicia el bot, registra al usuario en la base de datos si es nuevo y muestra el menú principal o las descargas disponibles.\n\n⌨️ <b>Uso:</b> <code>/start</code>\n💡 <b>Ejemplo:</b> <code>/start</code>",
    },
    "help_cmd_help": {
        "desc": "Ayuda: /help",
        "vars": [],
        "default": "ℹ️ <b>Comando: /help</b>\n\n📝 <b>Descripción:</b>\nMuestra el menú de ayuda interactivo con categorías y detalles de comandos.\n\n⌨️ <b>Uso:</b> <code>/help</code>\n💡 <b>Ejemplo:</b> <code>/help</code>",
    },
    "help_cmd_status": {
        "desc": "Ayuda: /status",
        "vars": [],
        "default": "ℹ️ <b>Comando: /status</b>\n\n📝 <b>Descripción:</b>\nMuestra información sobre tu cuenta: nivel de usuario (Free, VIP, etc.), descargas restantes hoy y tiempo para el reinicio.\n\n⌨️ <b>Uso:</b> <code>/status</code>\n💡 <b>Ejemplo:</b> <code>/status</code>",
    },
    "help_cmd_cancel": {
        "desc": "Ayuda: /cancel",
        "vars": [],
        "default": "ℹ️ <b>Comando: /cancel</b>\n\n📝 <b>Descripción:</b>\nCancela cualquier operación en curso, como búsquedas pendientes o navegación de menús, y limpia el estado temporal.\n\n⌨️ <b>Uso:</b> <code>/cancel</code>\n💡 <b>Ejemplo:</b> <code>/cancel</code>",
    },
    "help_cmd_sugerencia": {
        "desc": "Ayuda: /sugerencia",
        "vars": [],
        "default": "ℹ️ <b>Comando: /sugerencia</b>\n\n📝 <b>Descripción:</b>\nEnvía un mensaje directo al equipo de staff. Úsalo para reportar errores, sugerir nuevas funciones o pedir libros específicos. Adjunta detalles para que podamos ayudarte mejor.\n\n⌨️ <b>Uso:</b> <code>/sugerencia &lt;texto&gt;</code>\n💡 <b>Ejemplo:</b> <code>/sugerencia Hola, el libro 'Dune' tiene un error en el capítulo 3.</code>",
    },
    "help_cmd_search": {
        "desc": "Ayuda: /search",
        "vars": [],
        "default": "ℹ️ <b>Comando: /search</b>\n\n📝 <b>Descripción:</b>\nBusca libros en la biblioteca. Puedes buscar por Título, Autor o Serie. Los resultados mostrarán un botón para descargar.\n\nTip: Sé específico para mejores resultados.\n\n⌨️ <b>Uso:</b> <code>/search &lt;término&gt;</code>\n💡 <b>Ejemplo:</b> <code>/search Brandon Sanderson</code>",
    },
    "help_cmd_donar": {
        "desc": "Ayuda: /donar",
        "vars": [],
        "default": "ℹ️ <b>Comando: /donar</b>\n\n📝 <b>Descripción:</b>\nGenera un enlace para realizar donaciones a través de Ko-fi y apoyar el proyecto.\n\n⌨️ <b>Uso:</b> <code>/donar</code>\n💡 <b>Ejemplo:</b> <code>/donar</code>",
    },
    "help_cmd_niveles": {
        "desc": "Ayuda: /niveles",
        "vars": [],
        "default": "ℹ️ <b>Comando: /niveles</b>\n\n📝 <b>Descripción:</b>\nMuestra la tabla de niveles de donación y los beneficios asociados a cada uno (VIP, Premium, etc.).\n\n⌨️ <b>Uso:</b> <code>/niveles</code>\n💡 <b>Ejemplo:</b> <code>/niveles</code>",
    },
    "help_cmd_reglas": {
        "desc": "Ayuda: /reglas",
        "vars": [],
        "default": "ℹ️ <b>Comando: /reglas</b>\n\n📝 <b>Descripción:</b>\nMuestra las reglas configuradas para el grupo actual.\n\n⌨️ <b>Uso:</b> <code>/reglas</code>\n💡 <b>Ejemplo:</b> <code>/reglas</code>",
    },
    "help_cmd_add_user": {
        "desc": "Ayuda: /add_user",
        "vars": [],
        "default": "ℹ️ <b>Comando: /add_user</b>\n\n📝 <b>Descripción:</b>\nAgrega un usuario a la base de datos o actualiza su rol (VIP, Premium, etc.) y duración de beneficios.\n\n⌨️ <b>Uso:</b> <code>/add_user &lt;user_id&gt; &lt;rol&gt; [dias]</code>\n💡 <b>Ejemplo:</b> <code>/add_user 123456789 vip 30</code>",
    },
    "help_cmd_remove_user": {
        "desc": "Ayuda: /remove_user",
        "vars": [],
        "default": "ℹ️ <b>Comando: /remove_user</b>\n\n📝 <b>Descripción:</b>\nRevoca los privilegios especiales de un usuario, volviéndolo al estado 'Free'.\n\n⌨️ <b>Uso:</b> <code>/remove_user &lt;user_id&gt;</code>\n💡 <b>Ejemplo:</b> <code>/remove_user 123456789</code>",
    },
    "help_cmd_set_staff_status": {
        "desc": "Ayuda: /set_staff_status",
        "vars": [],
        "default": "ℹ️ <b>Comando: /set_staff_status</b>\n\n📝 <b>Descripción:</b>\nOtorga o revoca el estado de 'Staff' a un usuario. Cambia el [Rol] funcional.\n\n⌨️ <b>Uso:</b> <code>/set_staff_status &lt;user_id&gt; &lt;label&gt;</code>\n💡 <b>Ejemplo:</b> <code>/set_staff_status 123456789 Editor Jefe</code>",
    },
    "help_cmd_set_apodo": {
        "desc": "Ayuda: /set_apodo",
        "vars": [],
        "default": "ℹ️ <b>Comando: /set_apodo</b>\n\n📝 <b>Descripción:</b>\nEstablece un apodo personalizado para un usuario, accesible via [Apodo].\n\n⌨️ <b>Uso:</b> <code>/set_apodo &lt;user_id&gt; &lt;apodo&gt;</code>\n💡 <b>Ejemplo:</b> <code>/set_apodo 123456789 El Charly</code>",
    },
    "help_cmd_reset": {
        "desc": "Ayuda: /reset",
        "vars": [],
        "default": "ℹ️ <b>Comando: /reset</b>\n\n📝 <b>Descripción:</b>\nReinicia el contador de descargas diario de un usuario específico a 0.\n\n⌨️ <b>Uso:</b> <code>/reset &lt;user_id&gt;</code>\n💡 <b>Ejemplo:</b> <code>/reset 123456789</code>",
    },
    "help_cmd_id": {
        "desc": "Ayuda: /id",
        "vars": [],
        "default": "ℹ️ <b>Comando: /id</b>\n\n📝 <b>Descripción:</b>\nMuestra el ID numérico del chat actual y del usuario que envía el mensaje.\n\n⌨️ <b>Uso:</b> <code>/id</code>\n💡 <b>Ejemplo:</b> <code>/id</code>",
    },
    "help_cmd_setlog": {
        "desc": "Ayuda: /setlog",
        "vars": [],
        "default": "ℹ️ <b>Comando: /setlog</b>\n\n📝 <b>Descripción:</b>\nCambia el nivel de verbosidad de los logs del sistema en tiempo real.\n\n⌨️ <b>Uso:</b> <code>/setlog &lt;INFO|DEBUG|WARNING&gt;</code>\n💡 <b>Ejemplo:</b> <code>/setlog DEBUG</code>",
    },
    "help_cmd_stats": {
        "desc": "Ayuda: /stats",
        "vars": [],
        "default": "ℹ️ <b>Comando: /stats</b>\n\n📝 <b>Descripción:</b>\nMuestra estadísticas diarias del sistema o lista usuarios por rol (Admin/Staff only).\n\n⌨️ <b>Uso:</b> <code>/stats [rol]</code>\n💡 <b>Ejemplo:</b> <code>/stats vip</code>",
    },
    "help_cmd_evil": {
        "desc": "Ayuda: /evil",
        "vars": [],
        "default": "ℹ️ <b>Comando: /evil</b>\n\n📝 <b>Descripción:</b>\nInicia el modo privado (Evil) solicitando contraseña.\n\n⌨️ <b>Uso:</b> <code>/evil</code>\n💡 <b>Ejemplo:</b> <code>/evil</code>",
    },
    "help_cmd_set_auto_delete_time": {
        "desc": "Ayuda: /set_auto_delete_time",
        "vars": [],
        "default": "ℹ️ <b>Comando: /set_auto_delete_time</b>\n\n📝 <b>Descripción:</b>\nConfigura el tiempo (en minutos) antes de que los libros enviados se eliminen automáticamente.\n\n⌨️ <b>Uso:</b> <code>/set_auto_delete_time &lt;minutos&gt;</code>\n💡 <b>Ejemplo:</b> <code>/set_auto_delete_time 60</code>",
    },
    "help_cmd_debug_state": {
        "desc": "Ayuda: /debug_state",
        "vars": [],
        "default": "ℹ️ <b>Comando: /debug_state</b>\n\n📝 <b>Descripción:</b>\nMuestra el estado interno completo de un usuario: historial de navegación OPDS temporal, buffer de descarga y variables de sesión. Útil para diagnosticar problemas de navegación.\n\n⌨️ <b>Uso:</b> <code>/debug_state &lt;user_id&gt;</code>\n💡 <b>Ejemplo:</b> <code>/debug_state 123456789</code>",
    },
    "help_cmd_reset_msge": {
        "desc": "Ayuda: /reset_msge",
        "vars": [],
        "default": "ℹ️ <b>Comando: /reset_msge</b>\n\n📝 <b>Descripción:</b>\nRestablece una plantilla a su valor original por defecto, borrando cualquier personalización hecha con /add_msge.\n\n⌨️ <b>Uso:</b> <code>/reset_msge &lt;slug&gt;</code>\n💡 <b>Ejemplo:</b> <code>/reset_msge search_instructions_legacy</code>",
    },
    "help_cmd_update_system": {
        "desc": "Ayuda: /update_system",
        "vars": [],
        "default": "ℹ️ <b>Comando: /update_system</b>\n\n📝 <b>Descripción:</b>\nEjecuta un 'git pull' y reinicia el contenedor para actualizar el bot. Use 'force' para sobrescribir cambios locales.\n\n⌨️ <b>Uso:</b> <code>/update_system [force]</code>\n💡 <b>Ejemplo:</b> <code>/update_system force</code>",
    },
    "help_cmd_plugins": {
        "desc": "Ayuda: /plugins",
        "vars": [],
        "default": "ℹ️ <b>Comando: /plugins</b>\n\n📝 <b>Descripción:</b>\nLista todos los plugins cargados y sus versiones.\n\n⌨️ <b>Uso:</b> <code>/plugins</code>\n💡 <b>Ejemplo:</b> <code>/plugins</code>",
    },
    "help_cmd_set_price": {
        "desc": "Ayuda: /set_price",
        "vars": [],
        "default": "ℹ️ <b>Comando: /set_price</b>\n\n📝 <b>Descripción:</b>\nConfigura el precio base para los niveles de donación.\n\n⌨️ <b>Uso:</b> <code>/set_price &lt;nivel&gt; &lt;monto&gt;</code>\n💡 <b>Ejemplo:</b> <code>/set_price vip 10</code>",
    },
    "help_cmd_backup_db": {
        "desc": "Ayuda: /backup_db",
        "vars": [],
        "default": "ℹ️ <b>Comando: /backup_db</b>\n\n📝 <b>Descripción:</b>\nGenera y envía un archivo de respaldo de la base de datos principal.\n\n⌨️ <b>Uso:</b> <code>/backup_db</code>\n💡 <b>Ejemplo:</b> <code>/backup_db</code>",
    },
    "help_cmd_restore_db": {
        "desc": "Ayuda: /restore_db",
        "vars": [],
        "default": "ℹ️ <b>Comando: /restore_db</b>\n\n📝 <b>Descripción:</b>\nRestaura la base de datos desde un archivo adjunto. Debe responder al mensaje del archivo.\n\n⌨️ <b>Uso:</b> Responder a archivo con <code>/restore_db</code>\n💡 <b>Ejemplo:</b> <code>/restore_db</code>",
    },
    "help_cmd_import_history": {
        "desc": "Ayuda: /import_history",
        "vars": [],
        "default": "ℹ️ <b>Comando: /import_history</b>\n\n📝 <b>Descripción:</b>\nImporta historial de publicaciones desde un JSON exportado de Telegram.\n\n⌨️ <b>Uso:</b> Responder a archivo JSON con <code>/import_history</code>\n💡 <b>Ejemplo:</b> <code>/import_history</code>",
    },
    "help_cmd_latest_books": {
        "desc": "Ayuda: /latest_books",
        "vars": [],
        "default": "ℹ️ <b>Comando: /latest_books</b>\n\n📝 <b>Descripción:</b>\nMuestra una lista de los últimos libros añadidos al historial de publicaciones.\n\n⌨️ <b>Uso:</b> <code>/latest_books [chat_id]</code>\n💡 <b>Ejemplo:</b> <code>/latest_books -100123456</code>",
    },
    "help_cmd_clear_history": {
        "desc": "Ayuda: /clear_history",
        "vars": [],
        "default": "ℹ️ <b>Comando: /clear_history</b>\n\n📝 <b>Descripción:</b>\nElimina todos los registros de libros publicados del historial. Requiere confirmación.\n\n⌨️ <b>Uso:</b> <code>/clear_history</code>\n💡 <b>Ejemplo:</b> <code>/clear_history</code>",
    },
    "help_cmd_export_db": {
        "desc": "Ayuda: /export_db",
        "vars": [],
        "default": "ℹ️ <b>Comando: /export_db</b>\n\n📝 <b>Descripción:</b>\nExporta el mapeo de IDs a base de datos en formato CSV.\n\n⌨️ <b>Uso:</b> <code>/export_db</code>\n💡 <b>Ejemplo:</b> <code>/export_db</code>",
    },
    "help_cmd_export_history": {
        "desc": "Ayuda: /export_history",
        "vars": [],
        "default": "ℹ️ <b>Comando: /export_history</b>\n\n📝 <b>Descripción:</b>\nExporta el historial completo de libros publicados a un archivo CSV.\n\n⌨️ <b>Uso:</b> <code>/export_history</code>\n💡 <b>Ejemplo:</b> <code>/export_history</code>",
    },
    "help_cmd_add_msge": {
        "desc": "Ayuda: /add_msge",
        "vars": [],
        "default": "ℹ️ <b>Comando: /add_msge</b>\n\n📝 <b>Descripción:</b>\nGuarda el contenido del mensaje al que se responde para usarlo posteriormente. Requiere un ID único (slug).\n\n⌨️ <b>Uso:</b> Responder con <code>/add_msge &lt;slug&gt;</code>\n💡 <b>Ejemplo:</b> <code>/add_msge bienvenida_v1</code>",
    },
    "help_cmd_list_msge": {
        "desc": "Ayuda: /list_msge",
        "vars": [],
        "default": "ℹ️ <b>Comando: /list_msge</b>\n\n📝 <b>Descripción:</b>\nLista todos los mensajes guardados. Si se da un ID, muestra una vista previa de ese mensaje.\n\n⌨️ <b>Uso:</b> <code>/list_msge [slug]</code>\n💡 <b>Ejemplo:</b> <code>/list_msge bienvenida_v1</code>",
    },
    "help_cmd_send_msge": {
        "desc": "Ayuda: /send_msge",
        "vars": [],
        "default": "ℹ️ <b>Comando: /send_msge</b>\n\n📝 <b>Descripción:</b>\nEnvía una copia exacta de un mensaje guardado a un chat específico.\n\n⌨️ <b>Uso:</b> <code>/send_msge &lt;slug&gt; &lt;chat_id&gt;</code>\n💡 <b>Ejemplo:</b> <code>/send_msge bienvenida_v1 -1001234567</code>",
    },
    "help_cmd_saludo": {
        "desc": "Ayuda: /saludo",
        "vars": [],
        "default": "ℹ️ <b>Comando: /saludo</b>\n\n📝 <b>Descripción:</b>\nEnvía un mensaje de texto o un mensaje guardado a un chat.\n\n⌨️ <b>Uso:</b> <code>/saludo &lt;chat_id&gt; [thread_id] &lt;texto|slug&gt;</code>\n💡 <b>Ejemplo:</b> <code>/saludo -100123 Hola!</code>\n💡 <b>Ejemplo Topic:</b> <code>/saludo -100123 456 Hola!</code>",
    },
    "help_cmd_set_welcome": {
        "desc": "Ayuda: /set_welcome",
        "vars": [],
        "default": "ℹ️ <b>Comando: /set_welcome</b>\n\n📝 <b>Descripción:</b>\nDefine qué mensaje guardado se usará como bienvenida automática global (si aplica).\n\n⌨️ <b>Uso:</b> <code>/set_welcome &lt;slug|off&gt;</code>\n💡 <b>Ejemplo:</b> <code>/set_welcome bienvenida_v1</code>",
    },
    "help_cmd_templates": {
        "desc": "Ayuda: /templates",
        "vars": [],
        "default": "ℹ️ <b>Comando: /templates</b>\n\n📝 <b>Descripción:</b>\nMuestra todas las plantillas de mensajes registradas y las variables que aceptan.\n\n⌨️ <b>Uso:</b> <code>/templates</code>\n💡 <b>Ejemplo:</b> <code>/templates</code>",
    },
    "help_cmd_set_var": {
        "desc": "Ayuda: /set_var",
        "vars": [],
        "default": "ℹ️ <b>Comando: /set_var</b>\n\n📝 <b>Descripción:</b>\nCrea o actualiza una variable global que puede usarse en cualquier plantilla con [NombreVariable].\n\n⌨️ <b>Uso:</b> <code>/set_var &lt;Variable&gt; &lt;Valor&gt;</code>\n💡 <b>Ejemplo:</b> <code>/set_var CanalOficial https://t.me/mi_canal</code>",
    },
    "help_cmd_del_var": {
        "desc": "Ayuda: /del_var",
        "vars": [],
        "default": "ℹ️ <b>Comando: /del_var</b>\n\n📝 <b>Descripción:</b>\nBorra una variable global personalizada.\n\n⌨️ <b>Uso:</b> <code>/del_var &lt;Variable&gt;</code>\n💡 <b>Ejemplo:</b> <code>/del_var CanalOficial</code>",
    },
    "help_cmd_vars": {
        "desc": "Ayuda: /vars",
        "vars": [],
        "default": "ℹ️ <b>Comando: /vars</b>\n\n📝 <b>Descripción:</b>\nMuestra todas las variables globales disponibles (del sistema y personalizadas). Alías: /template_vars\n\n⌨️ <b>Uso:</b> <code>/vars</code>\n💡 <b>Ejemplo:</b> <code>/vars</code>",
    },
    "help_cmd_template_vars": {
        "desc": "Ayuda: /template_vars",
        "vars": [],
        "default": "ℹ️ <b>Comando: /template_vars</b>\n\n📝 <b>Descripción:</b>\nLista las variables globales disponibles (como [Nombre], [Fecha]) para usar en cualquier plantilla.\n\n⌨️ <b>Uso:</b> <code>/template_vars</code>\n💡 <b>Ejemplo:</b> <code>/template_vars</code>",
    },
    "help_cmd_status_links": {
        "desc": "Ayuda: /status_links",
        "vars": [],
        "default": "ℹ️ <b>Comando: /status_links</b>\n\n📝 <b>Descripción:</b>\nMuestra estadísticas sobre los enlaces generados y su estado.\n\n⌨️ <b>Uso:</b> <code>/status_links</code>\n💡 <b>Ejemplo:</b> <code>/status_links</code>",
    },
    "help_cmd_link_list": {
        "desc": "Ayuda: /link_list",
        "vars": [],
        "default": "ℹ️ <b>Comando: /link_list</b>\n\n📝 <b>Descripción:</b>\nMuestra una lista de los enlaces generados recientemente.\n\n⌨️ <b>Uso:</b> <code>/link_list</code>\n💡 <b>Ejemplo:</b> <code>/link_list</code>",
    },
    "help_cmd_purge_link": {
        "desc": "Ayuda: /purge_link",
        "vars": [],
        "default": "ℹ️ <b>Comando: /purge_link</b>\n\n📝 <b>Descripción:</b>\nElimina un enlace generado de la base de datos.\n\n⌨️ <b>Uso:</b> <code>/purge_link &lt;id&gt;</code>\n💡 <b>Ejemplo:</b> <code>/purge_link 123</code>",
    },
    "help_cmd_authorize_group": {
        "desc": "Ayuda: /authorize_group",
        "vars": [],
        "default": "ℹ️ <b>Comando: /authorize_group</b>\n\n📝 <b>Descripción:</b>\nAutoriza al bot a funcionar en el grupo especificado.\n\n⌨️ <b>Uso:</b> <code>/authorize_group [chat_id]</code>\n💡 <b>Ejemplo:</b> <code>/authorize_group -100123456</code>",
    },
    "help_cmd_revoke_group": {
        "desc": "Ayuda: /revoke_group",
        "vars": [],
        "default": "ℹ️ <b>Comando: /revoke_group</b>\n\n📝 <b>Descripción:</b>\nRevoca la autorización del bot en un grupo.\n\n⌨️ <b>Uso:</b> <code>/revoke_group [chat_id]</code>\n💡 <b>Ejemplo:</b> <code>/revoke_group</code>",
    },
    "help_cmd_set_group_welcome": {
        "desc": "Ayuda: /set_group_welcome",
        "vars": [],
        "default": "ℹ️ <b>Comando: /set_group_welcome</b>\n\n📝 <b>Descripción:</b>\nConfigura un mensaje de bienvenida personalizado para este grupo. Debes crear el mensaje primero con /add_msge.\n\n✨ <b>Personalización:</b> Si el mensaje guardado contiene <code>[Nombre]</code>, será reemplazado por el nombre del usuario nuevo.\n\n⌨️ <b>Uso:</b> <code>/set_group_welcome &lt;slug&gt;</code>\n💡 <b>Ejemplo:</b> <code>/set_group_welcome bienvenida_grupo</code>",
    },
}

# Global variables available in ALL templates
GLOBAL_VARIABLES = {
    "Nombre": "Nombre del usuario (First Name)",
    "Alias": "Username del usuario (sin @)",
    "ID": "ID numérico del usuario",
    "Fecha": "Fecha actual (YYYY-MM-DD)",
    "Hora": "Hora actual (HH:MM)",
    "VersionBot": "Versión actual del bot (ej: v3.7.2)",
}


class CustomMessagesPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "custom_messages"

    @property
    def version(self) -> str:
        return "1.3.0"

    @property
    def description(self) -> str:
        return "Permite guardar y reutilizar mensajes. Incluye bienvenida automática y comando saludo mejorado."

    def __init__(self):
        self.engine = None
        self.Session = None
        self.enabled = False
        self._global_vars_cache = {}

    async def initialize(self, bot_instance) -> bool:
        # Check env var directly or via os.environ if not in config object yet
        # Assuming config loads .env but we appended to it, might need reload or just os.getenv
        self.enabled = os.getenv("ENABLE_CUSTOM_MESSAGES", "False").lower() == "true"

        if not self.enabled:
            logger.info(
                "Plugin CustomMessages desactivado por configuración (ENABLE_CUSTOM_MESSAGES=False)."
            )
            return False

        # Initialize DB
        db_url = config.DATABASE_URL
        if not db_url:
            # Fallback to local sqlite like other services
            db_path = os.path.join("data", "custom_messages.db")
            db_url = f"sqlite:///{db_path}"

        try:
            self.engine = create_engine(db_url, future=True)
            Base.metadata.create_all(self.engine)

            # Migration: Ensure text_content column exists
            with self.engine.connect() as conn:
                try:
                    # Check if column exists by selecting it? Or just try adding it and ignore error
                    # SQLite doesn't support IF NOT EXISTS in ADD COLUMN effectively in all versions,
                    # but easiest is to try query it, catch error, then add.
                    # Or check pragma table_info.
                    if "sqlite" in db_url:
                        result = conn.execute(
                            text("PRAGMA table_info(stored_messages)")
                        )
                        columns = [
                            row[1] for row in result.fetchall()
                        ]  # row[1] is name
                        if "text_content" not in columns:
                            logger.info("Migrating DB: Adding text_content column...")
                            conn.execute(
                                text(
                                    "ALTER TABLE stored_messages ADD COLUMN text_content TEXT"
                                )
                            )
                    else:
                        # Postgres logic if using it (unlikely for this plugin default path but good practice)
                        pass
                except Exception as ex:
                    logger.warning(
                        f"Migration check failed (might be already up to date): {ex}"
                    )

            self.Session = sessionmaker(bind=self.engine)
            # Load global vars to cache
            self._refresh_global_vars_cache()
            logger.info("Plugin CustomMessages: Base de datos inicializada.")

        except Exception as e:
            logger.error(f"Error inicializando BD del plugin: {e}")
            return False

        # Register Handlers Manually
        # bot_instance is actually 'app' from main.py, so it has .add_handler
        try:
            app = bot_instance
            app.add_handler(CommandHandler("add_msge", self.add_msge))
            app.add_handler(CommandHandler("reset_msge", self.reset_msge))
            app.add_handler(CommandHandler("list_msge", self.list_msge))
            app.add_handler(CommandHandler("send_msge", self.send_msge))
            app.add_handler(CommandHandler("saludo", self.saludo))
            app.add_handler(CommandHandler("set_welcome", self.set_welcome))

            app.add_handler(CommandHandler("templates", self.templates))
            app.add_handler(
                CommandHandler("template", self.templates)
            )  # Alias requested by user
            app.add_handler(CommandHandler("template_vars", self.vars))  # Legacy alias
            app.add_handler(CommandHandler("vars", self.vars))
            app.add_handler(CommandHandler("set_var", self.set_var))
            app.add_handler(CommandHandler("del_var", self.del_var))

            app.add_handler(
                CallbackQueryHandler(self.templates_callback, pattern=r"^templates\|")
            )

            # ChatMemberHandler for welcome message
            # MY_CHAT_MEMBER is triggered when bot is added/promoted/removed
            app.add_handler(
                ChatMemberHandler(
                    self.welcome_handler, ChatMemberHandler.MY_CHAT_MEMBER
                )
            )

            logger.info("Plugin CustomMessages: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin: {e}")
            return False

    async def cleanup(self) -> None:
        logger.info("Plugin CustomMessages limpiando recursos.")

    # --- Database Helpers ---
    def _save_message(self, slug, chat_id, message_id, description=None):
        with self.Session() as session:
            msg = session.get(StoredMessage, slug)
            if msg:
                msg.source_chat_id = chat_id
                msg.source_message_id = message_id
                msg.description = description
                # Si description contiene el texto real (pasado desde add_msge), lo guardamos en text_content tambien
                msg.text_content = description

            else:
                msg = StoredMessage(
                    slug=slug,
                    source_chat_id=chat_id,
                    source_message_id=message_id,
                    description=description,
                    text_content=description,  # Usamos description para pasar el texto como descripción/contenido
                )
                session.add(msg)

            session.commit()

    def _get_message(self, slug):
        with self.Session() as session:
            return session.get(StoredMessage, slug)

    def _list_messages(self):
        with self.Session() as session:
            return session.query(StoredMessage).all()

    def _set_setting(self, key, value):
        with self.Session() as session:
            s = session.get(PluginSettings, key)
            if s:
                s.value = value
            else:
                s = PluginSettings(key=key, value=value)
                session.add(s)
            session.commit()

    def _get_setting(self, key):
        with self.Session() as session:
            s = session.get(PluginSettings, key)
            return s.value if s else None

    def _refresh_global_vars_cache(self):
        with self.Session() as session:
            vars_db = session.query(GlobalVariable).all()
            self._global_vars_cache = {v.key: v.value for v in vars_db}

    def _set_global_var(self, key, value):
        with self.Session() as session:
            v = session.get(GlobalVariable, key)
            if v:
                v.value = value
            else:
                v = GlobalVariable(key=key, value=value)
                session.add(v)
            session.commit()
        self._refresh_global_vars_cache()

    def _del_global_var(self, key):
        with self.Session() as session:
            v = session.get(GlobalVariable, key)
            if v:
                session.delete(v)
                session.commit()
        self._refresh_global_vars_cache()

    async def _get_extended_user_context(self, user) -> Dict[str, Any]:
        """
        Calcula variables dinámicas del usuario (Nivel, Descargas, etc.)
        Solo se llama si el template las requiere.
        """
        from services.user_service import get_effective_user
        from core.state_manager import state_manager
        from datetime import datetime, timedelta

        uid = user.id
        user_data = await get_effective_user(uid)
        st = state_manager.get_user_state(uid)

        # Mapping roles to display names requested by User
        # free -> Lector
        # white -> Patrocinador
        # vip -> VIP
        # premium -> Premium
        # staff -> STAFF
        # admin -> Administrador
        roles_display_map = {
            "admin": "Administrador",
            "staff": "STAFF",
            "premium": "Premium",
            "vip": "VIP",
            "white": "Patrocinador",
            "free": "Lector",
            "banned": "Baneado",
        }

        role_key = user_data.get("role", "free")
        expires_at = user_data.get("expires_at")

        if isinstance(role_key, str):
            role_key = role_key.strip().lower()

        # [Nivel] uses this map directly
        nivel_display = roles_display_map.get(role_key, "Lector")

        # [Rol] - Sólo si hay custom status real (user provided label via /set_staff_status)
        rol_funcional = user_data.get("custom_status")

        # Fallback legacy logic for user_level variable (if used elsewhere, but here we focus on vars)
        user_level = rol_funcional if rol_funcional else nivel_display

        # Max Download Logic
        if role_key in ("admin", "staff", "premium", "banned"):
            max_dl = None
        elif role_key == "vip":
            max_dl = config.VIP_DOWNLOADS_PER_DAY
        elif role_key == "white":
            max_dl = config.WHITELIST_DOWNLOADS_PER_DAY
        else:
            max_dl = config.MAX_DOWNLOADS_PER_DAY

        # Used / Remaining
        used = st.get("downloads_used", 0)

        if max_dl is None:
            if role_key == "banned":
                descargas_text = "⛔ Acceso denegado"
            else:
                descargas_text = "✅ Descargas ilimitadas"
        else:
            remaining = max_dl - used
            descargas_text = (
                f"⚡️ Te quedan {remaining if remaining>0 else 0} descargas por día"
            )

        # Reset Time
        reset_time_str = None
        if max_dl is not None:
            now = datetime.now()
            next_midnight = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            time_left = next_midnight - now
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            reset_time_str = f"{hours}h {minutes}m"

        # Expires
        expire_str = None
        if expires_at:
            fmt = "%d/%m/%Y %H:%M" if role_key == "banned" else "%d/%m/%Y"
            expire_str = expires_at.strftime(fmt)

        # [Nivel] -> External display name for System Role (Admin, Staff, etc.)
        # [Rol] -> Custom Status Label (functional role)
        # [Apodo] -> Nickname

        system_role_display = nivel_display  # [Nivel] uses strict system role map

        custom_status = user_level  # This variable 'user_level' holds status_label from get_effective_user which is custom_status or role.capitalize()
        # Wait, get_effective_user returns:
        # role: raw role
        # status_label: custom_status IF present, ELSE role.capitalize()
        # So 'user_level' variable currently holds `status_label`.
        # User wants [Rol] to be the FUNCTION (custom defined).
        # And [Nivel] to be the SYSTEM role.

        # So:
        # [Nivel] = system_role_display
        # [Rol] = user_data.get("status_label") (which is the custom label)
        # BUT if custom doesn't exist, status_label is role.capitalize().
        # If user wants [Rol] to be SPECIFICALLY the custom function, we should use that.
        # However, for consistency, let's use the status_label which defaults to role name if no custom label.

        rol_funcional = user_data.get(
            "custom_status"
        )  # [Rol] - Sólo si hay custom status real
        apodo = user_data.get("nickname")  # [Apodo] - None si no existe

        return {
            "Nivel": system_role_display,
            "Rol": rol_funcional,
            "Apodo": apodo,
            "Descargas": descargas_text,
            "ResetTime": reset_time_str,
            "Expires": expire_str,
        }

    # --- Helper Methods for Template System ---

    async def get_text(
        self, slug: str, default_text: str = None, user=None, **replacements
    ) -> str:
        """
        Recupera el texto de un mensaje guardado por su slug.
        Orden de prioridad:
        1. Base de Datos (Personalizado)
        2. default_text (Argumento legado, opcional)
        3. TEMPLATE_REGISTRY explicit default
        4. Cadena vacía

        Realiza el reemplazo de variables en el formato [Variable].
        """
        msg = self._get_message(slug.lower())

        final_text = None
        if msg and msg.text_content:
            final_text = msg.text_content

        # Fallbacks
        if not final_text:
            if default_text:
                final_text = default_text
            else:
                # Look in registry
                entry = TEMPLATE_REGISTRY.get(slug)
                if entry and "default" in entry:
                    final_text = entry["default"]

        if not final_text:
            return ""

        # 0. Admin Global Vars (System-wide)
        vars_to_use = self._global_vars_cache.copy()  # Start with admin globals

        # 1. Inject System Variables (Time/Version)
        from datetime import datetime

        now = datetime.now()
        vars_to_use["Fecha"] = now.strftime("%Y-%m-%d")
        vars_to_use["Hora"] = now.strftime("%H:%M")

        from utils.helpers import get_version_string

        vars_to_use["VersionBot"] = get_version_string()

        # 2. Inject User Variables (Context)
        if user:
            vars_to_use["Nombre"] = user.first_name or "Usuario"
            vars_to_use["Alias"] = user.username
            vars_to_use["ID"] = str(user.id)

            # 2.1 Auto-Inject Extended User Stats if needed
            # We check if keys are present in final_text to avoid expensive DB calls
            # 2.1 Auto-Inject Extended User Stats if needed
            # We check if keys are present in final_text to avoid expensive DB calls
            needed_keys = {
                "[Nivel]",
                "[Descargas]",
                "[ResetTime]",
                "[Expires]",
                "[Rol]",
                "[Apodo]",
            }
            # Simple string check (fast)
            if any(k in final_text for k in needed_keys):
                extended_context = await self._get_extended_user_context(user)
                vars_to_use.update(extended_context)

        # 3. Explicit Replacements (Arguments) - Override everything
        vars_to_use.update(replacements)

        # 4. Conditional Logic (Sync)
        def replacer(match):
            key = match.group(1)
            content = match.group(2)
            val = vars_to_use.get(key)
            is_true = bool(val)
            if val == 0 or val == "0":
                is_true = True
            return content if is_true else ""

        final_text = re.sub(
            r"{{if\s+(\w+)}}(.*?){{endif}}", replacer, final_text, flags=re.DOTALL
        )

        # 5. Variable Replacement
        for key, value in vars_to_use.items():
            placeholder = f"[{key}]"
            safe_value = str(value)
            final_text = final_text.replace(placeholder, safe_value)

        return final_text

    # --- Handlers ---

    async def add_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if not update.message.reply_to_message:
            await update.message.reply_text(
                "❌ Debes responder al mensaje que quieres guardar."
            )
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Uso: Responder al mensaje + /add_msge <id_unico>"
            )
            return

        slug = context.args[0].lower()
        original_msg = update.message.reply_to_message

        # Guardar source_chat_id y source_message_id
        # IMPORTANTE: Si es un grupo, source_chat_id es el id del grupo.
        # copy_message necesita permisos para ver ese chat.

        try:
            # Capturar texto o caption para guardarlo
            content_text = (
                original_msg.text_html
                or original_msg.caption_html
                or "Mensaje Multimedia"
            )

            self._save_message(
                slug,
                original_msg.chat_id,
                original_msg.message_id,
                description=content_text,  # Pasamos el texto como descripción/contenido
            )

            await update.message.reply_text(
                f"✅ Mensaje guardado como <code>{slug}</code>.", parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error guardando mensaje: {e}")
            await update.message.reply_text("❌ Error al guardar en base de datos.")

    async def list_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if context.args:
            # Preview mode
            slug = context.args[0].lower()
            msg = self._get_message(slug)

            # Logic to find text to preview:
            # 1. DB Content
            # 2. Registry Default
            text_to_preview = None
            source = "database"

            if msg and msg.text_content:
                text_to_preview = msg.text_content
            else:
                # Check registry
                entry = TEMPLATE_REGISTRY.get(slug)
                if entry and "default" in entry:
                    text_to_preview = entry["default"]
                    source = "default"

            if not text_to_preview:
                await update.message.reply_text(
                    "❌ Mensaje no encontrado (ni en base de datos ni por defecto)."
                )
                return

            # Check for optional target_uid for variable replacement testing
            target_uid = None
            if len(context.args) > 1:
                try:
                    target_uid = int(context.args[1])
                except ValueError:
                    pass

            # If we have text content (either from DB or default) and target for replacement
            if target_uid:
                try:
                    # Get user info to replace [Nombre]
                    try:
                        member = await context.bot.get_chat_member(
                            update.effective_chat.id, target_uid
                        )
                        user = member.user
                    except Exception:
                        chat = await context.bot.get_chat(target_uid)
                        user = chat

                    first_name = user.first_name if user else "Usuario"
                    safe_name = html.escape(first_name)

                    # Use get_text. Note: we don't pass default_text because we already resolved it or it's in registry
                    # But actually get_text will resolve it again if we pass just the slug.
                    # It's better to rely on get_text's internal resolution to be consistent.
                    text_sent = await self.get_text(slug, user=user)

                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text_sent,
                        parse_mode=ParseMode.HTML,
                        message_thread_id=get_thread_id(update),
                    )
                    return
                except Exception as e:
                    logger.warning(
                        f"Failed to test vars in list_msge: {e} - Falling back to simple preview"
                    )

            # Simple preview (raw text) or copy if it was a multimedia message in DB
            # If source is default, we just send message.
            # If source is DB and has text_content, we send message.
            # If source is DB and multimedia (no text_content but has IDs), we copy.

            if source == "default" or (msg and msg.text_content):
                # Send text representation
                prefix = (
                    "⚠️ <b>Mensaje por defecto:</b>\n\n"
                    if source == "default"
                    else f"📂 <b>Mensaje Personalizado ({slug}):</b>\n\n"
                )

                # Render keys to show placeholders? Or just raw?
                # Let's show raw but maybe escaped to not break HTML?
                # Actually user wants to see the structure.
                # Use get_text with NO user to see raw placeholders?
                # get_text replaces global vars always if we don't pass them? No, only if user object passed?
                # let's just show text_to_preview raw.

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"{prefix}{html.escape(text_to_preview)}",
                    parse_mode=ParseMode.HTML,
                    message_thread_id=get_thread_id(update),
                )
            elif msg:
                # Multimedia copy fallback
                try:
                    await context.bot.copy_message(
                        chat_id=update.effective_chat.id,
                        from_chat_id=msg.source_chat_id,
                        message_id=msg.source_message_id,
                        message_thread_id=get_thread_id(update),
                    )
                except Exception as e:
                    await update.message.reply_text(
                        f"❌ Error al previsualizar (¿Mensaje original borrado?): {e}"
                    )
            return

        # List mode
        # Show both DB keys and Registry keys
        msgs_db = self._list_messages()
        db_slugs = {m.slug for m in msgs_db}
        registry_slugs = set(TEMPLATE_REGISTRY.keys())

        all_slugs = sorted(db_slugs.union(registry_slugs))

        if not all_slugs:
            await update.message.reply_text("📭 No hay mensajes disponibles.")
            return

        text = "📂 <b>Mensajes Disponibles:</b>\n\n"
        for s in all_slugs:
            icon = "🔹"
            extra = ""
            if s in db_slugs:
                icon = "💾"  # Personalizado
            elif s in registry_slugs:
                icon = "📄"  # Por defecto

            text += f"{icon} <code>{s}</code>{extra}\n"

        text += "\n💾 = Personalizado, 📄 = Por defecto"
        text += "\nUsa <code>/list_msge &lt;id&gt;</code> para ver contenido."
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

    async def send_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if len(context.args) < 2:
            await update.message.reply_text("❌ Uso: /send_msge <id> <chat_id>")
            return

        slug = context.args[0].lower()
        target_chat_id = context.args[1]

        # Try to resolve via get_text first to see if we have text content
        # But send_msge is often used for multimedia copies...
        # If we have a DB entry with multimedia, copy it.
        # If we have only text (default or DB), send it.

        msg = self._get_message(slug)
        entry = TEMPLATE_REGISTRY.get(slug)

        has_content = (msg and msg.text_content) or (entry and "default" in entry)

        if not msg and not has_content:
            await update.message.reply_text("❌ Mensaje no encontrado.")
            return

        try:
            if msg and not msg.text_content:
                # Pure multimedia copy
                await context.bot.copy_message(
                    chat_id=target_chat_id,
                    from_chat_id=msg.source_chat_id,
                    message_id=msg.source_message_id,
                )
            else:
                # Text based (Default or DB text)
                # We can't really "send" a template without variables replaced...
                # This command is raw. Maybe just send the text?
                # Or try to render with empty vars?
                text_to_send = await self.get_text(slug)
                await context.bot.send_message(
                    chat_id=target_chat_id, text=text_to_send, parse_mode=ParseMode.HTML
                )

            await update.message.reply_text(f"✅ Enviado a {target_chat_id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error enviando: {e}")

    async def saludo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /saludo <chat_id> [thread_id] <id_guardado | texto libre>
        """
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        # Simple parsing for backward compatibility
        # But we need to support /saludo <chat_id> <slug> vs /saludo <chat_id> <text>
        # And now: /saludo <chat_id> <thread_id> <slug|text>

        args = context.args
        if not args or len(args) < 2:
            await update.message.reply_text(
                "❌ Uso: /saludo <chat_id> [thread_id] <id_mensaje | texto>\n"
                "Ej: /saludo -100123 welcome_v1\n"
                "Ej Topic: /saludo -100123 445 welcome_v1"
            )
            return

        target_chat_id = args[0]

        # Check if second argument is a thread_id (integer)
        # Note: Chat IDs usually start with -100... but topic IDs are small positive integers
        # However, we must be careful not to confuse a slug starting with a number as a thread ID?
        # Generally thread_ids are integers. Slugs are strings.
        # But if slug is "123_msg", int("123_msg") fails.
        # If slug IS "123", then it's ambiguous. But slugs are usually names.

        possible_thread_id = args[1]
        message_thread_id = None
        content_start_index = 1

        try:
            # Try to parse second arg as thread ID if it looks like a positive integer
            # Negative integers are likely chat IDs (but we already got chat_id).
            tid = int(possible_thread_id)
            if tid > 0:
                message_thread_id = tid
                content_start_index = 2
        except ValueError:
            pass

        # Reconstruct content from the rest of arguments
        if len(args) <= content_start_index:
            await update.message.reply_text("❌ Falta el contenido del mensaje.")
            return

        # Re-join the original text logic is tricky because context.args strips quotes sometimes or we lose spaces.
        # Ideally we want the raw text after the command and IDs.
        # update.message.text: "/saludo -100123 445 Hola mundo"
        # We can reconstruct roughly or try to parse from raw text.
        # Let's use the args join which is safer than string slicing raw text with variable length params.

        content = " ".join(args[content_start_index:])

        # Check if content matches a slug
        slug = content.strip().lower()

        # Check if it exists as a template (DB or Default)
        msg_db = self._get_message(slug)
        is_template = (slug in TEMPLATE_REGISTRY) or (msg_db is not None)

        if is_template:
            # It IS a stored message or template
            try:
                if msg_db and not msg_db.text_content:
                    # Multimedia copy
                    await context.bot.copy_message(
                        chat_id=target_chat_id,
                        from_chat_id=msg_db.source_chat_id,
                        message_id=msg_db.source_message_id,
                        message_thread_id=message_thread_id,
                    )
                else:
                    # Text Message (Template)
                    text_to_send = await self.get_text(slug)
                    await context.bot.send_message(
                        chat_id=target_chat_id,
                        text=text_to_send,
                        parse_mode="HTML",
                        message_thread_id=message_thread_id,
                    )

                tid_info = f" (Topic: {message_thread_id})" if message_thread_id else ""
                await update.message.reply_text(
                    f"✅ Mensaje <code>{slug}</code> enviado a {target_chat_id}{tid_info}",
                    parse_mode="HTML",
                )
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Error al enviar mensaje guardado: {e}"
                )
        else:
            # It is NOT a stored message, send as text (Legacy behavior)
            try:
                await context.bot.send_message(
                    chat_id=target_chat_id,
                    text=content,
                    message_thread_id=message_thread_id,
                )
                tid_info = f" (Topic: {message_thread_id})" if message_thread_id else ""
                await update.message.reply_text(
                    f"✅ Mensaje de texto enviado a {target_chat_id}{tid_info}"
                )
            except Exception as e:
                await update.message.reply_text(f"❌ Error al enviar texto: {e}")

    async def set_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if not context.args:
            current = self._get_setting("welcome_msg_id")
            status = "Apagado" if not current else f"Activo (ID: {current})"
            await update.message.reply_text(
                f"👋 Bienvenida Automática: <b>{status}</b>\nUsa /set_welcome <id|off>",
                parse_mode="HTML",
            )
            return

        arg = context.args[0].lower()
        if arg == "off":
            self._set_setting("welcome_msg_id", "")
            await update.message.reply_text("👋 Bienvenida automática desactivada.")
        else:
            # Verify if valid slug
            if arg not in TEMPLATE_REGISTRY and not self._get_message(arg):
                await update.message.reply_text(
                    "❌ ID no encontrado. Usa uno de /list_msge"
                )
                return

            self._set_setting("welcome_msg_id", arg)
            await update.message.reply_text(
                f"👋 Bienvenida configurada con mensaje: <code>{arg}</code>",
                parse_mode="HTML",
            )

    async def reset_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Borra un mensaje personalizado y restaura el valor por defecto."""
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if not context.args:
            await update.message.reply_text("❌ Uso: /reset_msge <slug>")
            return

        slug = context.args[0].lower()

        session = self.Session()
        try:
            msg = session.query(StoredMessage).filter_by(slug=slug).first()
            if not msg:
                if slug in TEMPLATE_REGISTRY:
                    await update.message.reply_text(
                        f"ℹ️ El mensaje <code>{slug}</code> ya está usando el valor por defecto.",
                        parse_mode="HTML",
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Mensaje <code>{slug}</code> no encontrado.",
                        parse_mode="HTML",
                    )
                return

            session.delete(msg)
            session.commit()

            await update.message.reply_text(
                f"✅ Mensaje <code>{slug}</code> restaurado a su valor por defecto.",
                parse_mode="HTML",
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Error reset_msge: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
        finally:
            session.close()

    def _get_template_categories(self) -> Dict[str, List[str]]:
        categories = {
            "Ayuda y Menús": [],
            "Inicio y Bienvenida": [],
            "Donaciones y Niveles": [],
            "Modo Evil (Privado)": [],
            "Búsqueda": [],
            "Sistema y Estado": [],
            "Otros": [],
        }

        all_keys = sorted(TEMPLATE_REGISTRY.keys())
        for slug in all_keys:
            if slug.startswith("help_"):
                cat = "Ayuda y Menús"
            elif slug.startswith("start_") or slug.startswith("saludo"):
                cat = "Inicio y Bienvenida"
            elif "donate" in slug or "donation" in slug or "levels" in slug:
                cat = "Donaciones y Niveles"
            elif slug.startswith("evil_"):
                cat = "Modo Evil (Privado)"
            elif slug.startswith("search_"):
                cat = "Búsqueda"
            elif any(
                x in slug for x in ["status", "banned", "bot_", "cancel", "private"]
            ):
                cat = "Sistema y Estado"
            else:
                cat = "Otros"
            categories[cat].append(slug)
        return categories

    def _build_templates_keyboard(
        self, current_cat: str = None
    ) -> InlineKeyboardMarkup:
        # Fixed order
        cat_order = [
            "Inicio y Bienvenida",
            "Ayuda y Menús",
            "Sistema y Estado",
            "Donaciones y Niveles",
            "Búsqueda",
            "Modo Evil (Privado)",
            "Otros",
        ]

        buttons = []
        if current_cat is None:
            # Main Menu: Categories
            for cat in cat_order:
                # Callback: templates|cat|<cat_name>
                buttons.append(
                    [
                        InlineKeyboardButton(
                            f"📂 {cat}", callback_data=f"templates|cat|{cat}"
                        )
                    ]
                )
            buttons.append(
                [InlineKeyboardButton("❌ Cerrar", callback_data="templates|close")]
            )
        else:
            # Back Button only
            buttons.append(
                [
                    InlineKeyboardButton(
                        "🔙 Volver a Categorías", callback_data="templates|home"
                    )
                ]
            )

        return InlineKeyboardMarkup(buttons)

    async def templates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú interactivo de plantillas."""
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        keyboard = self._build_templates_keyboard()
        await update.message.reply_text(
            "📋 <b>Gestor de Plantillas</b>\n\nSelecciona una categoría para ver los textos disponibles:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    async def templates_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        uid = update.effective_user.id

        if uid not in config.ADMIN_USERS:
            await query.answer("⛔ No tienes permisos.", show_alert=True)
            return

        data = query.data.split("|")
        # templates | action | arg
        action = data[1]
        arg = data[2] if len(data) > 2 else None

        if action == "close":
            await query.message.delete()
            return

        if action == "home":
            keyboard = self._build_templates_keyboard()
            await query.edit_message_text(
                "📋 <b>Gestor de Plantillas</b>\n\nSelecciona una categoría para ver los textos disponibles:",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            return

        if action == "cat":
            cat_name = arg
            categories = self._get_template_categories()
            slugs = categories.get(cat_name, [])

            text = f"📂 <b>{cat_name.upper()}</b>\n\n"
            text += "Usa <code>/add_msge &lt;slug&gt;</code> para personalizar.\n\n"

            for slug in slugs:
                info = TEMPLATE_REGISTRY[slug]
                vars_str = ", ".join(info["vars"]) if info["vars"] else "Ninguna"
                entry = f"🔹 <b>{slug}</b>\n"
                entry += f"   📝 {info['desc']}\n"
                entry += f"   💲 Vars: <code>{vars_str}</code>\n\n"

                # Check length limit (simple check, if too long cut it)
                if len(text) + len(entry) > 4000:
                    text += "<i>... lista truncada por límite de longitud ...</i>"
                    break
                text += entry

            keyboard = self._build_templates_keyboard(current_cat=cat_name)
            await query.edit_message_text(
                text, reply_markup=keyboard, parse_mode="HTML"
            )

    async def set_var(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Uso: /set_var <Variable> <Valor>\n"
                "Ejemplo: /set_var CanalOficial https://t.me/mi_canal"
            )
            return

        key = context.args[0]
        # Remove brackets if user typed them
        key = key.replace("[", "").replace("]", "")
        value = " ".join(context.args[1:])

        self._set_global_var(key, value)
        await update.message.reply_text(
            f"✅ Variable global <code>[{key}]</code> establecida a: <b>{html.escape(value)}</b>",
            parse_mode="HTML",
        )

    async def del_var(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if not context.args:
            await update.message.reply_text("❌ Uso: /del_var <Variable>")
            return

        key = context.args[0].replace("[", "").replace("]", "")
        self._del_global_var(key)
        await update.message.reply_text(
            f"🗑 Variable global <code>[{key}]</code> eliminada.", parse_mode="HTML"
        )

    async def vars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista las variables globales disponibles (Sistema + Admin)."""
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        text = "💲 <b>Variables Globales</b>\n\n"

        # System Vars
        text += "🤖 <b>Sistema (Automáticas):</b>\n"
        for key, desc in GLOBAL_VARIABLES.items():
            text += f"🔹 <code>[{key}]</code>: {desc}\n"

        # Admin Vars
        text += "\n🛠 <b>Personalizadas (Admin):</b>\n"
        if not self._global_vars_cache:
            text += "<i>(Ninguna definida, usa /set_var)</i>\n"
        else:
            for k, v in self._global_vars_cache.items():
                text += f"🔸 <code>[{k}]</code>: {html.escape(v)}\n"

        await update.message.reply_text(text, parse_mode="HTML")

    async def template_vars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Legacy alias for /vars
        await self.vars(update, context)

    async def welcome_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Triggered on MY_CHAT_MEMBER updates
        current_welcome_id = self._get_setting("welcome_msg_id")
        if not current_welcome_id:
            return

        result = update.my_chat_member
        new_state = result.new_chat_member.status
        old_state = result.old_chat_member.status

        # Check if bot was added (was not member/restricted/kicked, now is member/admin)
        from telegram.constants import ChatMemberStatus

        was_member = old_state in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
        ]
        is_member = new_state in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
        ]

        if not was_member and is_member:
            # Bot added to a new chat!
            chat_id = update.effective_chat.id
            logger.info(
                f"Bot añadido a grupo {chat_id}. Enviando bienvenida si corresponde."
            )

            # Use get_text to support default templates too, not just DB copy
            # But copy_message is richer for multimedia.
            # Strategy: Try DB message first (for copy). If not, send text.

            msg = self._get_message(current_welcome_id)
            if msg and not msg.text_content:
                try:
                    await context.bot.copy_message(
                        chat_id=chat_id,
                        from_chat_id=msg.source_chat_id,
                        message_id=msg.source_message_id,
                    )
                except Exception as e:
                    logger.error(f"Error enviando bienvenida (copy): {e}")
            else:
                # Text based
                try:
                    text = self.get_text(current_welcome_id)
                    await context.bot.send_message(
                        chat_id=chat_id, text=text, parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Error enviando bienvenida (text): {e}")
