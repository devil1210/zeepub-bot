import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from utils.command_registry import COMMANDS_REGISTRY, HELP_CATEGORIES

logger = logging.getLogger(__name__)


class HelpService:
    @staticmethod
    def get_main_help_keyboard(user_role: str = "user") -> InlineKeyboardMarkup:
        """Builds the main help menu with categories."""
        keyboard = []
        row = []

        # Filter categories based on role
        visible_cats = ["home", "content", "donations", "community", "config"]
        if user_role in ["staff", "admin"]:
            visible_cats.append("admin")
        if user_role == "admin":
            visible_cats.append("staff")

        for cat_key in visible_cats:
            cat = HELP_CATEGORIES.get(cat_key)
            if not cat:
                continue

            button = InlineKeyboardButton(f"{cat['icon']} {cat['title']}", callback_data=f"help_cat:{cat_key}")
            row.append(button)

            if len(row) == 2:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_category_keyboard(category_key: str, user_role: str = "user") -> InlineKeyboardMarkup:
        """Builds a keyboard with commands for a specific category."""
        keyboard = []
        row = []

        commands = [(cmd, data) for cmd, data in COMMANDS_REGISTRY.items() if data.get("cat") == category_key]

        # Sort commands alphabetically
        commands.sort(key=lambda x: x[0])

        for cmd_name, data in commands:
            button = InlineKeyboardButton(f"/{cmd_name}", callback_data=f"help_cmd:{cmd_name}")
            row.append(button)

            if len(row) == 2:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        # Back to main menu button
        keyboard.append([InlineKeyboardButton("⬅️ Volver al Menú", callback_data="help_main")])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_command_detail_keyboard(command_name: str) -> InlineKeyboardMarkup:
        """Builds a keyboard for command details (just a back button)."""
        cmd_data = COMMANDS_REGISTRY.get(command_name)
        cat_key = cmd_data.get("cat", "home") if cmd_data else "home"

        keyboard = [
            [InlineKeyboardButton("⬅️ Volver a Categoría", callback_data=f"help_cat:{cat_key}")],
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="help_main")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def build_main_help_text() -> str:
        """Returns the main help welcome text."""
        return (
            "<b>📖 Centro de Ayuda Zeepub</b>\n\n"
            "¡Bienvenido! Aquí puedes explorar todas las funciones disponibles del bot. "
            "Selecciona una categoría para ver los comandos relacionados.\n\n"
            "<i>Usa los botones de abajo para navegar.</i>"
        )

    @staticmethod
    def build_category_help_text(category_key: str) -> str:
        """Returns text for a specific category."""
        cat = HELP_CATEGORIES.get(category_key)
        title = cat["title"] if cat else category_key.capitalize()
        return (
            f"<b>{title}</b>\n\n"
            f"Estos son los comandos disponibles en la categoría <i>{category_key}</i>. "
            "Haz clic en uno para ver detalles, uso y ejemplos."
        )

    @staticmethod
    def build_command_detail_text(command_name: str) -> str:
        """Returns detailed information about a command."""
        cmd = COMMANDS_REGISTRY.get(command_name)
        if not cmd:
            return "❌ Comando no encontrado."

        text = (
            f"<b>Comando:</b> /{command_name}\n"
            f"<b>Descripción:</b> {cmd['desc']}\n\n"
            f"<b>Información detallada:</b>\n{cmd['long_desc']}\n\n"
            f"<b>Uso:</b> <code>{cmd['usage']}</code>\n"
            f"<b>Ejemplo:</b> <code>{cmd['example']}</code>"
        )
        return text
