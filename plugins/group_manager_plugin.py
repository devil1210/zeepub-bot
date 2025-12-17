import logging
import os
import html
from sqlalchemy import create_engine, Column, String, Boolean, Integer, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker
from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import ContextTypes, CommandHandler, ChatMemberHandler, MessageHandler, filters
from plugins.base_plugin import BasePlugin
from config.config_settings import config
from utils.helpers import get_thread_id
from plugins.custom_messages_plugin import StoredMessage  # To access message model

logger = logging.getLogger(__name__)
Base = declarative_base()


class GroupSettings(Base):
    __tablename__ = "group_settings"
    chat_id = Column(BigInteger, primary_key=True)
    is_authorized = Column(Boolean, default=False)
    welcome_msg_slug = Column(String(64), nullable=True)


class GroupManagerPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "group_manager"

    @property
    def version(self) -> str:
        return "1.0.2"

    @property
    def description(self) -> str:
        return "Gestión de grupos: Autorización y mensajes de bienvenida."

    def __init__(self):
        self.engine = None
        self.Session = None
        self.enabled = False
        # We need access to CustomMessages DB to fetch welcome messages
        self.custom_msg_engine = None
        self.CustomMsgSession = None

    async def initialize(self, bot_instance) -> bool:
        self.enabled = config.ENABLE_GROUP_MANAGER

        if not self.enabled:
            logger.info("Plugin GroupManager desactivado por configuración.")
            return False

        # Initialize Local DB for Group Settings
        self._init_db()

        # Initialize Connection to CustomMessages DB (read-only purpose)
        self._init_custom_msg_db()

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
                MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.welcome_new_members_message)
            )

            logger.info("Plugin GroupManager: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin GroupManager: {e}")
            return False

    def _init_db(self):
        # Determine DB URL (Shared Postgres or Local SQLite)
        db_url = config.DATABASE_URL
        if not db_url:
            db_path = os.path.join("data", "group_manager.db")
            db_url = f"sqlite:///{db_path}"

        self.engine = create_engine(db_url, future=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def _init_custom_msg_db(self):
        # Same logic as CustomMessagesPlugin to find the DB
        db_url = config.DATABASE_URL
        if not db_url:
            # Assumes standard path used by CustomMessagesPlugin
            db_path = os.path.join("data", "custom_messages.db")
            db_url = f"sqlite:///{db_path}"

        try:
            self.custom_msg_engine = create_engine(db_url, future=True)
            self.CustomMsgSession = sessionmaker(bind=self.custom_msg_engine)
        except Exception as e:
            logger.warning(f"GroupManager no pudo conectar a CustomMessages DB: {e}")

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

        session = self.Session()
        try:
            group = session.query(GroupSettings).filter_by(chat_id=chat_id).first()
            if not group:
                group = GroupSettings(chat_id=chat_id)
                session.add(group)

            group.is_authorized = True
            session.commit()
            await update.message.reply_text(
                f"✅ Grupo {chat_id} autorizado. El bot ahora está activo allí."
            )
        except Exception as e:
            logger.error(f"Error authorizing group: {e}")
            await update.message.reply_text("❌ Error al autorizar el grupo.")
        finally:
            session.close()

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

        session = self.Session()
        try:
            group = session.query(GroupSettings).filter_by(chat_id=chat_id).first()
            if group:
                group.is_authorized = False
                session.commit()
            await update.message.reply_text(
                f"⛔ Grupo {chat_id} revocado. El bot dejará de actuar allí."
            )
        except Exception as e:
            logger.error(f"Error revoking group: {e}")
        finally:
            session.close()

    async def set_group_welcome(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        if not self._is_admin(update.effective_user.id):
            return

        if not context.args:
            await update.message.reply_text("Uso: /set_group_welcome <slug_mensaje>")
            return

        slug = context.args[0].lower()
        # Default to current chat if no second arg (not implemented yet, stick to current chat)
        chat_id = update.effective_chat.id

        # Verify slug exists
        if not self._slug_exists(slug):
            await update.message.reply_text(
                f"❌ El mensaje '{slug}' no existe en la base de datos de mensajes."
            )
            return

        session = self.Session()
        try:
            group = session.query(GroupSettings).filter_by(chat_id=chat_id).first()
            if not group:
                # Require explicit authorization first? Or auto-create?
                # Let's auto-create but warn if not authorized.
                group = GroupSettings(chat_id=chat_id)
                session.add(group)
                msg_extra = (
                    " (Nota: El grupo aún no está autorizado, usa /authorize_group)"
                )
            else:
                msg_extra = ""

            group.welcome_msg_slug = slug
            session.commit()
            await update.message.reply_text(
                f"✅ Mensaje de bienvenida establecido a: {slug}{msg_extra}"
            )
        except Exception as e:
            logger.error(f"Error setting welcome: {e}")
            await update.message.reply_text("❌ Error guardando configuración.")
        finally:
            session.close()

    async def reglas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra las reglas del grupo (desde mensaje guardado 'reglas' o default)."""
        thread_id = get_thread_id(update)
        # Intentar cargar mensaje personalizado "reglas"
        msg = self._get_stored_message("reglas")

        if msg:
            # Si existe el mensaje, lo enviamos (copia o texto)
            # Priorizamos texto si existe para permitir edición
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
            # Fallback
            await update.message.reply_text(
                "📜 <b>Reglas del Grupo</b>\n\n"
                "1. Respeto mutuo.\n"
                "2. No spam.\n"
                "3. Disfrutar de la lectura.\n\n"
                "<i>(Configura este mensaje guardando uno con slug 'reglas')</i>",
                parse_mode="HTML",
                message_thread_id=thread_id,
            )

    def _slug_exists(self, slug):
        if not self.CustomMsgSession:
            return False
        session = self.CustomMsgSession()
        try:
            exists = (
                session.query(StoredMessage).filter_by(slug=slug).first() is not None
            )
            return exists
        except Exception as e:
            logger.error(f"Error checking slug: {e}")
            return False
        finally:
            session.close()

    def _get_stored_message(self, slug):
        if not self.CustomMsgSession:
            return None
        session = self.CustomMsgSession()
        try:
            return session.query(StoredMessage).filter_by(slug=slug).first()
        finally:
            session.close()

    async def track_chats(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Track when bot is added/removed from groups and send introduction."""
        result = self._extract_status_change(update.my_chat_member)
        if result is None:
            return

        was_member, is_member = result
        chat_id = update.effective_chat.id

        # Bot was just added to the group
        if not was_member and is_member:
            logger.info(f"Bot added to group {chat_id}")
            
            # Try to fetch custom introduction message
            msg_data = self._get_stored_message("bot_presentation")
            
            if msg_data:
                # Use custom message
                try:
                    if hasattr(msg_data, "text_content") and msg_data.text_content:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=msg_data.text_content,
                            parse_mode="HTML"
                        )
                    else:
                        await context.bot.copy_message(
                            chat_id=chat_id,
                            from_chat_id=msg_data.source_chat_id,
                            message_id=msg_data.source_message_id
                        )
                except Exception as e:
                    logger.error(f"Error sending custom introduction to {chat_id}: {e}")
            else:
                # Fallback to default introduction message
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
                        chat_id=chat_id,
                        text=intro_message,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Error sending default introduction to {chat_id}: {e}")
                
        # Bot was removed from the group
        elif was_member and not is_member:
            logger.info(f"Bot removed from group {chat_id}")

    async def welcome_member(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Greet new members in authorized groups."""
        result = self._extract_status_change(update.chat_member)
        if result is None:
            return

        was_member, is_member = result

        # Check if it's a new member join
        if not was_member and is_member:
            chat_id = update.effective_chat.id

            # Check authorization
            session = self.Session()
            try:
                group = session.query(GroupSettings).filter_by(chat_id=chat_id).first()
                if not group or not group.is_authorized or not group.welcome_msg_slug:
                    return
                slug = group.welcome_msg_slug
            finally:
                session.close()

            # Fetch message content
            msg_data = self._get_stored_message(slug)
            if not msg_data:
                return

            new_member = update.chat_member.new_chat_member.user
            await self._send_welcome(context, chat_id, new_member, msg_data)

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

    async def welcome_new_members_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle new_chat_members service message."""
        if not update.message or not update.message.new_chat_members:
            return
            
        chat_id = update.effective_chat.id
        
        # Check authorization strictly
        session = self.Session()
        try:
             group = session.query(GroupSettings).filter_by(chat_id=chat_id).first()
             if not group or not group.is_authorized or not group.welcome_msg_slug:
                 return
             slug = group.welcome_msg_slug
        finally:
             session.close()

        msg_data = self._get_stored_message(slug)
        if not msg_data:
            return

        reply_to = update.message.message_id

        for user in update.message.new_chat_members:
            if user.is_bot:
                continue
            await self._send_welcome(context, chat_id, user, msg_data, reply_to_message_id=reply_to)

    async def _send_welcome(self, context, chat_id, user, msg_data, reply_to_message_id=None):
        """Helper to send the welcome message to a specific user."""
        first_name = user.first_name
        safe_name = html.escape(first_name)

        if hasattr(msg_data, "text_content") and msg_data.text_content:
            text_to_send = msg_data.text_content.replace("[Nombre]", safe_name)
            try:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=text_to_send, 
                    parse_mode="HTML",
                    reply_to_message_id=reply_to_message_id
                )
                return
            except Exception as e:
                logger.warning(f"Failed to send text welcome: {e}")

        # Fallback: Copy
        try:
            await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=msg_data.source_chat_id,
                message_id=msg_data.source_message_id,
                reply_to_message_id=reply_to_message_id
            )
        except Exception as e:
            logger.error(f"Error sending welcome copy: {e}")
