"""
Registro de plantillas y variables globales.
Extraído de custom_messages_plugin.py
"""

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
    "search_streaming_feedback": {
        "desc": "Búsqueda: Feedback en tiempo real (Draft)",
        "vars": ["[Termino]"],
        "default": "🔎 Buscando en catálogos: <i>[Termino]</i>...",
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
    "donation_redirect_prompt": {
        "desc": "Mensaje de redirección a privado para comprobante",
        "vars": ["[Nombre]"],
        "default": "👋 Hola [Nombre],\n\nPara proteger tu privacidad, por favor envíame el comprobante a mi chat privado pulsando el botón de abajo.",
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
    "donation_cancelled_timeout": {
        "desc": "Mensaje de registro cancelado por inactividad",
        "vars": ["[Nombre]"],
        "default": "⚠️ <b>Registro de Donación Cancelado</b>\n\nHola [Nombre], el tiempo de espera para enviar el comprobante (10 min) ha expirado. Si aún deseas registrar tu donación, por favor usa /donar nuevamente.",
    },
    "donation_cancelled_user": {
        "desc": "Mensaje de registro cancelado por el usuario",
        "vars": ["[Nombre]"],
        "default": "✅ <b>Registro Cancelado</b>\n\nHola [Nombre], el registro de tu donación ha sido cancelado exitosamente.",
    },
    "donation_proof_request": {
        "desc": "Solicitud de comprobante de donación",
        "vars": ["[Tiempo]"],
        "default": "🧾 <b>Comprobante Requerido</b>\n\nPor favor, envía una <b>captura de pantalla</b> o <b>archivo PDF</b> de tu comprobante de donación.\nLo revisaremos para actualizar tu nivel.\n\n⏳ Tienes <b>[Tiempo] minutos</b> para enviar el comprobante antes de que el registro se cancele automáticamente.",
    },
    "donation_proof_received": {
        "desc": "Confirmación de recepción de comprobante",
        "vars": [],
        "default": "✅ <b>Comprobante recibido</b>\n\nHemos enviado tu comprobante a los administradores para su verificación.\nTe avisaremos cuando tu nivel sea actualizado.\n¡Gracias por tu apoyo! ❤️",
    },
    "donation_link_unauthorized": {
        "desc": "Enlace de donación no autorizado",
        "vars": [],
        "default": "⚠️ Este enlace de donación no es para ti.",
    },
    "webapp_auth_invalid": {
        "desc": "Autenticación webapp inválida",
        "vars": [],
        "default": "❌ Datos de autenticación inválidos.",
    },
    "download_preparing": {
        "desc": "Preparando descarga",
        "vars": [],
        "default": "⏳ Preparando descarga...",
    },
    "donation_proof_invalid_format": {
        "desc": "Formato de comprobante inválido",
        "vars": [],
        "default": "❌ Por favor envía una imagen o un archivo PDF.",
    },
    "destination_selected": {
        "desc": "Destino seleccionado",
        "vars": [],
        "default": "✅ Destino seleccionado",
    },
    "no_pending_publication": {
        "desc": "No hay publicación pendiente",
        "vars": [],
        "default": "No hay publicación pendiente.",
    },
    "search_prompt": {
        "desc": "Solicitud de búsqueda (sin término)",
        "vars": [],
        "default": "🔍 ¿Qué libro buscas? Escribe el título o autor:",
    },
    "search_prompt_inline": {
        "desc": "Solicitud de búsqueda (inline)",
        "vars": [],
        "default": "🔍 Escribe parte del título del EPUB:",
    },
    "manual_destination_prompt": {
        "desc": "Solicitud de destino manual",
        "vars": [],
        "default": "✏️ Escribe @usuario o chat_id para publicar:",
    },
    "publisher_target_prompt": {
        "desc": "Pregunta de destino para publisher (/start)",
        "vars": [],
        "default": "🔧 Eres publisher — ¿dónde quieres publicar la próxima vez que selecciones un libro?",
    },
    "evil_telegram_selected": {
        "desc": "Aviso: Publicación temporal en Telegram",
        "vars": [],
        "default": "✅ Publicación temporal en Telegram seleccionada — configurando destino.",
    },
    "evil_facebook_selected": {
        "desc": "Aviso: Publicación temporal en Facebook",
        "vars": [],
        "default": "✅ Publicación temporal en Facebook seleccionada — entrando a Evil (publicación en este chat).",
    },
    "evil_selected_generic": {
        "desc": "Aviso: Modo Evil seleccionado",
        "vars": [],
        "default": "✅ Modo Evil seleccionado.",
    },
    "publish_cancelled": {
        "desc": "Publicación cancelada",
        "vars": [],
        "default": "⛔ Publicación cancelada.",
    },
    "publish_success_telegram": {
        "desc": "Publicación exitosa (Telegram)",
        "vars": ["[Titulo]"],
        "default": "✅ Publicado: [Titulo]",
    },
    "publish_preference_cleared": {
        "desc": "Preferencia de publicación borrada",
        "vars": [],
        "default": "⚪ Preferencia temporal de publicación descartada.",
    },
    "publish_preference_set": {
        "desc": "Preferencia de publicación establecida",
        "vars": ["[Destino]"],
        "default": "✅ Publicación temporal establecida para el próximo libro: [Destino].",
    },
    "invalid_option": {
        "desc": "Opción inválida",
        "vars": [],
        "default": "Opción inválida",
    },
    "no_more_pages": {
        "desc": "No hay más páginas",
        "vars": [],
        "default": "🚫 No hay más páginas",
    },
    "fb_preview_discarded": {
        "desc": "Vista previa FB descartada",
        "vars": [],
        "default": "🗑️ Descartado",
    },
    "button_unauthorized": {
        "desc": "Botón/mensaje no autorizado",
        "vars": [],
        "default": "⚠️ Este botón no es para ti.",
    },
    "donation_request_registered": {
        "desc": "Solicitud de donación registrada",
        "vars": [],
        "default": "✅ Solicitud registrada.",
    },
    "request_processing_error": {
        "desc": "Error procesando solicitud",
        "vars": [],
        "default": "❌ Ocurrió un error al procesar tu solicitud.",
    },
    "donation_approved": {
        "desc": "Notificación de donación aprobada",
        "vars": ["[Nivel]", "[Duración]"],
        "default": "✅ <b>¡Donación Verificada!</b>\n\nTu donación ha sido aprobada.\n<b>Nuevo nivel:</b> [Nivel]{{if Duración}}\n<b>Duración:</b> [Duración] días{{endif}}\n\n¡Gracias por tu apoyo! ❤️",
    },
    "donation_rejected": {
        "desc": "Notificación de donación rechazada",
        "vars": [],
        "default": "⚠️ <b>Comprobante No Válido</b>\n\nLamentablemente, tu comprobante de donación no pudo ser verificado.\n\nSi crees que es un error, por favor contacta a un administrador.",
    },
    "suggestion_accepted": {
        "desc": "Sugerencia aceptada",
        "vars": [],
        "default": "✅ <b>Sugerencia Aceptada</b>\n\n¡Gracias por tu aporte! Tu sugerencia será tomada en cuenta.",
    },
    "suggestion_rejected": {
        "desc": "Sugerencia rechazada",
        "vars": [],
        "default": "❌ <b>Sugerencia Rechazada</b>\n\nGracias por tu interés, pero tu sugerencia no será implementada en este momento.",
    },
    "suggestion_custom_response": {
        "desc": "Respuesta personalizada a sugerencia",
        "vars": ["[Respuesta]"],
        "default": "💬 <b>Respuesta a tu Sugerencia</b>\n\n[Respuesta]",
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
        "vars": [
            "[Nivel]",
            "[Descargas]",
            "[ResetTime]",
            "[Expires]",
            "[TotalDescargas]",
        ],
        "default": "🤖 <b>ZeePub Bot</b> [VersionBot]\n\n📊 <b>Tu Estado</b>\n\n👤 <b>Usuario:</b> [Nombre]\n🆔 <b>ID:</b> [ID]\n⭐ <b>Nivel:</b> [Nivel]\n{{if Rol}}👨🏻‍💻 <b>Rol:</b> [Rol]\n{{endif}}{{if Apodo}}👨🏻‍💻 <b>Apodo:</b> [Apodo]\n{{endif}}{{if Expires}}📅 <b>Vence:</b> [Expires]\n{{endif}}📉 <b>Descargas Hoy:</b> [Descargas]\n📈 <b>Descargas Totales:</b> [TotalDescargas]\n{{if ResetTime}}⏳ <b>Reinicio en:</b> [ResetTime]\n{{endif}}",
    },
    "help_cat_header": {
        "desc": "Encabezado de categoría en /help",
        "vars": ["[Categoria]"],
        "default": "📂 <b>Categoría: [Categoria]</b>\n\nSelecciona un comando para ver detalles:",
    },
    "bot_presentation": {
        "desc": "Presentación Automática al unirse a grupos/canales",
        "vars": [],
        "default": "👋 <b>¡Hola! Soy ZeePub Bot.</b>\n\nGracias por añadirme. 📚\nPuedo ayudarte a buscar y descargar libros, gestionar bibliotecas y más.\n\n👤 <b>Admin:</b> Usa /start por privado para configurarme.\n🔍 <b>Usuarios:</b> Usen /search para buscar libros.\n\n¡Espero ser de ayuda!",
    },
    "milestone_10_downloads": {
        "desc": "Hito: 10 descargas (Nivel 1)",
        "vars": ["[Nombre]"],
        "default": "🎁 ¡Felicidades [Nombre]! Has descargado tus primeros 10 libros. 🎉",
    },
    "milestone_50_downloads": {
        "desc": "Hito: 50 descargas (Nivel 2)",
        "vars": ["[Nombre]"],
        "default": "🌟 ¡Increíble [Nombre]! Ya llevas 50 libros descargados. Eres un lector apasionado. 📚",
    },
    "milestone_100_downloads": {
        "desc": "Hito: 100 descargas (Nivel 3)",
        "vars": ["[Nombre]"],
        "default": "👑 ¡Master Lector [Nombre]! 100 libros descargados. ¡Tu biblioteca es legendaria! 🏆",
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
    "help_cmd_menu": {
        "desc": "Ayuda: /menu",
        "vars": [],
        "default": "ℹ️ <b>Comando: /menu</b>\n\n📝 <b>Descripción:</b>\nMuestra un menú interactivo con botones para acceder rápidamente a las diferentes funciones del bot organizadas por categorías.\n\n⌨️ <b>Uso:</b> <code>/menu</code>\n💡 <b>Ejemplo:</b> <code>/menu</code>",
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
    "help_cmd_set_rol": {
        "desc": "Ayuda: /set_rol",
        "vars": [],
        "default": "ℹ️ <b>Comando: /set_rol</b>\n\n📝 <b>Descripción:</b>\nOtorga o revoca el estado de 'Staff' a un usuario. Cambia el [Rol] funcional.\n\n⌨️ <b>Uso:</b> <code>/set_rol &lt;user_id&gt; &lt;label&gt;</code>\n💡 <b>Ejemplo:</b> <code>/set_rol 123456789 Editor Jefe</code>",
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
    "help_cmd_approve_donation": {
        "desc": "Ayuda: /approve_donation",
        "vars": [],
        "default": "ℹ️ <b>Comando: /approve_donation</b>\n\n📝 <b>Descripción:</b>\nAprueba una donación, actualiza el nivel del usuario y envía una notificación automática al chat privado.\n\n⌨️ <b>Uso:</b> <code>/approve_donation &lt;id&gt; &lt;rol&gt; [meses]</code>\n💡 <b>Ejemplo:</b> <code>/approve_donation 123456 vip 1</code>",
    },
    "help_cmd_reject_donation": {
        "desc": "Ayuda: /reject_donation",
        "vars": [],
        "default": "ℹ️ <b>Comando: /reject_donation</b>\n\n📝 <b>Descripción:</b>\nRechaza una donación y envía una notificación automática al usuario informándole que su comprobante no es válido.\n\n⌨️ <b>Uso:</b> <code>/reject_donation &lt;id&gt;</code>\n💡 <b>Ejemplo:</b> <code>/reject_donation 123456</code>",
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
    "help_cmd_refresh_user": {
        "desc": "Ayuda: /refresh_user",
        "vars": [],
        "default": "ℹ️ <b>Comando: /refresh_user</b>\n\n📝 <b>Descripción:</b>\nBusca y actualiza los datos del usuario (id, nombre, alias) directamente desde los servidores de Telegram. Útil si un usuario ha cambiado su alias o nombre.\n\n⌨️ <b>Uso:</b> <code>/refresh_user &lt;user_id&gt;</code>\n💡 <b>Ejemplo:</b> <code>/refresh_user 123456789</code>",
    },
    "help_cmd_scan_library": {
        "desc": "Ayuda: /scan_library",
        "vars": [],
        "default": "ℹ️ <b>Comando: /scan_library</b>\n\n📝 <b>Descripción:</b>\nInicia un escaneo completo de la carpeta de libros local para indexar nuevos títulos, autores, series y generar miniaturas.\n\n⌨️ <b>Uso:</b> <code>/scan_library</code>\n💡 <b>Ejemplo:</b> <code>/scan_library</code>",
    },
    "help_cmd_verify": {
        "desc": "Ayuda: /verify",
        "vars": [],
        "default": "ℹ️ <b>Comando: /verify</b>\n\n📝 <b>Descripción:</b>\nInicia el proceso de verificación para nuevos usuarios mediante retos sencillos para confirmar que no son bots.\n\n⌨️ <b>Uso:</b> <code>/verify</code>\n💡 <b>Ejemplo:</b> <code>/verify</code>",
    },
    "help_cmd_set_export_time": {
        "desc": "Ayuda: /set_export_time",
        "vars": [],
        "default": "ℹ️ <b>Comando: /set_export_time</b>\n\n📝 <b>Descripción:</b>\nConfigura la hora para la exportación automática diaria de las bases de datos (url_cache.db y library.db).\n\n⌨️ <b>Uso:</b> <code>/set_export_time &lt;HH:MM&gt;</code>\n💡 <b>Ejemplo:</b> <code>/set_export_time 04:00</code>",
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
    "help_cmd_view_msge": {
        "desc": "Ayuda: /view_msge",
        "vars": [],
        "default": "ℹ️ <b>Comando: /view_msge</b>\n\n📝 <b>Descripción:</b>\nMuestra cómo se verá un template renderizado con HTML procesado (útil para previsualizar el resultado final).\n\n⌨️ <b>Uso:</b> <code>/view_msge &lt;slug&gt;</code>\n💡 <b>Ejemplo:</b> <code>/view_msge start_welcome_unlimited</code>",
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
    "help_cmd_set_bot_avatar": {
        "desc": "Ayuda: /set_bot_avatar",
        "vars": [],
        "default": "ℹ️ <b>Comando: /set_bot_avatar</b>\n\n📝 <b>Descripción:</b>\nCambia la foto de perfil del bot. Debes responder a una imagen con el comando.\n\n⌨️ <b>Uso:</b> Responder a foto con <code>/set_bot_avatar</code>\n💡 <b>Ejemplo:</b> <code>/set_bot_avatar</code>",
    },
    "help_cmd_set_version": {
        "desc": "Ayuda: /set_version",
        "vars": [],
        "default": "ℹ️ <b>Comando: /set_version</b>\n\n📝 <b>Descripción:</b>\nCambia la etiqueta de imagen (versión) en el archivo docker-compose.yml y reinicia el bot.\n\n⌨️ <b>Uso:</b> <code>/set_version &lt;tag&gt;</code>\n💡 <b>Ejemplo:</b> <code>/set_version v6.0.0</code>",
    },
    "help_cmd_add_menu_cmd": {
        "desc": "Ayuda: /add_menu_cmd",
        "vars": [],
        "default": "ℹ️ <b>Comando: /add_menu_cmd</b>\n\n📝 <b>Descripción:</b>\nAgrega un comando existente al menú público de Telegram.\n\n⌨️ <b>Uso:</b> <code>/add_menu_cmd &lt;comando&gt;</code>\n💡 <b>Ejemplo:</b> <code>/add_menu_cmd search</code>",
    },
    "help_cmd_del_menu_cmd": {
        "desc": "Ayuda: /del_menu_cmd",
        "vars": [],
        "default": "ℹ️ <b>Comando: /del_menu_cmd</b>\n\n📝 <b>Descripción:</b>\nElimina un comando del menú público de Telegram.\n\n⌨️ <b>Uso:</b> <code>/del_menu_cmd &lt;comando&gt;</code>\n💡 <b>Ejemplo:</b> <code>/del_menu_cmd status</code>",
    },
    "help_cmd_list_menu_cmd": {
        "desc": "Ayuda: /list_menu_cmd",
        "vars": [],
        "default": "ℹ️ <b>Comando: /list_menu_cmd</b>\n\n📝 <b>Descripción:</b>\nMuestra la lista actual de comandos en el menú público de Telegram.\n\n⌨️ <b>Uso:</b> <code>/list_menu_cmd</code>\n💡 <b>Ejemplo:</b> <code>/list_menu_cmd</code>",
    },
    "help_cmd_move_menu_cmd": {
        "desc": "Ayuda: /move_menu_cmd",
        "vars": [],
        "default": "ℹ️ <b>Comando: /move_menu_cmd</b>\n\n📝 <b>Descripción:</b>\nCambia la posición de un comando en el menú público (1-indexado).\n\n⌨️ <b>Uso:</b> <code>/move_menu_cmd &lt;comando&gt; &lt;posición&gt;</code>\n💡 <b>Ejemplo:</b> <code>/move_menu_cmd search 1</code>",
    },
    "help_cmd_refresh_menu": {
        "desc": "Ayuda: /refresh_menu",
        "vars": [],
        "default": "ℹ️ <b>Comando: /refresh_menu</b>\n\n📝 <b>Descripción:</b>\nForza la actualización inmediata del menú de comandos en Telegram para todos los usuarios.\n\n⌨️ <b>Uso:</b> <code>/refresh_menu</code>\n💡 <b>Ejemplo:</b> <code>/refresh_menu</code>",
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
    "help_cmd_recommend": {
        "desc": "Ayuda: /recommend",
        "vars": [],
        "default": "ℹ️ <b>Comando: /recommend</b>\n\n📝 <b>Descripción:</b>\nGenera recomendaciones personalizadas de libros basadas en tus gustos (Beta Staff).\n\n⌨️ <b>Uso:</b> <code>/recommend</code>\n💡 <b>Ejemplo:</b> <code>/recommend</code>",
    },
    "help_cmd_settings": {
        "desc": "Ayuda: /settings",
        "vars": [],
        "default": "ℹ️ <b>Comando: /settings</b>\n\n📝 <b>Descripción:</b>\nAccede al menú de configuración para gestionar tus preferencias, como las recomendaciones semanales.\n\n⌨️ <b>Uso:</b> <code>/settings</code>\n💡 <b>Ejemplo:</b> <code>/settings</code>",
    },
    "help_cmd_rules": {
        "desc": "Ayuda: /rules",
        "vars": [],
        "default": "ℹ️ <b>Comando: /rules</b>\n\n📝 <b>Descripción:</b>\nMuestra las reglas configuradas para el grupo actual. Alias de /reglas.\n\n⌨️ <b>Uso:</b> <code>/rules</code>\n💡 <b>Ejemplo:</b> <code>/rules</code>",
    },
    # --- Mini App Donation Tiers ---
    "web_donate_tier_lector_name": {
        "desc": "Web: Nombre nivel Lector",
        "vars": [],
        "default": "Lector",
    },
    "web_donate_tier_lector_price": {
        "desc": "Web: Precio nivel Lector",
        "vars": [],
        "default": "Gratis",
    },
    "web_donate_tier_lector_downloads": {
        "desc": "Web: Descargas nivel Lector",
        "vars": [],
        "default": "5 al día",
    },
    "web_donate_tier_patrocinador_name": {
        "desc": "Web: Nombre nivel Patrocinador",
        "vars": [],
        "default": "Patrocinador",
    },
    "web_donate_tier_premium_downloads": {
        "desc": "Web: Descargas nivel Premium",
        "vars": [],
        "default": "Ilimitado",
    },
    # --- Telegram Stars ---
    "star_payment_invoice_desc": {
        "desc": "Stars: Descripción de la factura",
        "vars": ["Nivel"],
        "default": "Suscripción al nivel [Nivel] de ZeePubBot",
    },
    "star_payment_success": {
        "desc": "Stars: Mensaje de pago exitoso",
        "vars": ["Nivel", "Nombre"],
        "default": "🌟 ¡Gracias [Nombre]! Has desbloqueado el nivel <b>[Nivel]</b> con éxito usando Telegram Stars.\n\nDisfruta de tus beneficios.",
    },
    "web_donate_stars_btn": {
        "desc": "Web: Botón de pago con Estrellas",
        "vars": [],
        "default": "Pagar con Estrellas ⭐️",
    },
    "web_donate_tier_patrocinador_downloads": {
        "desc": "Web: Descargas nivel Patrocinador",
        "vars": [],
        "default": "10 al día",
    },
    "web_donate_tier_vip_name": {
        "desc": "Web: Nombre nivel VIP",
        "vars": [],
        "default": "VIP",
    },
    "web_donate_tier_vip_price": {
        "desc": "Web: Precio nivel VIP",
        "vars": [],
        "default": "$8/mes",
    },
    "web_donate_tier_vip_downloads": {
        "desc": "Web: Descargas nivel VIP",
        "vars": [],
        "default": "25 al día",
    },
    "web_donate_tier_premium_name": {
        "desc": "Web: Nombre nivel Premium",
        "vars": [],
        "default": "Premium",
    },
    "web_donate_tier_premium_price": {
        "desc": "Web: Precio nivel Premium",
        "vars": [],
        "default": "$12/mes",
    },
    "help_cmd_set_group_welcome": {
        "desc": "Ayuda: /set_group_welcome",
        "vars": [],
        "default": "ℹ️ <b>Comando: /set_group_welcome</b>\n\n📝 <b>Descripción:</b>\nConfigura un mensaje de bienvenida personalizado para este grupo. Debes crear el mensaje primero con /add_msge.\n\n✨ <b>Personalización:</b> Si el mensaje guardado contiene <code>[Nombre]</code>, será reemplazado por el nombre del usuario nuevo.\n\n⌨️ <b>Uso:</b> <code>/set_group_welcome &lt;slug&gt;</code>\n💡 <b>Ejemplo:</b> <code>/set_group_welcome bienvenida_grupo</code>",
    },
    # --- Stats Plugin ---
    "stats_no_users": {
        "desc": "Stats: No se encontraron usuarios",
        "vars": ["[Rol]"],
        "default": "ℹ️ No se encontraron usuarios con el rol <b>[Rol]</b> en base de datos.",
    },
    "stats_list_header": {
        "desc": "Stats: Encabezado de lista de usuarios",
        "vars": ["[Rol]", "[Cantidad]"],
        "default": "📋 <b>Usuarios con rol: [Rol]</b> ([Cantidad])\n\n",
    },
    "stats_daily_summary": {
        "desc": "Stats: Resumen diario",
        "vars": ["[UniqueUsers]", "[TotalDownloads]", "[RolesBreakdown]"],
        "default": "📊 <b>Estadísticas Diarias (Hoy)</b>\n\n👥 <b>Usuarios Únicos:</b> [UniqueUsers]\n⬇️ <b>Descargas Totales:</b> [TotalDownloads]\n[RolesBreakdown]",
    },
    # --- Maintenance Plugin ---
    "maint_backup_preparing": {
        "desc": "Maint: Generando backup",
        "vars": [],
        "default": "⏳ Generando backup...",
    },
    "maint_backup_caption": {
        "desc": "Maint: Pie de backup",
        "vars": ["[Fecha]"],
        "default": "📦 Backup de base de datos\n📅 [Fecha]",
    },
    "maint_restore_preparing": {
        "desc": "Maint: Restaurando",
        "vars": [],
        "default": "⏳ Descargando y restaurando backup... (Esto borrará los datos actuales)",
    },
    "maint_restore_success": {
        "desc": "Maint: Restauración exitosa",
        "vars": [],
        "default": "✅ Base de datos restaurada exitosamente.",
    },
    "maint_restore_error_no_doc": {
        "desc": "Maint: Error falta archivo",
        "vars": [],
        "default": "⚠️ Debes responder a un mensaje con el archivo .sql de backup para restaurarlo.",
    },
    "maint_export_preparing": {
        "desc": "Maint: Generando CSV",
        "vars": [],
        "default": "⏳ Generando CSV de la base de datos...",
    },
    "maint_export_caption": {
        "desc": "Maint: Pie de exportación",
        "vars": ["[Fecha]", "[Registros]"],
        "default": "📊 Exportación de base de datos\n📅 [Fecha]\n📦 [Registros] registros",
    },
    "maint_import_instructions": {
        "desc": "Maint: Instrucciones de importación",
        "vars": [],
        "default": "📂 <b>Modo de Importación Activado</b>\n\nPor favor, envía ahora el archivo <code>result.json</code> exportado de Telegram Desktop.\nEl bot procesará el archivo y guardará el historial de libros publicados.\n\n<i>Este modo se desactivará automáticamente después de recibir el archivo.</i>",
    },
    "maint_history_cleared": {
        "desc": "Maint: Historial borrado",
        "vars": [],
        "default": "✅ Historial borrado exitosamente.",
    },
    "maint_history_clear_confirm": {
        "desc": "Maint: Confirmación borrar historial",
        "vars": [],
        "default": "⚠️ <b>¡ATENCIÓN!</b> Esto borrará TODO el historial de libros publicados.\nPara confirmar, usa: <code>/clear_history confirm</code>",
    },
    # --- Mini App (Web) ---
    "web_catalog_title": {
        "desc": "Web: Título del catálogo",
        "vars": [],
        "default": "Catálogo",
    },
    "web_catalog_back": {
        "desc": "Web: Botón volver/subir nivel",
        "vars": [],
        "default": "Subir nivel",
    },
    "web_search_placeholder": {
        "desc": "Web: Placeholder buscador",
        "vars": [],
        "default": "Buscar por título, autor o serie...",
    },
    "web_search_button": {
        "desc": "Web: Botón buscar",
        "vars": [],
        "default": "Buscar",
    },
    "web_search_empty": {
        "desc": "Web: Texto sin resultados",
        "vars": [],
        "default": "No se encontraron resultados",
    },
    "web_search_prompt": {
        "desc": "Web: Instrucción inicial búsqueda",
        "vars": [],
        "default": "Busca libros por título o autor",
    },
    "web_pagination_prev": {
        "desc": "Web: Botón Anterior",
        "vars": [],
        "default": "Anterior",
    },
    "web_pagination_up": {
        "desc": "Web: Botón Subir",
        "vars": [],
        "default": "Subir",
    },
    "web_pagination_next": {
        "desc": "Web: Botón Siguiente",
        "vars": [],
        "default": "Siguiente",
    },
    "web_book_loading": {
        "desc": "Web: Texto cargando detalles",
        "vars": [],
        "default": "Cargando detalles...",
    },
    "web_book_download": {
        "desc": "Web: Botón descargar",
        "vars": [],
        "default": "Descargar",
    },
    # --- Command Menu Descriptions (Telegram /) ---
    "cmd_menu_desc_start": {
        "desc": "Menú: Descripción /start",
        "vars": [],
        "default": "Iniciar bot",
    },
    "cmd_menu_desc_help": {
        "desc": "Menú: Descripción /help",
        "vars": [],
        "default": "Muestra este menú",
    },
    "cmd_menu_desc_menu": {
        "desc": "Menú: Descripción /menu",
        "vars": [],
        "default": "Menú interactivo",
    },
    "cmd_menu_desc_search": {
        "desc": "Menú: Descripción /search",
        "vars": [],
        "default": "Buscar libros",
    },
    "cmd_menu_desc_donar": {
        "desc": "Menú: Descripción /donar",
        "vars": [],
        "default": "Link donación",
    },
    "cmd_menu_desc_niveles": {
        "desc": "Menú: Descripción /niveles",
        "vars": [],
        "default": "Info niveles",
    },
    "cmd_menu_desc_status": {
        "desc": "Menú: Descripción /status",
        "vars": [],
        "default": "Mi estado",
    },
    "cmd_menu_desc_cancel": {
        "desc": "Menú: Descripción /cancel",
        "vars": [],
        "default": "Cancelar acción",
    },
    "cmd_menu_desc_recommend": {
        "desc": "Menú: Descripción /recommend",
        "vars": [],
        "default": "Recomendaciones (Beta)",
    },
    "cmd_menu_desc_settings": {
        "desc": "Menú: Descripción /settings",
        "vars": [],
        "default": "Configuración personal",
    },
    "cmd_menu_desc_reglas": {
        "desc": "Menú: Descripción /reglas",
        "vars": [],
        "default": "Ver reglas",
    },
    "cmd_menu_desc_rules": {
        "desc": "Menú: Descripción /rules",
        "vars": [],
        "default": "Ver reglas (Alias)",
    },
    "cmd_menu_desc_sugerencia": {
        "desc": "Menú: Descripción /sugerencia",
        "vars": [],
        "default": "Enviar sugerencia",
    },
    "cmd_menu_desc_add_user": {
        "desc": "Menú: Descripción /add_user",
        "vars": [],
        "default": "Agregar/Editar usuario",
    },
    "cmd_menu_desc_remove_user": {
        "desc": "Menú: Descripción /remove_user",
        "vars": [],
        "default": "Eliminar usuario",
    },
    "cmd_menu_desc_set_rol": {
        "desc": "Menú: Descripción /set_rol",
        "vars": [],
        "default": "Gestionar Staff/Rol",
    },
    "cmd_menu_desc_set_apodo": {
        "desc": "Menú: Descripción /set_apodo",
        "vars": [],
        "default": "Establecer Apodo",
    },
    "cmd_menu_desc_reset": {
        "desc": "Menú: Descripción /reset",
        "vars": [],
        "default": "Resetear descargas",
    },
    "cmd_menu_desc_refresh_user": {
        "desc": "Menú: Descripción /refresh_user",
        "vars": [],
        "default": "Refrescar datos usuario",
    },
    "cmd_menu_desc_id": {
        "desc": "Menú: Descripción /id",
        "vars": [],
        "default": "Ver mi ID",
    },
    "cmd_menu_desc_setlog": {
        "desc": "Menú: Descripción /setlog",
        "vars": [],
        "default": "Cambiar nivel de log",
    },
    "cmd_menu_desc_stats": {
        "desc": "Menú: Descripción /stats",
        "vars": [],
        "default": "Estadísticas del bot",
    },
    "cmd_menu_desc_evil": {
        "desc": "Menú: Descripción /evil",
        "vars": [],
        "default": "Activar Modo Evil",
    },
    "cmd_menu_desc_set_auto_delete_time": {
        "desc": "Menú: Descripción /set_auto_delete_time",
        "vars": [],
        "default": "Tiempo auto-borrado",
    },
    "cmd_menu_desc_debug_state": {
        "desc": "Menú: Descripción /debug_state",
        "vars": [],
        "default": "Estado interno usuario",
    },
    "cmd_menu_desc_update_system": {
        "desc": "Menú: Descripción /update_system",
        "vars": [],
        "default": "Actualizar sistema",
    },
    "cmd_menu_desc_set_version": {
        "desc": "Menú: Descripción /set_version",
        "vars": [],
        "default": "Cambiar versión bot",
    },
    "cmd_menu_desc_plugins": {
        "desc": "Menú: Descripción /plugins",
        "vars": [],
        "default": "Listar plugins cargados",
    },
    "cmd_menu_desc_set_price": {
        "desc": "Menú: Descripción /set_price",
        "vars": [],
        "default": "Configurar precios",
    },
    "cmd_menu_desc_approve_donation": {
        "desc": "Menú: Descripción /approve_donation",
        "vars": [],
        "default": "Aprobar donación",
    },
    "cmd_menu_desc_reject_donation": {
        "desc": "Menú: Descripción /reject_donation",
        "vars": [],
        "default": "Rechazar donación",
    },
    "cmd_menu_desc_backup_db": {
        "desc": "Menú: Descripción /backup_db",
        "vars": [],
        "default": "Respaldar Base de Datos",
    },
    "cmd_menu_desc_restore_db": {
        "desc": "Menú: Descripción /restore_db",
        "vars": [],
        "default": "Restaurar Base de Datos",
    },
    "cmd_menu_desc_import_history": {
        "desc": "Menú: Descripción /import_history",
        "vars": [],
        "default": "Importar historial",
    },
    "cmd_menu_desc_latest_books": {
        "desc": "Menú: Descripción /latest_books",
        "vars": [],
        "default": "Libros recientes",
    },
    "cmd_menu_desc_scan_library": {
        "desc": "Menú: Descripción /scan_library",
        "vars": [],
        "default": "Escanear librería",
    },
    "cmd_menu_desc_clear_history": {
        "desc": "Menú: Descripción /clear_history",
        "vars": [],
        "default": "Borrar historial",
    },
    "cmd_menu_desc_export_db": {
        "desc": "Menú: Descripción /export_db",
        "vars": [],
        "default": "Exportar mappings",
    },
    "cmd_menu_desc_export_history": {
        "desc": "Menú: Descripción /export_history",
        "vars": [],
        "default": "Exportar historial",
    },
    "cmd_menu_desc_set_export_time": {
        "desc": "Menú: Descripción /set_export_time",
        "vars": [],
        "default": "Hora exportación diaria",
    },
    "cmd_menu_desc_add_msge": {
        "desc": "Menú: Descripción /add_msge",
        "vars": [],
        "default": "Guardar mensaje",
    },
    "cmd_menu_desc_reset_msge": {
        "desc": "Menú: Descripción /reset_msge",
        "vars": [],
        "default": "Resetear mensaje",
    },
    "cmd_menu_desc_list_msge": {
        "desc": "Menú: Descripción /list_msge",
        "vars": [],
        "default": "Listar mensajes",
    },
    "cmd_menu_desc_view_msge": {
        "desc": "Menú: Descripción /view_msge",
        "vars": [],
        "default": "Previsualizar mensaje",
    },
    "cmd_menu_desc_send_msge": {
        "desc": "Menú: Descripción /send_msge",
        "vars": [],
        "default": "Enviar mensaje guardado",
    },
    "cmd_menu_desc_saludo": {
        "desc": "Menú: Descripción /saludo",
        "vars": [],
        "default": "Enviar saludo",
    },
    "cmd_menu_desc_set_welcome": {
        "desc": "Menú: Descripción /set_welcome",
        "vars": [],
        "default": "Configurar bienvenida",
    },
    "cmd_menu_desc_templates": {
        "desc": "Menú: Descripción /templates",
        "vars": [],
        "default": "Listar plantillas",
    },
    "cmd_menu_desc_set_var": {
        "desc": "Menú: Descripción /set_var",
        "vars": [],
        "default": "Definir variable",
    },
    "cmd_menu_desc_del_var": {
        "desc": "Menú: Descripción /del_var",
        "vars": [],
        "default": "Eliminar variable",
    },
    "cmd_menu_desc_vars": {
        "desc": "Menú: Descripción /vars",
        "vars": [],
        "default": "Listar variables",
    },
    "cmd_menu_desc_template_vars": {
        "desc": "Menú: Descripción /template_vars",
        "vars": [],
        "default": "Listar variables",
    },
    "cmd_menu_desc_status_links": {
        "desc": "Menú: Descripción /status_links",
        "vars": [],
        "default": "Estado de links",
    },
    "cmd_menu_desc_link_list": {
        "desc": "Menú: Descripción /link_list",
        "vars": [],
        "default": "Listar links",
    },
    "cmd_menu_desc_purge_link": {
        "desc": "Menú: Descripción /purge_link",
        "vars": [],
        "default": "Borrar link",
    },
    "cmd_menu_desc_authorize_group": {
        "desc": "Menú: Descripción /authorize_group",
        "vars": [],
        "default": "Autorizar grupo",
    },
    "cmd_menu_desc_revoke_group": {
        "desc": "Menú: Descripción /revoke_group",
        "vars": [],
        "default": "Revocar grupo",
    },
    "cmd_menu_desc_set_group_welcome": {
        "desc": "Menú: Descripción /set_group_welcome",
        "vars": [],
        "default": "Bienvenida grupo",
    },
    "cmd_menu_desc_add_menu_cmd": {
        "desc": "Menú: Descripción /add_menu_cmd",
        "vars": [],
        "default": "Añadir comando menú",
    },
    "cmd_menu_desc_del_menu_cmd": {
        "desc": "Menú: Descripción /del_menu_cmd",
        "vars": [],
        "default": "Quitar comando menú",
    },
    "cmd_menu_desc_list_menu_cmd": {
        "desc": "Menú: Descripción /list_menu_cmd",
        "vars": [],
        "default": "Listar comandos menú",
    },
    "cmd_menu_desc_move_menu_cmd": {
        "desc": "Menú: Descripción /move_menu_cmd",
        "vars": [],
        "default": "Reordenar menú",
    },
    "cmd_menu_desc_refresh_menu": {
        "desc": "Menú: Descripción /refresh_menu",
        "vars": [],
        "default": "Refrescar menú Telegram",
    },
    "cmd_menu_desc_set_bot_avatar": {
        "desc": "Menú: Descripción /set_bot_avatar",
        "vars": [],
        "default": "Cambiar avatar bot",
    },
    "cmd_menu_desc_verify": {
        "desc": "Menú: Descripción /verify",
        "vars": [],
        "default": "Verificar cuenta",
    },
    "web_book_section": {
        "desc": "Web: Texto ver colección",
        "vars": [],
        "default": "Ver esta colección...",
    },
    "web_book_series": {
        "desc": "Web: Etiqueta Serie",
        "vars": [],
        "default": "Serie",
    },
    "web_book_details_hint": {
        "desc": "Web: Sugerencia ver detalles",
        "vars": [],
        "default": "Toca para detalles...",
    },
    "web_donate_hero_title": {
        "desc": "Web: Título cabecera donaciones",
        "vars": [],
        "default": "Apoya a ZeePubBot",
    },
    "web_donate_hero_desc": {
        "desc": "Web: Descripción cabecera donaciones",
        "vars": [],
        "default": "Tu donación nos ayuda a mantener el servicio activo y mejorar continuamente",
    },
    "web_donate_tier_title": {
        "desc": "Web: Título selección de nivel",
        "vars": [],
        "default": "Elige tu nivel",
    },
    "web_donate_why_title": {
        "desc": "Web: Título por qué donar",
        "vars": [],
        "default": "¿Por qué donar?",
    },
    "web_donate_why_desc": {
        "desc": "Web: Descripción por qué donar",
        "vars": [],
        "default": "ZeePubBot es un proyecto de código abierto mantenido por la comunidad. Tu apoyo nos ayuda a:",
    },
    "web_donate_benefit_1": {
        "desc": "Web: Beneficio donación 1",
        "vars": [],
        "default": "Mantener los servidores activos 24/7",
    },
    "web_donate_benefit_2": {
        "desc": "Web: Beneficio donación 2",
        "vars": [],
        "default": "Añadir nuevas funcionalidades",
    },
    "web_donate_benefit_3": {
        "desc": "Web: Beneficio donación 3",
        "vars": [],
        "default": "Mejorar el catálogo de libros",
    },
    "web_home_greeting": {
        "desc": "Web: Saludo inicial",
        "vars": ["[Nombre]"],
        "default": "Hola, [Nombre]",
    },
    "web_home_functions": {
        "desc": "Web: Título sección funciones",
        "vars": [],
        "default": "Funciones",
    },
    "web_home_admin_panel": {
        "desc": "Web: Título panel administrador",
        "vars": [],
        "default": "Panel Administrador",
    },
    "web_home_admin_publish_title": {
        "desc": "Web: Título selector destino",
        "vars": [],
        "default": "Destino de Publicación",
    },
    "web_home_admin_publish_private": {
        "desc": "Web: Opción privado",
        "vars": [],
        "default": "Privado",
    },
    "web_home_admin_publish_channel": {
        "desc": "Web: Opción canal",
        "vars": [],
        "default": "Canal",
    },
    "web_home_admin_publish_group": {
        "desc": "Web: Opción grupo",
        "vars": [],
        "default": "Grupo",
    },
    "web_menu_search_label": {
        "desc": "Web: Etiqueta Buscar",
        "vars": [],
        "default": "Buscar Libros",
    },
    "web_menu_search_desc": {
        "desc": "Web: Desc Buscar",
        "vars": [],
        "default": "Encuentra ePubs en el catálogo",
    },
    "web_menu_catalog_label": {
        "desc": "Web: Etiqueta Catálogo",
        "vars": [],
        "default": "Mi Catálogo",
    },
    "web_menu_catalog_desc": {
        "desc": "Web: Desc Catálogo",
        "vars": [],
        "default": "Accede a bibliotecas OPDS",
    },
    "web_menu_downloads_label": {
        "desc": "Web: Etiqueta Descargas",
        "vars": [],
        "default": "Mis Descargas",
    },
    "web_menu_downloads_desc": {
        "desc": "Web: Desc Descargas",
        "vars": [],
        "default": "Historial y límites de descarga",
    },
    "web_menu_status_label": {
        "desc": "Web: Etiqueta Estado",
        "vars": [],
        "default": "Estado",
    },
    "web_menu_status_desc": {
        "desc": "Web: Desc Estado",
        "vars": [],
        "default": "Ver estado del bot y estadísticas",
    },
    "web_menu_donate_label": {
        "desc": "Web: Etiqueta Donar",
        "vars": [],
        "default": "Donar",
    },
    "web_menu_donate_desc": {
        "desc": "Web: Desc Donar",
        "vars": [],
        "default": "Apoya el proyecto",
    },
    "web_menu_help_label": {
        "desc": "Web: Etiqueta Ayuda",
        "vars": [],
        "default": "Ayuda",
    },
    "web_menu_help_desc": {
        "desc": "Web: Desc Ayuda",
        "vars": [],
        "default": "Comandos y soporte",
    },
    "web_status_current_level": {
        "desc": "Web: Etiqueta nivel actual",
        "vars": [],
        "default": "Nivel actual",
    },
    "web_status_downloads_today": {
        "desc": "Web: Título descargas de hoy",
        "vars": [],
        "default": "Descargas de Hoy",
    },
    "web_status_next_reset": {
        "desc": "Web: Texto próximo reset",
        "vars": ["[Tiempo]"],
        "default": "Próximo reset en [Tiempo]",
    },
    "web_status_unlimited": {
        "desc": "Web: Texto descargas ilimitadas",
        "vars": [],
        "default": "✅ Descargas ilimitadas",
    },
    "web_status_unlimited_desc": {
        "desc": "Web: Desc descargas ilimitadas",
        "vars": [],
        "default": "Tu nivel permite descargas sin restricciones",
    },
    "web_status_system": {
        "desc": "Web: Título estado sistema",
        "vars": [],
        "default": "Estado del Sistema",
    },
    "web_status_upgrade_btn": {
        "desc": "Web: Botón aumentar límite",
        "vars": [],
        "default": "Aumentar Límite de Descargas",
    },
    "web_downloads_unlimited": {
        "desc": "Web: Etiqueta ilimitado",
        "vars": [],
        "default": "∞ Ilimitadas",
    },
    "web_downloads_available": {
        "desc": "Web: Texto descargas disponibles",
        "vars": [],
        "default": "Descargas disponibles",
    },
    "web_downloads_today": {
        "desc": "Web: Texto descargas hoy",
        "vars": [],
        "default": "Descargas hoy",
    },
    "web_downloads_completed": {
        "desc": "Web: Texto completadas",
        "vars": ["[Cant]"],
        "default": "[Cant] completadas",
    },
    "web_downloads_remaining": {
        "desc": "Web: Texto restantes",
        "vars": ["[Cant]"],
        "default": "[Cant] restantes",
    },
    "web_downloads_reset_info": {
        "desc": "Web: Info reset",
        "vars": [],
        "default": "📊 Las estadísticas se resetean diariamente a las 00:00",
    },
    "web_downloads_history_title": {
        "desc": "Web: Título historial",
        "vars": [],
        "default": "Historial Reciente",
    },
    "web_downloads_history_sent": {
        "desc": "Web: Etiqueta enviado",
        "vars": [],
        "default": "Enviado",
    },
    "web_help_hero_title": {
        "desc": "Web: Título ayuda",
        "vars": [],
        "default": "¿Necesitas ayuda?",
    },
    "web_help_hero_desc": {
        "desc": "Web: Desc ayuda",
        "vars": [],
        "default": "Aquí encontrarás todo lo que necesitas saber sobre ZeePubBot",
    },
    "web_help_commands_title": {
        "desc": "Web: Título comandos",
        "vars": [],
        "default": "Comandos Disponibles",
    },
    "web_help_faq_title": {
        "desc": "Web: Título FAQ",
        "vars": [],
        "default": "Preguntas Frecuentes",
    },
    "web_help_support_title": {
        "desc": "Web: Título soporte",
        "vars": [],
        "default": "¿Aún necesitas ayuda?",
    },
    "web_help_support_desc": {
        "desc": "Web: Desc soporte",
        "vars": [],
        "default": "Nuestro equipo está aquí para ayudarte",
    },
    "web_help_support_btn": {
        "desc": "Web: Botón soporte",
        "vars": [],
        "default": "Contactar Soporte",
    },
}

# Global variables available in ALL templates
# Global variables documentation (used for /vars)
GLOBAL_VARIABLES = {
    "Usuario": {
        "Nombre": "Nombre del usuario (First Name) - Clickeable",
        "Alias": "Username del usuario (sin @)",
        "ID": "ID numérico del usuario",
        "Apodo": "Apodo personalizado (si tiene)",
    },
    "Estado": {
        "Nivel": "Rango oficial (Lector, VIP, etc.)",
        "Rol": "Función personalizada (Editor, etc.)",
        "Descargas": "Estado de descargas diarias",
        "ResetTime": "Tiempo para reinicio de cuota",
        "Expires": "Fecha de vencimiento de beneficios",
    },
    "Sistema": {
        "Fecha": "Fecha actual (YYYY-MM-DD)",
        "Hora": "Hora actual (HH:MM)",
        "VersionBot": "Versión del bot y hash commit",
        "BotNombre": "Nombre configurado del bot",
        "BotAlias": "Username del bot (@...)",
    },
    "Chat": {
        "ChatID": "ID del chat actual (Grupo/Canal/Privado)",
        "ChatTitulo": "Nombre del grupo o canal actual",
    },
}
