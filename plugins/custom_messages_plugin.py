import html
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import (
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
)

from config.config_settings import config
from core.db_manager_pg import pg_manager as db_manager
from plugins.base_plugin import BasePlugin
from repositories.custom_messages_repository import CustomMessagesRepository
from services.custom_messages_service import CustomMessagesService
from utils.helpers import get_thread_id
from utils.template_registry_data import GLOBAL_VARIABLES, TEMPLATE_REGISTRY

logger = logging.getLogger(__name__)


class CustomMessagesPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "custom_messages"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "Controller para gestión de mensajes personalizados mediante CustomMessagesService."

    def __init__(self):
        self.enabled = False
        self.service = None
        self._global_vars_cache: dict = {}

    async def initialize(self, bot_instance) -> bool:
        self.enabled = os.getenv("ENABLE_CUSTOM_MESSAGES", "True").lower() == "true"

        if not self.enabled:
            logger.info("Plugin CustomMessages desactivado por configuración (ENABLE_CUSTOM_MESSAGES=False).")
            return False

        try:
            repository = CustomMessagesRepository(db_manager)
            self.service = CustomMessagesService(repository, bot_instance.bot)

            # Inicialización de BD y caché a través del servicio si fuera necesario,
            # pero el plugin sigue siendo responsable de la infraestructura de BD del modelo
            from sqlalchemy.sql import text

            from models.custom_messages_models import Base

            if db_manager and hasattr(db_manager, "engine"):
                async with db_manager.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                    try:
                        await conn.execute(
                            text("ALTER TABLE stored_messages ADD COLUMN IF NOT EXISTS text_content TEXT")
                        )
                    except Exception as ex:
                        logger.warning(f"Migration check failed: {ex}")

            await self.service.initialize()
            logger.info("Plugin CustomMessages: Servicio inicializado.")

        except Exception as e:
            logger.error(f"Error inicializando servicio del plugin CustomMessages: {e}")
            return False

        try:
            app = bot_instance
            app.add_handler(CommandHandler("add_msge", self.add_msge))
            app.add_handler(CommandHandler("reset_msge", self.reset_msge))
            app.add_handler(CommandHandler("list_msge", self.list_msge))
            app.add_handler(CommandHandler("view_msge", self.view_msge))
            app.add_handler(CommandHandler("send_msge", self.send_msge))
            app.add_handler(CommandHandler("saludo", self.saludo))
            app.add_handler(CommandHandler("set_welcome", self.set_welcome))

            app.add_handler(ChatMemberHandler(self.welcome_handler, ChatMemberHandler.MY_CHAT_MEMBER))

            logger.info("Plugin CustomMessages: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin CustomMessages: {e}")
            return False

    async def cleanup(self) -> None:
        logger.info("Plugin CustomMessages limpiando recursos.")

    # --- API Wrapper for other plugins/services ---
    async def get_text(self, slug: str, default_text: str = None, user=None, **replacements) -> str:
        return await self.service.get_text(slug, default_text, user, **replacements)

    async def get_web_strings(self) -> dict[str, str]:
        return await self.service.get_web_strings()

    # --- Handlers ---

    async def add_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Debes responder al mensaje que quieres guardar.")
            return

        if not context.args:
            await update.message.reply_text("❌ Uso: Responder al mensaje + /add_msge <id_unico>")
            return

        slug = context.args[0].lower()
        original_msg = update.message.reply_to_message

        try:
            content_text = original_msg.text_html or original_msg.caption_html or "Mensaje Multimedia"
            await self.service.save_message(
                slug,
                original_msg.chat_id,
                original_msg.message_id,
                description=content_text,
            )
            await update.message.reply_text(f"✅ Mensaje guardado como <code>{slug}</code>.", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error guardando mensaje: {e}")
            await update.message.reply_text("❌ Error al guardar en base de datos.")

    async def list_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if context.args:
            target = context.args[0].lower()
            try:
                page = int(target)
                await self._show_message_list(update, context, page)
                return
            except ValueError:
                await self._preview_message(update, context, target)
                return

        await self._show_message_list(update, context, 1)

    async def _preview_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, slug: str):
        msg = await self.service.get_message(slug)
        entry = TEMPLATE_REGISTRY.get(slug)

        text_content = None
        source = "database"

        if msg and msg.text_content:
            text_content = msg.text_content
        elif entry and "default" in entry:
            text_content = entry["default"]
            source = "default"

        if not text_content and not (msg and not msg.text_content):
            await update.message.reply_text(f"❌ Mensaje '{slug}' no encontrado.")
            return

        # Check for optional target_uid for variable replacement testing
        target_uid = None
        if len(context.args) > 1:
            try:
                target_uid = int(context.args[1])
            except ValueError:
                pass

        if target_uid:
            try:
                user = None
                try:
                    member = await context.bot.get_chat_member(update.effective_chat.id, target_uid)
                    user = member.user
                except Exception:
                    chat = await context.bot.get_chat(target_uid)
                    user = chat

                text_sent = await self.service.get_text(slug, user=user)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text_sent,
                    parse_mode=ParseMode.HTML,
                    message_thread_id=get_thread_id(update),
                )
                return
            except Exception as e:
                logger.warning(f"Preview test vars failed: {e}")

        if source == "default" or (msg and msg.text_content):
            prefix = "⚠️ <b>Por defecto:</b>\n" if source == "default" else f"📂 <b>Personalizado ({slug}):</b>\n"
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{prefix}\n{html.escape(text_content)}",
                parse_mode=ParseMode.HTML,
                message_thread_id=get_thread_id(update),
            )
        elif msg:
            await context.bot.copy_message(
                chat_id=update.effective_chat.id,
                from_chat_id=msg.source_chat_id,
                message_id=msg.source_message_id,
                message_thread_id=get_thread_id(update),
            )

    async def _show_message_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
        limit = 10
        offset = (page - 1) * limit
        messages = await self.service.list_messages(limit, offset)

        if not messages and page == 1:
            await update.message.reply_text("📭 No hay mensajes personalizados guardados.")
            return

        text = f"📂 <b>Mensajes Personalizados (Pág {page})</b>\n\n"
        for m in messages:
            desc = (
                (m.description[:40] + "...") if m.description and len(m.description) > 40 else (m.description or "---")
            )
            text += f"• <code>{m.slug}</code>: {html.escape(desc)}\n"

        text += "\n<i>Para ver/previsualizar: /list_msge &lt;slug&gt;</i>"
        if len(messages) == limit:
            text += f"\n<i>Siguiente página: /list_msge {page + 1}</i>"

        await update.message.reply_text(text, parse_mode="HTML")

    async def view_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return
        if not context.args:
            await update.message.reply_text("❌ Uso: /view_msge <slug>")
            return
        await self._preview_message(update, context, context.args[0].lower())

    async def saludo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        text = await self.service.get_text("saludo", user=user)
        await update.message.reply_text(text, parse_mode="HTML", message_thread_id=get_thread_id(update))

    async def send_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ Uso: /send_msge <chat_id> [thread_id] <slug|texto>")
            return

        try:
            target_chat_id = int(args[0])
        except ValueError:
            await update.message.reply_text("❌ ID de chat inválido.")
            return

        possible_thread_id = args[1]
        message_thread_id = None
        content_start_index = 1

        try:
            tid = int(possible_thread_id)
            if tid > 0:
                message_thread_id = tid
                content_start_index = 2
        except ValueError:
            pass

        if len(args) <= content_start_index:
            await update.message.reply_text("❌ Falta el contenido del mensaje.")
            return

        content = " ".join(args[content_start_index:])
        slug = content.strip().lower()

        msg_db = await self.service.get_message(slug)
        is_template = (slug in TEMPLATE_REGISTRY) or (msg_db is not None)

        if is_template:
            try:
                if msg_db and not msg_db.text_content:
                    await context.bot.copy_message(
                        chat_id=target_chat_id,
                        from_chat_id=msg_db.source_chat_id,
                        message_id=msg_db.source_message_id,
                        message_thread_id=message_thread_id,
                    )
                else:
                    text_to_send = await self.service.get_text(slug)
                    await context.bot.send_message(
                        chat_id=target_chat_id,
                        text=text_to_send,
                        parse_mode="HTML",
                        message_thread_id=message_thread_id,
                    )
                await update.message.reply_text(f"✅ Mensaje <code>{slug}</code> enviado.", parse_mode="HTML")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
        else:
            try:
                await context.bot.send_message(
                    chat_id=target_chat_id,
                    text=content,
                    message_thread_id=message_thread_id,
                )
                await update.message.reply_text("✅ Texto enviado.")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")

    async def set_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if not context.args:
            current = await self.service.get_setting("welcome_msg_id")
            status = "Apagado" if not current else f"Activo (ID: {current})"
            await update.message.reply_text(f"👋 Bienvenida: <b>{status}</b>", parse_mode="HTML")
            return

        arg = context.args[0].lower()
        if arg == "off":
            await self.service.set_setting("welcome_msg_id", "")
            await update.message.reply_text("👋 Bienvenida desactivada.")
        else:
            if arg not in TEMPLATE_REGISTRY and not await self.service.get_message(arg):
                await update.message.reply_text("❌ ID no encontrado.")
                return
            await self.service.set_setting("welcome_msg_id", arg)
            await update.message.reply_text(f"👋 Bienvenida configurada: <code>{arg}</code>", parse_mode="HTML")

    async def reset_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return
        if not context.args:
            await update.message.reply_text("❌ Uso: /reset_msge <slug>")
            return
        slug = context.args[0].lower()
        try:
            if await self.service.delete_message(slug):
                await update.message.reply_text(f"✅ Mensaje <code>{slug}</code> restaurado.", parse_mode="HTML")
            else:
                await update.message.reply_text("❌ No encontrado o ya es default.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    # --- Private Helper Methods ---

    async def _get_message(self, slug: str):
        """Proxy al repositorio via servicio."""
        if self.service:
            return await self.service.get_message(slug)
        return None

    async def _get_setting(self, key: str) -> str | None:
        """Obtiene un ajuste del plugin via servicio."""
        if self.service:
            return await self.service.get_setting(key)
        return None

    async def _set_setting(self, key: str, value: str):
        """Guarda un ajuste del plugin via servicio."""
        if self.service:
            await self.service.set_setting(key, value)

    async def _set_global_var(self, key: str, value: str):
        """Guarda una variable global y actualiza el caché."""
        if self.service:
            await self.service.set_global_var(key, value)
            self._global_vars_cache[key] = value

    async def _del_global_var(self, key: str):
        """Elimina una variable global y actualiza el caché."""
        if self.service:
            await self.service.del_global_var(key)
            self._global_vars_cache.pop(key, None)

    def _get_template_categories(self) -> dict[str, list[str]]:
        """Agrupa los slugs de TEMPLATE_REGISTRY por su categoría."""
        categories: dict[str, list[str]] = {}
        for slug, info in TEMPLATE_REGISTRY.items():
            cat = info.get("cat", "general")
            categories.setdefault(cat, []).append(slug)
        return categories

    def _build_templates_keyboard(
        self,
        current_cat: str | None = None,
        page: int = 1,
        has_more: bool = False,
    ) -> InlineKeyboardMarkup:
        """Construye el teclado inline para el menú de plantillas."""
        buttons = []

        if current_cat is None:
            # Vista de categorías raíz
            categories = self._get_template_categories()
            for cat_name in sorted(categories.keys()):
                count = len(categories[cat_name])
                buttons.append(
                    [
                        InlineKeyboardButton(
                            f"📂 {cat_name.upper()} ({count})", callback_data=f"templates|cat|{cat_name}|1"
                        )
                    ]
                )
            buttons.append([InlineKeyboardButton("❌ Cerrar", callback_data="templates|close")])
        else:
            # Vista de plantillas dentro de una categoría
            nav_row = []
            if page > 1:
                nav_row.append(InlineKeyboardButton("⬅️ Ant", callback_data=f"templates|cat|{current_cat}|{page - 1}"))
            if has_more:
                nav_row.append(InlineKeyboardButton("Sig ➡️", callback_data=f"templates|cat|{current_cat}|{page + 1}"))
            if nav_row:
                buttons.append(nav_row)
            buttons.append([InlineKeyboardButton("🔙 Volver a Categorías", callback_data="templates|home")])

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

    async def templates_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            page = int(data[3]) if len(data) > 3 else 1
            page_size = 8  # templates per page

            categories = self._get_template_categories()
            slugs = categories.get(cat_name, [])

            # Paginate slugs
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paged_slugs = slugs[start_idx:end_idx]
            has_more = len(slugs) > end_idx

            text = f"📂 <b>{cat_name.upper()}</b> (Pag {page})\n\n"
            text += "Usa <code>/add_msge &lt;slug&gt;</code> para personalizar.\n\n"

            for slug in paged_slugs:
                info = TEMPLATE_REGISTRY[slug]
                vars_str = ", ".join(info["vars"]) if info["vars"] else "Ninguna"
                entry = f"🔹 <b>{slug}</b>\n"
                entry += f"   📝 {info['desc']}\n"
                entry += f"   💲 Vars: <code>{vars_str}</code>\n\n"
                text += entry

            keyboard = self._build_templates_keyboard(current_cat=cat_name, page=page, has_more=has_more)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
            return

    async def set_var(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Uso: /set_var <Variable> <Valor>\nEjemplo: /set_var CanalOficial https://t.me/mi_canal"
            )
            return

        key = context.args[0]
        # Remove brackets if user typed them
        key = key.replace("[", "").replace("]", "")
        value = " ".join(context.args[1:])

        await self._set_global_var(key, value)
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
        await self._del_global_var(key)
        await update.message.reply_text(f"🗑 Variable global <code>[{key}]</code> eliminada.", parse_mode="HTML")

    async def vars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista las variables globales disponibles organizadas por categorías."""
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        text = "💲 <b>Variables de Plantillas</b>\n\n"
        text += "Puedes usar cualquiera de estas variables encerrándola entre corchetes, ej: <code>[Nombre]</code>\n\n"

        for cat, variables in GLOBAL_VARIABLES.items():
            text += f"📂 <b>{cat}:</b>\n"
            for key, desc in variables.items():
                text += f"🔹 <code>[{key}]</code>: {desc}\n"
            text += "\n"

        # Admin Vars
        text += "🛠 <b>Personalizadas (Admin /set_var):</b>\n"
        if not self._global_vars_cache:
            text += "<i>(Ninguna definida)</i>\n"
        else:
            for k, v in self._global_vars_cache.items():
                text += f"🔸 <code>[{k}]</code>: {html.escape(v)}\n"

        await update.message.reply_text(text, parse_mode="HTML")

    async def template_vars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Legacy alias for /vars
        await self.vars(update, context)

    async def welcome_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Triggered on MY_CHAT_MEMBER updates
        current_welcome_id = await self._get_setting("welcome_msg_id")

        # Fallback to default presentation if configured explicitly or if we want auto-welcome
        if not current_welcome_id:
            current_welcome_id = "bot_presentation"

        result = update.my_chat_member
        new_state = result.new_chat_member.status
        old_state = result.old_chat_member.status

        # Check if bot was added (was not member/restricted/kicked, now is member/admin)

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
            logger.info(f"Bot añadido a grupo {chat_id}. Enviando bienvenida si corresponde.")

            # Use get_text to support default templates too, not just DB copy
            # But copy_message is richer for multimedia.
            # Strategy: Try DB message first (for copy). If not, send text.

            msg = await self._get_message(current_welcome_id)
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
                    text = await self.get_text(current_welcome_id)
                    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Error enviando bienvenida (text): {e}")
