import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config.config_settings import config
from plugins.base_plugin import BasePlugin
from repositories.publication_repository import PublicationRepository

logger = logging.getLogger(__name__)

# Estados del ConversationHandler
(
    MENU,
    CREATE_NAME,
    CREATE_CONTENT,
    CREATE_PLATFORM,
    DELETE_SELECT,
) = range(5)


class TemplatesPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "templates_manager"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Gestión de plantillas de publicación desde Telegram"

    def __init__(self):
        self.app: Application | None = None
        self.pub_repo = PublicationRepository()
        self.user_states = {}  # Para guardar temporalmente datos de la creación

    async def initialize(self, bot_instance: Application) -> bool:
        self.app = bot_instance

        # ConversationHandler para gestionar templates
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("pub_templates", self.start_templates)],
            states={
                MENU: [CallbackQueryHandler(self.handle_menu_selection, pattern="^tpl_")],
                CREATE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_name)],
                CREATE_PLATFORM: [CallbackQueryHandler(self.receive_platform, pattern="^plt_")],
                CREATE_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_content)],
                DELETE_SELECT: [CallbackQueryHandler(self.delete_template, pattern="^del_tpl_")],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CallbackQueryHandler(self.cancel, pattern="^tpl_cancel$"),
            ],
            per_user=True,
            per_chat=False,
        )

        self.app.add_handler(conv_handler)
        logger.info(f"Plugin {self.name} inicializado correctamente.")
        return True

    async def cleanup(self) -> None:
        logger.info(f"Plugin {self.name} desactivado.")

    def _is_staff(self, user_id: int) -> bool:
        return user_id in config.ADMIN_USERS or user_id in config.STAFF_USERS

    async def start_templates(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        if not self._is_staff(user_id):
            await update.effective_message.reply_text("⛔ No tienes permisos para usar este comando.")
            return ConversationHandler.END

        await self._show_main_menu(update, context)
        return MENU

    async def _show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback: bool = False):
        keyboard = [
            [
                InlineKeyboardButton("📝 Nueva Plantilla", callback_data="tpl_create"),
                InlineKeyboardButton("📋 Ver Plantillas", callback_data="tpl_list"),
            ],
            [
                InlineKeyboardButton("🗑️ Borrar Plantilla", callback_data="tpl_delete"),
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="tpl_cancel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "⚙️ **Gestión de Plantillas de Publicación**\n\nSelecciona una opción:"

        if is_callback and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    async def handle_menu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "tpl_create":
            await query.edit_message_text(
                "📝 **Nueva Plantilla**\n\nEscribe el **nombre** de la plantilla (ej: *Lanzamiento VIP*):\n\n/cancel para abortar.",
                parse_mode="Markdown",
            )
            return CREATE_NAME

        elif data == "tpl_list":
            templates = await self.pub_repo.get_templates()
            if not templates:
                await query.edit_message_text("📋 No hay plantillas creadas. Usa /pub_templates para volver al menú.")
                return ConversationHandler.END

            text = "📋 **Lista de Plantillas**\n\n"
            for t in templates:
                text += f"▪️ **{t.name}** ({t.platform})\n`ID: {t.id}`\n\n"

            keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="tpl_back")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return MENU

        elif data == "tpl_delete":
            templates = await self.pub_repo.get_templates()
            if not templates:
                await query.edit_message_text("🗑️ No hay plantillas para borrar.")
                return ConversationHandler.END

            keyboard = []
            for t in templates:
                keyboard.append([InlineKeyboardButton(f"❌ {t.name} ({t.platform})", callback_data=f"del_tpl_{t.id}")])
            keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="tpl_back")])

            await query.edit_message_text(
                "🗑️ Selecciona la plantilla a borrar:", reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return DELETE_SELECT

        elif data == "tpl_back":
            await self._show_main_menu(update, context, True)
            return MENU

        return MENU

    async def receive_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        name = update.message.text.strip()
        self.user_states[update.effective_user.id] = {"name": name}

        keyboard = [
            [InlineKeyboardButton("Telegram", callback_data="plt_telegram")],
            [InlineKeyboardButton("Discord", callback_data="plt_discord")],
        ]
        await update.effective_message.reply_text(
            "Selecciona la plataforma para esta plantilla:", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CREATE_PLATFORM

    async def receive_platform(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        platform = query.data.split("_")[1]

        user_id = update.effective_user.id
        if user_id in self.user_states:
            self.user_states[user_id]["platform"] = platform

        await query.edit_message_text(
            f"Plataforma seleccionada: **{platform}**\n\nAhora envía el **contenido** de la plantilla. Puedes usar variables como `{{title}}`, `{{author}}`, etc.\n\n/cancel para abortar.",
            parse_mode="Markdown",
        )
        return CREATE_CONTENT

    async def receive_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        content = update.message.text
        user_id = update.effective_user.id

        if user_id not in self.user_states:
            await update.effective_message.reply_text("Hubo un error de estado. Usa /pub_templates de nuevo.")
            return ConversationHandler.END

        name = self.user_states[user_id].get("name", "Sin Nombre")
        platform = self.user_states[user_id].get("platform", "telegram")

        from models.communications import PublicationTemplate

        template = PublicationTemplate(name=name, content=content, platform=platform, extra_config={})
        await self.pub_repo.create_template(template)

        del self.user_states[user_id]

        await update.effective_message.reply_text(
            f"✅ **Plantilla '{name}' creada con éxito!**\n\nYa puedes seleccionarla en la interfaz web.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    async def delete_template(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        template_id = int(query.data.replace("del_tpl_", ""))
        success = await self.pub_repo.delete_template(template_id)

        if success:
            await query.edit_message_text("✅ Plantilla borrada con éxito.")
        else:
            await query.edit_message_text("❌ Error al borrar plantilla (podría estar en uso).")

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text("Operación cancelada.")
        else:
            await update.effective_message.reply_text("Operación cancelada.")

        if update.effective_user.id in self.user_states:
            del self.user_states[update.effective_user.id]

        return ConversationHandler.END
