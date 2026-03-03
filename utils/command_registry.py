from typing import Any

# --- HELP CATEGORIES ---
HELP_CATEGORIES = {
    "home": {"title": "🏠 Inicio", "icon": "🏠"},
    "content": {"title": "📚 Biblioteca", "icon": "📚"},
    "donations": {"title": "☕ Donaciones / VIP", "icon": "⭐"},
    "community": {"title": "👥 Comunidad / Redes", "icon": "📢"},
    "admin": {"title": "🛠️ Administración", "icon": "🛠️"},
    "staff": {"title": "🛡️ Staff / Moderación", "icon": "🛡️"},
    "config": {"title": "⚙️ Configuración", "icon": "⚙️"},
}

# --- COMMAND REGISTRY ---
COMMANDS_REGISTRY: dict[str, dict[str, Any]] = {
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
    "settings": {
        "cat": "home",
        "desc": "Configuración personal",
        "long_desc": "Accede al menú de configuración para gestionar tus preferencias, como las recomendaciones semanales.",
        "usage": "/settings",
        "example": "/settings",
    },
    # --- Content ---
    "search": {
        "cat": "content",
        "desc": "Buscar libros",
        "long_desc": "Busca libros en la biblioteca. Puedes buscar por Título, Autor o Serie. Los resultados mostrarán un botón para descargar.\\n\\nTip: Sé específico para mejores resultados.",
        "usage": "/search <término>",
        "example": "/search Brandon Sanderson",
    },
    "catalog": {
        "cat": "content",
        "desc": "Ver catálogo completo",
        "long_desc": "Accede al catálogo completo de libros disponibles en la biblioteca, organizados por fecha o popularidad.",
        "usage": "/catalog",
        "example": "/catalog",
    },
    "random": {
        "cat": "content",
        "desc": "Libro aleatorio",
        "long_desc": "Obtén una recomendación de un libro aleatorio de la biblioteca para descubrir nuevas lecturas.",
        "usage": "/random",
        "example": "/random",
    },
    "series": {
        "cat": "content",
        "desc": "Explorar por series",
        "long_desc": "Muestra un listado de todas las novelas organizadas por series para facilitar la navegación.",
        "usage": "/series",
        "example": "/series",
    },
    "history": {
        "cat": "content",
        "desc": "Tu historial",
        "long_desc": "Muestra la lista de los últimos libros que has descargado o consultado.",
        "usage": "/history",
        "example": "/history",
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
    "canjear": {
        "cat": "donations",
        "desc": "Canjear código",
        "long_desc": "Permite canjear códigos promocionales o de regalo para obtener niveles VIP o beneficios exclusivos.",
        "usage": "/canjear <código>",
        "example": "/canjear VIP1MES-1234",
    },
    # --- Community ---
    "canal": {
        "cat": "community",
        "desc": "Canal oficial",
        "long_desc": "Enlace directo a nuestro canal oficial de noticias y actualizaciones.",
        "usage": "/canal",
        "example": "/canal",
    },
    "grupo": {
        "cat": "community",
        "desc": "Grupo de discusión",
        "long_desc": "Enlace para unirte a nuestro grupo de comunidad donde puedes hablar sobre libros y recibir soporte.",
        "usage": "/grupo",
        "example": "/grupo",
    },
    "reglas": {
        "cat": "community",
        "desc": "Reglas del grupo",
        "long_desc": "Muestra las normas de convivencia de la comunidad Zeepub.",
        "usage": "/reglas",
        "example": "/reglas",
    },
    # --- Config ---
    "notifications": {
        "cat": "config",
        "desc": "Gestión notificaciones",
        "long_desc": "Activa o desactiva las notificaciones sobre nuevos lanzamientos, actualizaciones de series que sigues y noticias del bot.",
        "usage": "/notifications <on|off>",
        "example": "/notifications on",
    },
    # --- Admin ---
    "stats": {
        "cat": "admin",
        "desc": "Estadísticas globales",
        "long_desc": "Muestra estadísticas del bot: usuarios totales, descargas, libros en biblioteca y rendimiento del sistema.",
        "usage": "/stats",
        "example": "/stats",
    },
    "broadcast": {
        "cat": "staff",
        "desc": "Mensaje global",
        "long_desc": "Envía un mensaje a todos los usuarios registrados del bot. Reservado para anuncios críticos.",
        "usage": "/broadcast <mensaje>",
        "example": "/broadcast Se ha añadido la nueva serie de 'One Piece'.",
    },
    "upload_epub": {
        "cat": "staff",
        "desc": "Subir libro",
        "long_desc": "Inicia el proceso interactivo para subir un nuevo EPUB a la biblioteca. Responde al archivo con el comando.",
        "usage": "/upload_epub",
        "example": "Usa /upload_epub respondiendo a un archivo .epub",
    },
}
