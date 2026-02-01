# Reuse existing sending logic or custom card
# from services.telegram_service import enviar_libro_directo
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from plugins.base_plugin import BasePlugin
from services.recommendation_service import RecommendationService
from services.user_service import get_user_settings, update_user_setting

logger = logging.getLogger(__name__)


class RecommendationPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "recommendations"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Sistema de recomendaciones personalizadas y configuración de usuario."

    async def initialize(self, bot_instance) -> bool:
        self.bot_instance = bot_instance
        self.plugin_manager = (
            bot_instance.plugin_manager
        )  # Plugin manager is attached to app/bot in bot.py

        # Register handlers directly to the application
        # Note: bot_instance is actually the 'application' object in bot.py logic
        app = bot_instance

        app.add_handler(CommandHandler("recommend", self.command_recommend))
        app.add_handler(CommandHandler("settings", self.command_settings))
        app.add_handler(
            CallbackQueryHandler(self.handle_settings_callback, pattern="^settings_")
        )

        return True

    async def cleanup(self) -> None:
        pass

    async def command_recommend(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Genera recomendaciones inmediatas."""
        uid = update.effective_user.id
        from services.user_service import get_effective_user

        user_info = await get_effective_user(uid)

        if user_info.get("role") not in ("admin", "staff"):
            await update.message.reply_text(
                "⛔ Esta función está en Beta exclusiva para Staff."
            )
            return

        await update.message.reply_text("🤔 Analizando tus gustos...")

        recs = await RecommendationService.get_recommendations(uid, limit=3)

        if not recs:
            await update.message.reply_text(
                "😢 No encontré recomendaciones obvias. ¡Sigue leyendo para que aprenda más de ti!"
            )
            return

        await update.message.reply_text(
            "💡 <b>Tengo estas sugerencias para ti:</b>", parse_mode="HTML"
        )

        # Enviar fichas simplificadas
        for book in recs:
            # Construir tarjeta simple con botón de descarga
            caption = (
                f"📚 <b>{book['title']}</b>\n"
                f"👤 {book['author']}\n"
                f"⭐ {book.get('rating_average', 0):.1f} ({book.get('rating_count', 0)} votos)\n"
            )

            # Botón para descargar
            local_id = book.get("id")
            kb = []
            if local_id:
                # Use standard flow: lib|local_{id}
                kb = [
                    [
                        InlineKeyboardButton(
                            "📥 Ver Libro", callback_data=f"lib|local_{local_id}"
                        )
                    ]
                ]

            # Enviar portada si hay path
            sent = False
            if book.get("cover_path") and book["cover_path"].startswith("/"):
                try:
                    # Check file existence to avoid errors
                    import os

                    if os.path.exists(book["cover_path"]):
                        await context.bot.send_photo(
                            chat_id=uid,
                            photo=open(book["cover_path"], "rb"),
                            caption=caption,
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup(kb),
                        )
                        sent = True
                except Exception:
                    pass

            if not sent:
                await context.bot.send_message(
                    chat_id=uid,
                    text=caption,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(kb),
                )

    async def command_settings(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Menú de configuración de usuario."""
        uid = update.effective_user.id
        settings = await get_user_settings(uid)

        recomm_enabled = settings.get("recommendations_enabled", False)

        status_icon = "✅" if recomm_enabled else "❌"
        action = "enable" if not recomm_enabled else "disable"

        text = (
            "⚙️ <b>Configuración Personal</b>\n\nAquí puedes gestionar tus preferencias."
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    f"{status_icon} Recomendaciones Semanales",
                    callback_data=f"settings_toggle_recomm|{action}",
                )
            ]
        ]

        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )

    async def handle_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        data = query.data
        uid = update.effective_user.id

        if data.startswith("settings_toggle_recomm|"):
            action = data.split("|")[1]
            new_state = action == "enable"

            await update_user_setting(uid, "recommendations_enabled", new_state)

            # Refresh menu
            settings = await get_user_settings(uid)
            recomm_enabled = settings.get("recommendations_enabled", False)
            status_icon = "✅" if recomm_enabled else "❌"
            next_action = "disable" if recomm_enabled else "enable"

            keyboard = [
                [
                    InlineKeyboardButton(
                        f"{status_icon} Recomendaciones Semanales",
                        callback_data=f"settings_toggle_recomm|{next_action}",
                    )
                ]
            ]

            try:
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception:
                pass  # Identical content

            await query.answer(f"Configuración guardada: {status_icon}")
