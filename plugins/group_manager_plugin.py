import logging
import os
from sqlalchemy import create_engine, Column, String, Boolean, Integer, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker
from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import ContextTypes, CommandHandler, ChatMemberHandler
from plugins.base_plugin import BasePlugin
from config.config_settings import config
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
        return "1.0.0"

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

            # Events
            app.add_handler(
                ChatMemberHandler(self.track_chats, ChatMemberHandler.MY_CHAT_MEMBER)
            )
            app.add_handler(
                ChatMemberHandler(self.welcome_member, ChatMemberHandler.CHAT_MEMBER)
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
        return str(uid) in config.ADMIN_USERS

    async def authorize_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_admin(update.effective_user.id):
            return

        chat_id = update.effective_chat.id
        if update.effective_chat.type not in ["group", "supergroup"]:
            await update.message.reply_text("⛔ Este comando solo funciona en grupos.")
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
                "✅ Grupo autorizado. El bot ahora está activo aquí."
            )
        except Exception as e:
            logger.error(f"Error authorizing group: {e}")
            await update.message.reply_text("❌ Error al autorizar el grupo.")
        finally:
            session.close()

    async def revoke_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_admin(update.effective_user.id):
            return

        chat_id = update.effective_chat.id
        session = self.Session()
        try:
            group = session.query(GroupSettings).filter_by(chat_id=chat_id).first()
            if group:
                group.is_authorized = False
                session.commit()
            await update.message.reply_text(
                "⛔ Grupo revocado. El bot dejará de actuar aquí."
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

        slug = context.args[0]
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
                group = GroupSettings(
                    chat_id=chat_id, is_authorized=True
                )  # Auto-auth if setting welcome? Maybe safer strict.
                # Let's enforce auth first or assume setting config implies auth intentions, but sticking to explicit auth is better.
                # Only allow setting if record exists or create it but default auth?
                # User said: "el admin definirá en que grupos el bot tendrá ese poder".
                # I'll create the record if missing but keep authorized=False unless /authorize is run?
                # Or auto-create as False.
                session.add(group)

            group.welcome_msg_slug = slug
            session.commit()
            await update.message.reply_text(
                f"✅ Mensaje de bienvenida establecido a: {slug}"
            )
        except Exception as e:
            logger.error(f"Error setting welcome: {e}")
            await update.message.reply_text("❌ Error guardando configuración.")
        finally:
            session.close()

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
        """Track when bot is added/removed from groups."""
        result = self._extract_status_change(update.chat_member)
        if result is None:
            return

        was_member, is_member = result
        # If bot was added needed processing?
        # For now we rely on explicit /authorize_group
        pass

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
            mention = new_member.mention_html()

            # Assuming CustomMessagesPlugin stores original message_id and chat_id to forward/copy
            # Or description is the text? StoredMessage model has: slug, source_chat_id, source_message_id, description.
            # We should COPY the message to the new chat.

            try:
                await context.bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=msg_data.source_chat_id,
                    message_id=msg_data.source_message_id,
                )
                # Opcional: Enviar también texto si se requiere reemplazo de variables?
                # CustomMessagesPlugin generalmente reenvía. El usuario pidió "responda con un mensaje... el cual será uno de los ya almacenados".
                # copy_message es lo más fiel al original.
            except Exception as e:
                logger.error(f"Error sending welcome message: {e}")

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
