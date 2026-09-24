import asyncio
import html
import logging
import time

from telegram import (
    ChatMember,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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
        return uid in config.ADMIN_USERS

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
    ):
        """Procesa y coordina la bienvenida efímera al grupo, copia en privado y aviso a administradores."""
        chat_id = chat.id
        user_id = user.id

        # 1. Deduplicación por (chat_id, user_id) en ventana de 120 segundos
        now = time.time()
        self._recent_welcomes = {
            k: v for k, v in self._recent_welcomes.items() if now - v < 120
        }
        key = (chat_id, user_id)
        if key in self._recent_welcomes:
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

        # 3. Obtener mensaje personalizado si tiene slug configurado
        msg_data = None
        if group and group.welcome_msg_slug:
            msg_data = await custom_messages_repo.get_message(group.welcome_msg_slug)

        # 4. Obtener username del bot
        bot_user = await context.bot.get_me()
        bot_username = bot_user.username or "ZeePubBot"

        # 5. Enviar mensaje de bienvenida en grupo (efímero)
        await self._send_welcome_group(
            context, chat, user, msg_data, bot_username, reply_to_message_id
        )

        # 6. Enviar copia en privado al usuario
        await self._send_welcome_private(context, user, msg_data, bot_username)

        # 7. Notificar a los administradores del grupo
        asyncio.create_task(self._notify_admins(context.bot, chat_id, chat.title, user))

    async def _send_welcome_group(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat,
        user,
        msg_data,
        bot_username: str,
        reply_to_message_id: int | None = None,
    ):
        """Envía el mensaje de bienvenida efímero en el grupo y programa su autodestrucción."""
        chat_id = chat.id
        safe_name = html.escape(user.first_name or "Lector")
        sent_msg = None

        if msg_data and msg_data.text_content:
            text_to_send = msg_data.text_content.replace("[Nombre]", safe_name)
            text_to_send += "\n\n⏳ <i>Este mensaje en el grupo se autodestruirá en 2 minutos para mantener el chat limpio.</i>"
            try:
                sent_msg = await context.bot.send_message(
                    chat_id=chat_id,
                    text=text_to_send,
                    parse_mode="HTML",
                    reply_to_message_id=reply_to_message_id,
                )
            except Exception as e:
                logger.warning(
                    f"[GroupManager] Error enviando bienvenida custom en grupo: {e}"
                )
        elif msg_data and not msg_data.text_content:
            try:
                sent_msg = await context.bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=msg_data.source_chat_id,
                    message_id=msg_data.source_message_id,
                    reply_to_message_id=reply_to_message_id,
                )
            except Exception as e:
                logger.error(
                    f"[GroupManager] Error enviando copia de bienvenida en grupo: {e}"
                )
        else:
            text_group, reply_markup = build_welcome_message(
                user_name=user.first_name,
                bot_username=bot_username,
                is_ephemeral=True,
                is_private=False,
            )
            try:
                sent_msg = await context.bot.send_message(
                    chat_id=chat_id,
                    text=text_group,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                    reply_to_message_id=reply_to_message_id,
                )
            except Exception as e:
                logger.error(
                    f"[GroupManager] Error enviando bienvenida Rich Message en grupo: {e}"
                )

        # Programar autodestrucción (efímero) tras 120 segundos
        if sent_msg:
            asyncio.create_task(
                self._delete_message_after(
                    context.bot, chat_id, sent_msg.message_id, delay_seconds=120
                )
            )

    async def _delete_message_after(
        self, bot, chat_id: int, message_id: int, delay_seconds: int = 120
    ):
        """Elimina el mensaje de bienvenida tras el tiempo especificado para mantener limpio el grupo."""
        await asyncio.sleep(delay_seconds)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.info(
                f"[GroupManager] Mensaje efímero {message_id} en chat {chat_id} eliminado exitosamente."
            )
        except Exception as e:
            logger.debug(
                f"[GroupManager] No se pudo eliminar mensaje efímero {message_id} en {chat_id}: {e}"
            )

    async def _send_welcome_private(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        user,
        msg_data,
        bot_username: str,
    ):
        """Envía copia del mensaje de bienvenida por privado al usuario recién ingresado."""
        user_id = user.id
        safe_name = html.escape(user.first_name or "Lector")

        try:
            if msg_data and msg_data.text_content:
                text_to_send = msg_data.text_content.replace("[Nombre]", safe_name)
                await context.bot.send_message(
                    chat_id=user_id,
                    text=text_to_send,
                    parse_mode="HTML",
                )
            elif msg_data and not msg_data.text_content:
                await context.bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=msg_data.source_chat_id,
                    message_id=msg_data.source_message_id,
                )
            else:
                text_priv, reply_markup = build_welcome_message(
                    user_name=user.first_name,
                    bot_username=bot_username,
                    is_ephemeral=False,
                    is_private=True,
                )
                await context.bot.send_message(
                    chat_id=user_id,
                    text=text_priv,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
            logger.info(
                f"[GroupManager] Copia de bienvenida enviada por privado a {user_id} ({user.first_name})"
            )
        except Exception as e:
            # Telegram 403 Forbidden ocurre si el usuario nunca ha iniciado el bot en privado
            logger.info(
                f"[GroupManager] No se pudo enviar copia privada a {user_id} (el usuario aún no ha iniciado el bot en privado): {e}"
            )

    async def _notify_admins(self, bot, chat_id: int, chat_title: str | None, new_user):
        """Notifica a los administradores del grupo por privado sobre el ingreso del nuevo miembro."""
        safe_name = html.escape(new_user.first_name or "Usuario")
        username_str = f"(@{new_user.username})" if new_user.username else "(sin alias)"
        group_name = html.escape(chat_title or f"Chat {chat_id}")

        admin_notice = (
            f"🔔 <b>Nuevo Miembro en Grupo • ZeePubs</b>\n\n"
            f"📍 <b>Grupo:</b> {group_name}\n"
            f'👤 <b>Usuario:</b> <a href="tg://user?id={new_user.id}">{safe_name}</a> {username_str}\n'
            f"🆔 <b>ID:</b> <code>{new_user.id}</code>\n\n"
            f"<i>Se ha enviado la bienvenida en el grupo (efímera, 2 min) y copia a su chat privado.</i>"
        )

        notified_ids: set[int] = set()

        # 1. Obtener administradores del grupo de Telegram
        try:
            admins = await bot.get_chat_administrators(chat_id)
            for admin in admins:
                if (
                    admin.user
                    and not admin.user.is_bot
                    and admin.user.id not in notified_ids
                ):
                    try:
                        await bot.send_message(
                            chat_id=admin.user.id,
                            text=admin_notice,
                            parse_mode="HTML",
                        )
                        notified_ids.add(admin.user.id)
                    except Exception as ex:
                        logger.debug(
                            f"[GroupManager] Admin {admin.user.id} no alcanzable por DM: {ex}"
                        )
        except Exception as e:
            logger.warning(
                f"[GroupManager] Error obteniendo admins de chat {chat_id}: {e}"
            )

        # 2. Notificar a los administradores globales (config.ADMIN_USERS)
        for admin_id in getattr(config, "ADMIN_USERS", []):
            if admin_id not in notified_ids:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=admin_notice,
                        parse_mode="HTML",
                    )
                    notified_ids.add(admin_id)
                except Exception as ex:
                    logger.debug(
                        f"[GroupManager] Admin global {admin_id} no alcanzable por DM: {ex}"
                    )


