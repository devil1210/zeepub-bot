import asyncio
import html
import logging
import time

from telegram import (
    ChatMember,
    ChatMemberUpdated,
    Update,
)
from telegram.ext import (
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config.config_settings import config
from plugins.base_plugin import BasePlugin
from repositories.custom_messages_repository import custom_messages_repo
from repositories.group_settings_repository import group_settings_repo
from services.library_ui import build_welcome_rich_blocks
from services.rich_message_service import RichMessageService
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


class GroupManagerPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "group_manager"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "Gestión de grupos asíncrona: Autorización y mensajes de bienvenida."

    def __init__(self):
        super().__init__()
        self.enabled = False
        self._recent_welcomes: dict[tuple[int, int], float] = {}

    async def initialize(self, bot_instance) -> bool:
        self.enabled = config.ENABLE_GROUP_MANAGER

        if not self.enabled:
            logger.info("Plugin GroupManager desactivado por configuración.")
            return False

        try:
            app = bot_instance
            # Admin commands
            app.add_handler(CommandHandler("authorize_group", self.authorize_group))
            app.add_handler(CommandHandler("revoke_group", self.revoke_group))
            app.add_handler(CommandHandler("set_group_welcome", self.set_group_welcome))
            app.add_handler(CommandHandler("test_welcome", self.test_welcome))
            # Rules command
            app.add_handler(CommandHandler("reglas", self.reglas))
            app.add_handler(CommandHandler("rules", self.reglas))

            # Events
            app.add_handler(
                ChatMemberHandler(self.track_chats, ChatMemberHandler.MY_CHAT_MEMBER)
            )
            app.add_handler(
                ChatMemberHandler(self.welcome_member, ChatMemberHandler.CHAT_MEMBER)
            )
            # Add MessageHandler for service messages (when bot is not admin or update is simple)
            app.add_handler(
                MessageHandler(
                    filters.StatusUpdate.NEW_CHAT_MEMBERS,
                    self.welcome_new_members_message,
                )
            )

            logger.info("Plugin GroupManager (Async): Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin GroupManager: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    def _is_admin(self, uid: int) -> bool:
        return uid in config.ADMIN_USERS or (
            getattr(config, "SUPER_ADMIN_ID", None) is not None
            and uid == config.SUPER_ADMIN_ID
        )

    async def test_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra de prueba del mensaje efímero de bienvenida (solo para administradores)."""
        if not update.effective_user or not self._is_admin(update.effective_user.id):
            return
        chat = update.effective_chat
        user = update.effective_user
        reply_to_message_id = (
            update.effective_message.message_id if update.effective_message else None
        )
        await self._process_welcome(
            context,
            chat,
            user,
            reply_to_message_id=reply_to_message_id,
            force=True,
        )

    async def authorize_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_admin(update.effective_user.id):
            return

        # Check for arguments (e.g., /authorize_group -100123456789)
        if context.args:
            try:
                chat_id = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ ID de chat inválido.")
                return
        else:
            chat_id = update.effective_chat.id
            if update.effective_chat.type not in ["group", "supergroup"]:
                await update.message.reply_text(
                    "⛔ Usa este comando en un grupo o proporciona un ID: /authorize_group <id>"
                )
                return

        success = await group_settings_repo.set_authorized(chat_id, True)
        if success:
            await update.message.reply_text(
                f"✅ Grupo {chat_id} autorizado. El bot ahora está activo allí."
            )
        else:
            await update.message.reply_text("❌ Error al autorizar el grupo.")

    async def revoke_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_admin(update.effective_user.id):
            return

        if context.args:
            try:
                chat_id = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ ID de chat inválido.")
                return
        else:
            chat_id = update.effective_chat.id

        success = await group_settings_repo.set_authorized(chat_id, False)
        if success:
            await update.message.reply_text(
                f"⛔ Grupo {chat_id} revocado. El bot dejará de actuar allí."
            )
        else:
            await update.message.reply_text("❌ Error al revocar el grupo.")

    async def set_group_welcome(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        if not self._is_admin(update.effective_user.id):
            return

        if not context.args:
            await update.message.reply_text("Uso: /set_group_welcome <slug_mensaje>")
            return

        slug = context.args[0].lower()
        chat_id = update.effective_chat.id

        # Verify slug exists
        msg_exists = await custom_messages_repo.get_message(slug)
        if not msg_exists:
            await update.message.reply_text(
                f"❌ El mensaje '{slug}' no existe en la base de datos de mensajes."
            )
            return

        group = await group_settings_repo.get_by_chat_id(chat_id)
        msg_extra = ""
        if not group or not group.is_authorized:
            msg_extra = " (Nota: El grupo aún no está autorizado, usa /authorize_group)"

        success = await group_settings_repo.set_welcome_slug(chat_id, slug)
        if success:
            await update.message.reply_text(
                f"✅ Mensaje de bienvenida establecido a: {slug}{msg_extra}"
            )
        else:
            await update.message.reply_text("❌ Error guardando configuración.")

    async def reglas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra las reglas del grupo (desde mensaje guardado 'reglas' o Rich Message por defecto)."""
        thread_id = get_thread_id(update)
        # Intentar cargar mensaje personalizado "reglas"
        msg = await custom_messages_repo.get_message("reglas")

        if msg:
            if msg.text_content:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=msg.text_content,
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
            else:
                await context.bot.copy_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=msg.source_chat_id,
                    message_id=msg.source_message_id,
                    message_thread_id=thread_id,
                )
        else:
            from services.library_ui import build_rules_rich_blocks
            from services.rich_message_service import RichMessageService

            blocks = build_rules_rich_blocks()
            res = await RichMessageService.send_rich_message(
                chat_id=update.effective_chat.id,
                blocks=blocks,
                message_thread_id=thread_id,
            )
            if not res or not res.get("ok"):
                await update.message.reply_text(
                    "📜 <b>Normas de la Comunidad • ZeePubs</b>\n\n"
                    "1. Respeto mutuo y trato cordial.\n"
                    "2. Cero spam o contenido no autorizado.\n"
                    "3. Uso responsable de las búsquedas y descargas.",
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )

    async def track_chats(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Track when bot is added/removed from groups and send introduction."""
        result = self._extract_status_change(update.my_chat_member)
        if result is None:
            return

        was_member, is_member = result
        chat_id = update.effective_chat.id

        if not was_member and is_member:
            logger.info(f"Bot added to group {chat_id}")
            msg_data = await custom_messages_repo.get_message("bot_presentation")

            if msg_data:
                try:
                    if msg_data.text_content:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=msg_data.text_content,
                            parse_mode="HTML",
                        )
                    else:
                        await context.bot.copy_message(
                            chat_id=chat_id,
                            from_chat_id=msg_data.source_chat_id,
                            message_id=msg_data.source_message_id,
                        )
                except Exception as e:
                    logger.error(f"Error sending custom introduction to {chat_id}: {e}")
            else:
                intro_message = (
                    "👋 ¡Hola! Soy ZeepubBot.\n\n"
                    "📚 Ayudo a compartir y gestionar libros en formato EPUB.\n\n"
                    "🔐 <b>Nota importante:</b> Por defecto, necesito que un administrador "
                    "autorice este grupo para que pueda funcionar completamente.\n\n"
                    "📝 <b>Comandos para administradores:</b>\n"
                    "• /authorize_group - Autorizar este grupo\n"
                    "• /set_group_welcome &lt;slug&gt; - Configurar mensaje de bienvenida\n"
                    "• /reglas o /rules - Ver las reglas del grupo\n\n"
                    "¿Necesitas ayuda? Usa /help para ver todos los comandos disponibles.\n\n"
                    "<i>Tip: Puedes personalizar este mensaje usando /save_msge bot_presentation</i>"
                )
                try:
                    await context.bot.send_message(
                        chat_id=chat_id, text=intro_message, parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(
                        f"Error sending default introduction to {chat_id}: {e}"
                    )

    async def welcome_member(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Greet new members in groups (ChatMemberUpdated event)."""
        result = self._extract_status_change(update.chat_member)
        if result is None:
            return

        was_member, is_member = result
        if not was_member and is_member:
            chat = update.effective_chat
            user = update.chat_member.new_chat_member.user
            if user.is_bot:
                return

            await self._process_welcome(context, chat, user)

    def _extract_status_change(self, chat_member_update: ChatMemberUpdated):
        """Helper to Determine if user joined or left."""
        status_change = chat_member_update.difference().get("status")
        old_is_member, new_is_member = chat_member_update.difference().get(
            "is_member", (None, None)
        )

        if status_change is None:
            return None

        old_status, new_status = status_change
        was_member = old_status in [
            ChatMember.MEMBER,
            ChatMember.OWNER,
            ChatMember.ADMINISTRATOR,
        ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)

        is_member = new_status in [
            ChatMember.MEMBER,
            ChatMember.OWNER,
            ChatMember.ADMINISTRATOR,
        ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

        return was_member, is_member

    async def welcome_new_members_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle new_chat_members service message."""
        if not update.message or not update.message.new_chat_members:
            return

        chat = update.effective_chat
        reply_to = update.message.message_id
        for user in update.message.new_chat_members:
            if user.is_bot:
                continue
            await self._process_welcome(
                context, chat, user, reply_to_message_id=reply_to
            )

    async def _process_welcome(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat,
        user,
        reply_to_message_id: int | None = None,
        force: bool = False,
    ):
        """Envía el mensaje de bienvenida efímero en el grupo (receiver_user_id) al nuevo usuario y a los administradores."""
        chat_id = chat.id
        user_id = user.id

        # 1. Deduplicación por (chat_id, user_id) en ventana de 60 segundos
        now = time.time()
        self._recent_welcomes = {
            k: v for k, v in self._recent_welcomes.items() if now - v < 60
        }
        key = (chat_id, user_id)
        if not force and key in self._recent_welcomes:
            logger.debug(
                f"[GroupManager] Bienvenida omitida por duplicado reciente para {user_id} en {chat_id}"
            )
            return
        self._recent_welcomes[key] = now

        # 2. Verificar autorización si el grupo está explícitamente revocado
        group = await group_settings_repo.get_by_chat_id(chat_id)
        if group and group.is_authorized is False:
            logger.info(
                f"[GroupManager] Grupo {chat_id} revocado explícitamente; se omite bienvenida."
            )
            return

        # 3. Obtener bloques para el mensaje enriquecido
        msg_data = None
        if group and group.welcome_msg_slug:
            msg_data = await custom_messages_repo.get_message(group.welcome_msg_slug)

        user_name = user.first_name or "Lector"
        if msg_data and msg_data.text_content:
            custom_text = msg_data.text_content.replace(
                "[Nombre]", html.escape(user_name)
            )
            user_blocks = [
                {
                    "type": "heading",
                    "size": 2,
                    "text": f"🎴 ¡Bienvenido/a, {html.escape(user_name)}! 📚",
                },
                {"type": "paragraph", "text": custom_text},
                {
                    "type": "buttons",
                    "align": "center",
                    "buttons": [
                        {
                            "text": "📚 Catálogo",
                            "callback_data": "nav_local|all_series",
                        },
                        {"text": "📜 Reglas", "callback_data": "nav_local|rules"},
                        {"text": "ℹ️ Ayuda", "callback_data": "nav_local|help"},
                    ],
                },
                {"type": "divider"},
                {"type": "paragraph", "text": "#ZeePubs #Bienvenida"},
            ]
        else:
            user_blocks = build_welcome_rich_blocks(
                user_name=user_name, is_admin_copy=False
            )

        # 4. Enviar Rich Message efímero en el grupo al nuevo miembro (Only visible to you)
        try:
            res = await RichMessageService.send_rich_message(
                chat_id=chat_id,
                blocks=user_blocks,
                receiver_user_id=user_id,
            )
            if res and res.get("ok"):
                logger.info(
                    f"[GroupManager] Rich Message efímero de bienvenida enviado en grupo {chat_id} a {user_id} ({user.first_name})"
                )
            else:
                logger.warning(
                    f"[GroupManager] Falló send_rich_message de bienvenida para {user_id} en {chat_id}: {res}"
                )
        except Exception as e:
            logger.warning(
                f"[GroupManager] Error enviando bienvenida efímera a {user_id} en {chat_id}: {e}"
            )

        # 5. Enviar Rich Message efímero en el grupo a los administradores (Only visible to you)
        admin_blocks = build_welcome_rich_blocks(
            user_name=user_name, is_admin_copy=True
        )
        asyncio.create_task(
            self._send_ephemeral_to_admins(
                context.bot,
                chat_id,
                user,
                admin_blocks,
            )
        )

    async def _send_ephemeral_to_admins(
        self,
        bot,
        chat_id: int,
        new_user,
        admin_blocks: list[dict],
    ):
        """Envía el Rich Message efímero en el grupo a cada administrador para que también les aparezca a ellos (Only visible to you)."""
        admin_ids: set[int] = set()

        # Obtener administradores del grupo
        try:
            admins = await bot.get_chat_administrators(chat_id)
            for admin in admins:
                if (
                    admin.user
                    and not admin.user.is_bot
                    and admin.user.id != new_user.id
                ):
                    admin_ids.add(admin.user.id)
        except Exception as e:
            logger.warning(
                f"[GroupManager] Error obteniendo administradores de {chat_id}: {e}"
            )

        # Añadir administradores configurados en config.ADMIN_USERS
        for admin_uid in getattr(config, "ADMIN_USERS", []):
            if admin_uid != new_user.id:
                admin_ids.add(admin_uid)

        # Añadir SUPER_ADMIN_ID
        if (
            getattr(config, "SUPER_ADMIN_ID", None)
            and config.SUPER_ADMIN_ID != new_user.id
        ):
            admin_ids.add(config.SUPER_ADMIN_ID)

        logger.info(
            f"[GroupManager] Enviando bienvenida efímera Rich Message a {len(admin_ids)} administradores en grupo {chat_id}: {admin_ids}"
        )

        for admin_id in admin_ids:
            try:
                res = await RichMessageService.send_rich_message(
                    chat_id=chat_id,
                    blocks=admin_blocks,
                    receiver_user_id=admin_id,
                )
                if res and res.get("ok"):
                    logger.info(
                        f"[GroupManager] Bienvenida efímera Rich Message entregada al admin {admin_id} en grupo {chat_id}"
                    )
                else:
                    logger.warning(
                        f"[GroupManager] No se pudo enviar bienvenida efímera Rich Message al admin {admin_id}: {res}"
                    )
            except Exception as ex:
                logger.warning(
                    f"[GroupManager] Error enviando bienvenida efímera al admin {admin_id} en {chat_id}: {ex}"
                )
