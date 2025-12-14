import logging
import os
from datetime import datetime
from typing import Dict, Callable, List, Optional, Any
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    BigInteger,
    Text,
    DateTime,
)
from sqlalchemy.sql import text  # Importar text explícitamente
from sqlalchemy.orm import declarative_base, sessionmaker
from telegram import Update, Message
from telegram.ext import ContextTypes, CommandHandler, ChatMemberHandler
from plugins.base_plugin import BasePlugin
from config.config_settings import config

logger = logging.getLogger(__name__)
Base = declarative_base()


class StoredMessage(Base):
    __tablename__ = "stored_messages"
    slug = Column(String(64), primary_key=True)
    source_chat_id = Column(BigInteger, nullable=False)
    source_message_id = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    text_content = Column(
        Text, nullable=True
    )  # Contenido capturado para reemplazo de variables
    created_at = Column(DateTime, default=datetime.utcnow)


class PluginSettings(Base):
    __tablename__ = "custom_messages_settings"
    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=True)


class CustomMessagesPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "custom_messages"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Permite guardar y reutilizar mensajes. Incluye bienvenida automática y comando saludo mejorado."

    def __init__(self):
        self.engine = None
        self.Session = None
        self.enabled = False

    async def initialize(self, bot_instance) -> bool:
        # Check env var directly or via os.environ if not in config object yet
        # Assuming config loads .env but we appended to it, might need reload or just os.getenv
        self.enabled = os.getenv("ENABLE_CUSTOM_MESSAGES", "False").lower() == "true"

        if not self.enabled:
            logger.info(
                "Plugin CustomMessages desactivado por configuración (ENABLE_CUSTOM_MESSAGES=False)."
            )
            return False

        # Initialize DB
        db_url = config.DATABASE_URL
        if not db_url:
            # Fallback to local sqlite like other services
            db_path = os.path.join("data", "custom_messages.db")
            db_url = f"sqlite:///{db_path}"

        try:
            self.engine = create_engine(db_url, future=True)
            Base.metadata.create_all(self.engine)

            # Migration: Ensure text_content column exists
            with self.engine.connect() as conn:
                try:
                    # Check if column exists by selecting it? Or just try adding it and ignore error
                    # SQLite doesn't support IF NOT EXISTS in ADD COLUMN effectively in all versions,
                    # but easiest is to try query it, catch error, then add.
                    # Or check pragma table_info.
                    if "sqlite" in db_url:
                        result = conn.execute(
                            text("PRAGMA table_info(stored_messages)")
                        )
                        columns = [
                            row[1] for row in result.fetchall()
                        ]  # row[1] is name
                        if "text_content" not in columns:
                            logger.info("Migrating DB: Adding text_content column...")
                            conn.execute(
                                text(
                                    "ALTER TABLE stored_messages ADD COLUMN text_content TEXT"
                                )
                            )
                    else:
                        # Postgres logic if using it (unlikely for this plugin default path but good practice)
                        pass
                except Exception as ex:
                    logger.warning(
                        f"Migration check failed (might be already up to date): {ex}"
                    )

            self.Session = sessionmaker(bind=self.engine)
            logger.info("Plugin CustomMessages: Base de datos inicializada.")

        except Exception as e:
            logger.error(f"Error inicializando BD del plugin: {e}")
            return False

        # Register Handlers Manually
        # bot_instance is actually 'app' from main.py, so it has .add_handler
        try:
            app = bot_instance
            app.add_handler(CommandHandler("add_msge", self.add_msge))
            app.add_handler(CommandHandler("list_msge", self.list_msge))
            app.add_handler(CommandHandler("send_msge", self.send_msge))
            app.add_handler(CommandHandler("saludo", self.saludo))
            app.add_handler(CommandHandler("set_welcome", self.set_welcome))

            # ChatMemberHandler for welcome message
            # MY_CHAT_MEMBER is triggered when bot is added/promoted/removed
            app.add_handler(
                ChatMemberHandler(
                    self.welcome_handler, ChatMemberHandler.MY_CHAT_MEMBER
                )
            )

            logger.info("Plugin CustomMessages: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin: {e}")
            return False

    async def cleanup(self) -> None:
        logger.info("Plugin CustomMessages limpiando recursos.")

    # --- Database Helpers ---
    def _save_message(self, slug, chat_id, message_id, description=None):
        with self.Session() as session:
            msg = session.get(StoredMessage, slug)
            if msg:
                msg.source_chat_id = chat_id
                msg.source_message_id = message_id
                msg.description = description
                # Si description contiene el texto real (pasado desde add_msge), lo guardamos en text_content tambien
                msg.text_content = description

            else:
                msg = StoredMessage(
                    slug=slug,
                    source_chat_id=chat_id,
                    source_message_id=message_id,
                    description=description,
                    text_content=description,  # Usamos description para pasar el texto en add_msge
                )
                session.add(msg)

            session.commit()

    def _get_message(self, slug):
        with self.Session() as session:
            return session.get(StoredMessage, slug)

    def _list_messages(self):
        with self.Session() as session:
            return session.query(StoredMessage).all()

    def _set_setting(self, key, value):
        with self.Session() as session:
            s = session.get(PluginSettings, key)
            if s:
                s.value = value
            else:
                s = PluginSettings(key=key, value=value)
                session.add(s)
            session.commit()

    def _get_setting(self, key):
        with self.Session() as session:
            s = session.get(PluginSettings, key)
            return s.value if s else None

    # --- Handlers ---

    async def add_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if not update.message.reply_to_message:
            await update.message.reply_text(
                "❌ Debes responder al mensaje que quieres guardar."
            )
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Uso: Responder al mensaje + /add_msge <id_unico>"
            )
            return

        slug = context.args[0].lower()
        original_msg = update.message.reply_to_message

        # Guardar source_chat_id y source_message_id
        # IMPORTANTE: Si es un grupo, source_chat_id es el id del grupo.
        # copy_message necesita permisos para ver ese chat.

        try:
            # Capturar texto o caption para guardarlo
            content_text = (
                original_msg.text_html
                or original_msg.caption_html
                or "Mensaje Multimedia"
            )

            self._save_message(
                slug,
                original_msg.chat_id,
                original_msg.message_id,
                description=content_text,  # Pasamos el texto como descripción/contenido
            )

            await update.message.reply_text(
                f"✅ Mensaje guardado como <code>{slug}</code>.", parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error guardando mensaje: {e}")
            await update.message.reply_text("❌ Error al guardar en base de datos.")

    async def list_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if context.args:
            # Preview mode
            slug = context.args[0].lower()
            msg = self._get_message(slug)
            if not msg:
                await update.message.reply_text("❌ Mensaje no encontrado.")
                return

            try:
                await context.bot.copy_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=msg.source_chat_id,
                    message_id=msg.source_message_id,
                )
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Error al previsualizar (¿Mensaje original borrado?): {e}"
                )
            return

        # List mode
        msgs = self._list_messages()
        if not msgs:
            await update.message.reply_text("📭 No hay mensajes guardados.")
            return

        text = "📂 <b>Mensajes Guardados:</b>\n\n"
        for m in msgs:
            text += f"🔹 <code>{m.slug}</code>\n"

        text += "\nUsa <code>/list_msge &lt;id&gt;</code> para ver uno."
        await update.message.reply_text(text, parse_mode="HTML")

    async def send_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if len(context.args) < 2:
            await update.message.reply_text("❌ Uso: /send_msge <id> <chat_id>")
            return

        slug = context.args[0].lower()
        target_chat_id = context.args[1]

        msg = self._get_message(slug)
        if not msg:
            await update.message.reply_text("❌ ID de mensaje no encontrado.")
            return

        try:
            await context.bot.copy_message(
                chat_id=target_chat_id,
                from_chat_id=msg.source_chat_id,
                message_id=msg.source_message_id,
            )
            await update.message.reply_text(f"✅ Enviado a {target_chat_id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error enviando: {e}")

    async def saludo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /saludo <chat_id> <id_guardado | texto libre>
        """
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        # Simple parsing for backward compatibility
        # But we need to support /saludo <chat_id> <slug> vs /saludo <chat_id> <text>
        # Algorithm:
        # 1. Split update.message.text to get args.
        # 2. Arg 0 = /saludo, Arg 1 = chat_id, Arg 2... = content

        text_content = update.message.text.replace("/saludo", "", 1).strip()
        parts = text_content.split(" ", 1)

        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Uso: /saludo <chat_id> <id_mensaje | texto>\n"
                "Ej: /saludo -100123 welcome_v1\n"
                "Ej: /saludo -100123 Hola amigos"
            )
            return

        target_chat_id = parts[0]
        content = parts[1]

        # Check if content matches a stored slug EXACTLY
        msg = self._get_message(content.strip().lower())

        if msg:
            # It IS a stored message
            try:
                await context.bot.copy_message(
                    chat_id=target_chat_id,
                    from_chat_id=msg.source_chat_id,
                    message_id=msg.source_message_id,
                )
                await update.message.reply_text(
                    f"✅ Mensaje guardado <code>{msg.slug}</code> enviado a {target_chat_id}",
                    parse_mode="HTML",
                )
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Error al enviar mensaje guardado: {e}"
                )
        else:
            # It is NOT a stored message, send as text (Legacy behavior)
            try:
                await context.bot.send_message(chat_id=target_chat_id, text=content)
                await update.message.reply_text(
                    f"✅ Mensaje de texto enviado a {target_chat_id}"
                )
            except Exception as e:
                await update.message.reply_text(f"❌ Error al enviar texto: {e}")

    async def set_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if not context.args:
            current = self._get_setting("welcome_msg_id")
            status = "Apagado" if not current else f"Activo (ID: {current})"
            await update.message.reply_text(
                f"👋 Bienvenida Automática: <b>{status}</b>\nUsa /set_welcome <id|off>",
                parse_mode="HTML",
            )
            return

        arg = context.args[0].lower()
        if arg == "off":
            self._set_setting("welcome_msg_id", "")
            await update.message.reply_text("👋 Bienvenida automática desactivada.")
        else:
            msg = self._get_message(arg)
            if not msg:
                await update.message.reply_text(
                    "❌ ID de mensaje no encontrado. Primero guárdalo con /add_msge"
                )
                return
            self._set_setting("welcome_msg_id", arg)
            await update.message.reply_text(
                f"👋 Bienvenida configurada con mensaje: <code>{arg}</code>",
                parse_mode="HTML",
            )

    async def welcome_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Triggered on MY_CHAT_MEMBER updates
        current_welcome_id = self._get_setting("welcome_msg_id")
        if not current_welcome_id:
            return

        result = update.my_chat_member
        new_state = result.new_chat_member.status
        old_state = result.old_chat_member.status

        # Check if bot was added (was not member/restricted/kicked, now is member/admin)
        from telegram.constants import ChatMemberStatus

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
            logger.info(
                f"Bot añadido a grupo {chat_id}. Enviando bienvenida si corresponde."
            )

            msg = self._get_message(current_welcome_id)
            if msg:
                try:
                    await context.bot.copy_message(
                        chat_id=chat_id,
                        from_chat_id=msg.source_chat_id,
                        message_id=msg.source_message_id,
                    )
                except Exception as e:
                    logger.error(
                        f"Error enviando bienvenida automática a {chat_id}: {e}"
                    )