def build_welcome_message(
    user_name: str,
    bot_username: str = "ZeePubBot",
    is_ephemeral: bool = False,
    is_private: bool = False,
) -> tuple[str, InlineKeyboardMarkup]:
    """Construye el mensaje de bienvenida oficial en formato Rich HTML (Telegram 7.0+)
    con blockquotes nativos y botones interactivos.
    """
    safe_name = html.escape(user_name or "Lector")

    text = (
        f"¡Bienvenido/a a la biblioteca de Zeepubs, <b>{safe_name}</b>! 📚🎴\n\n"
        f"Soy <b>ZeePub Bot</b>, tu asistente encargado de organizar las Novelas Ligeras y mantener el orden por aquí.\n\n"
        f"<blockquote>🎯 <b>Misiones principales:</b>\n"
        f"1. <b>Buscador Especializado:</b> Me conecto directo a nuestra biblioteca para entregarte los EPUBs exclusivos que nosotros mismos maquetamos.\n"
        f"2. <b>Moderador:</b> Cuidar que nuestra comunidad sea segura y divertida.</blockquote>\n\n"
        f"🚀 <b>¿Por dónde empezar?</b>\n"
    )

    if not is_private:
        text += f'— Toca aquí 👉 <a href="https://t.me/{bot_username}?start=bienvenida">/start</a> para activarme en privado.\n'

    text += (
        "— Usa <code>/ayuda</code> o <code>/help</code> para ver todo lo que puedo hacer por ti.\n"
        "— Escribe <code>/buscar &lt;título&gt;</code> seguido del nombre de la novela.\n"
        "— Consulta las <code>/reglas</code>, son pocas pero es necesario cumplirlas.\n\n"
        "<blockquote expandable>⚠️ <b>Nota Importante / Búsquedas:</b>\n"
        "Mi base de datos trabaja con los títulos internacionales, así que por favor realiza tus búsquedas preferentemente en <b>INGLÉS</b> o romanji para encontrar lo que necesitas (Ej: <code>/buscar That Time I Got Reincarnated as a Slime</code> en lugar de <i>'Y me reencarné en un slime'</i>).</blockquote>\n\n"
        "¡Ponte cómodo/a y disfruta de nuestras ediciones! ☕✨"
    )

    if is_ephemeral:
        text += "\n\n⏳ <i>Este mensaje en el grupo se autodestruirá en 2 minutos para mantener el chat limpio.</i>"

    buttons: list[list[InlineKeyboardButton]] = []
    if not is_private:
        buttons.append(
            [
                InlineKeyboardButton(
                    "🤖 Activar en Privado",
                    url=f"https://t.me/{bot_username}?start=bienvenida",
                ),
                InlineKeyboardButton("📜 Reglas", callback_data="nav_local|rules"),
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    "📚 Catálogo Completo", callback_data="nav_local|all_series"
                ),
            ]
        )
    else:
        buttons.append(
            [
                InlineKeyboardButton(
                    "📚 Catálogo Completo", callback_data="nav_local|all_series"
                ),
                InlineKeyboardButton("📜 Reglas", callback_data="nav_local|rules"),
            ]
        )
        buttons.append(
            [
                InlineKeyboardButton("ℹ️ Ayuda", callback_data="nav_local|help"),
                InlineKeyboardButton("🏠 Menú Principal", callback_data="volver_menu"),
            ]
        )

    reply_markup = InlineKeyboardMarkup(buttons)
    return text, reply_markup
