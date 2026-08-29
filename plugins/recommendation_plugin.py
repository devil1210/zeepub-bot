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
        self.plugin_manager = bot_instance.plugin_manager  # Plugin manager is attached to app/bot in bot.py

        # Register handlers directly to the application
        # Note: bot_instance is actually the 'application' object in bot.py logic
        app = bot_instance

        app.add_handler(CommandHandler("recommend", self.command_recommend))
        app.add_handler(CommandHandler("settings", self.command_settings))
        app.add_handler(CallbackQueryHandler(self.handle_settings_callback, pattern="^settings_"))

        return True

    async def cleanup(self) -> None:
        pass

    async def command_recommend(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Genera recomendaciones personalizadas en formato Rich Message."""
        uid = update.effective_user.id
        thread_id = update.effective_message.message_thread_id if update.effective_message else None
        from services.user_service import get_effective_user
        from services.rich_message_service import RichMessageService
        from core.state_manager import state_manager
        import uuid

        user_info = await get_effective_user(uid)

        if user_info.get("role") not in ("admin", "staff"):
            await update.message.reply_text("⛔ Esta función está en Beta exclusiva para Staff.")
            return

        recs = await RecommendationService.get_recommendations(uid, limit=4)

        if not recs:
            await update.message.reply_text(
                "😢 No encontré recomendaciones obvias. ¡Sigue leyendo para que aprenda más de ti!"
            )
            return

        st = state_manager.get_user_state(uid)
        st["libros"] = st.get("libros", {})

        table_rows = []
        buttons = []

        for book in recs:
            title = book.get("title") or "Novela"
            author = book.get("author") or "Desconocido"
            rating = book.get("rating_average", 0)
            local_id = book.get("id") or book.get("hash") or book.get("book_hash")

            key = uuid.uuid4().hex[:8]
            st["libros"][key] = {
                "titulo": title,
                "autor": author,
                "descarga": book.get("filepath"),
                "portada": book.get("cover") or book.get("cover_low") or book.get("cover_medium"),
                "hash": local_id,
                "volume": book.get("volume"),
            }

            table_rows.append([
                {"text": f"📖 {title[:28]}", "align": "left"},
                {"text": f"⭐ {rating:.1f}" if rating else "—", "align": "right"},
            ])
            buttons.append({"text": f"📕 {title[:25]}...", "callback_data": f"lib|{key}"})

        blocks = [
            {
                "type": "heading",
                "size": 2,
                "text": "💡 Recomendaciones para Ti • ZeePubs",
            },
            {
                "type": "paragraph",
                "text": "Basado en tu historial y preferencias de lectura, seleccionamos estas obras:",
            },
            {
                "type": "table",
                "is_bordered": True,
                "is_striped": True,
                "is_compact": True,
                "cells": table_rows,
            },
        ]

        # Agregar botones en pares
        for i in range(0, len(buttons), 2):
            row = buttons[i : i + 2]
            blocks.append({
                "type": "buttons",
                "align": "center",
                "buttons": row,
            })

        blocks.extend([
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {"text": "📚 Catálogo", "callback_data": "nav_local|all_series"},
                    {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                ],
            },
            {"type": "divider"},
            {"type": "paragraph", "text": "#ZeePubs #Recomendaciones"},
        ])

        res = await RichMessageService.send_rich_message(
            chat_id=update.effective_chat.id,
            blocks=blocks,
            message_thread_id=thread_id,
        )

        if not res or not res.get("ok"):
            await update.message.reply_text("💡 <b>Tus Recomendaciones:</b>", parse_mode="HTML")

    async def command_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menú de configuración de usuario."""
        uid = update.effective_user.id
        settings = await get_user_settings(uid)

        recomm_enabled = settings.get("recommendations_enabled", False)

        status_icon = "✅" if recomm_enabled else "❌"
        action = "enable" if not recomm_enabled else "disable"

        text = "⚙️ <b>Configuración Personal</b>\n\nAquí puedes gestionar tus preferencias."

        keyboard = [
            [
                InlineKeyboardButton(
                    f"{status_icon} Recomendaciones Semanales",
                    callback_data=f"settings_toggle_recomm|{action}",
                )
            ]
        ]

        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    async def handle_settings_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception:
                pass  # Identical content

            await query.answer(f"Configuración guardada: {status_icon}")
