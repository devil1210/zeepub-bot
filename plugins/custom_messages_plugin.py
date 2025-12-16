import logging
import os
import html
import re
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
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, ChatMemberHandler
from plugins.base_plugin import BasePlugin
from config.config_settings import config
from utils.helpers import get_thread_id

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


# Registry for available templates
TEMPLATE_REGISTRY = {
    "banned_message": {
        "desc": "Mensaje para usuario baneado",
        "vars": ["[Fecha]"],
        "default": "⛔ Estás <b>baneado</b> del bot.{{if Fecha}} Hasta: <b>[Fecha]</b>{{endif}}",
    },
    "evil_password_success": {
        "desc": "Contraseña correcta (Modo Evil)",
        "vars": [],
        "default": "✅ Contraseña correcta. Elige destino:",
    },
    "evil_password_fail": {
        "desc": "Contraseña incorrecta (Modo Evil)",
        "vars": [],
        "default": "❌ Contraseña incorrecta.",
    },
    "search_no_results": {
        "desc": "Búsqueda sin resultados",
        "vars": ["[Termino]"],
        "default": "🔍 Mmm, no encontré nada para: [Termino]",
    },
    "private_default_fallback": {
        "desc": "Respuesta por defecto en chat privado",
        "vars": [],
        "default": "Usa /start para comenzar o selecciona una opción del menú.",
    },
    "start_welcome_unlimited": {
        "desc": "Bienvenida /start (Ilimitado)",
        "vars": ["[Nombre]"],
        "default": "👋 ¡Hola [Nombre]! Comencemos.\n\n✅ Tienes descargas ilimitadas.",
    },
    "start_welcome_limited": {
        "desc": "Bienvenida /start (Limitado)",
        "vars": ["[Nombre]", "[Descargas]"],
        "default": "👋 ¡Hola [Nombre]! Comencemos.\n\n⚡️ Te quedan [Descargas] descargas hoy.",
    },
    "evil_mode_prompt": {
        "desc": "Pregunta de destino (Admin -> Evil)",
        "vars": [],
        "default": "🔧 Modo Evil: ¿Dónde quieres publicar?",
    },
    "evil_password_prompt": {
        "desc": "Solicitud de contraseña",
        "vars": [],
        "default": "🔒 Modo Privado. Por favor, ingresa la contraseña:",
    },
    "cancel_confirmation": {
        "desc": "Confirmación de cancelación",
        "vars": [],
        "default": "✅ ¡Entendido! Operación cancelada.",
    },
    "donate_message": {
        "desc": "Mensaje comando /donar",
        "vars": ["[Nombre]", "[DonationUrl]"],
        "default": "💸 <b>Apoya el Mantenimiento del Bot</b>\n\nHola [Nombre], si te gusta el servicio, considera apoyar con una donación para cubrir los costos del servidor.\n\n<a href='[DonationUrl]'>☕ Invítame un café en Ko-fi</a>\n\n¡Gracias por tu apoyo!",
    },
    "levels_message": {
        "desc": "Mensaje comando /niveles",
        "vars": ["[white]", "[vip]", "[premium]", "[duration]"],
        "default": "📊 <b>Niveles de Usuario</b>\n\n⬜ <b>White</b>: [white] descargas/día\n⭐ <b>VIP</b>: [vip] descargas/día\n✨ <b>Premium</b>: [premium] descargas/día\n\nDuración Premium: [duration] días por donación.",
    },
    "bot_closing": {
        "desc": "Mensaje al cerrar menú",
        "vars": ["[Nombre]"],
        "default": "👋 Gracias por usar el bot.",
    },
    "donation_success": {
        "desc": "Confirmación de donación reportada",
        "vars": ["[Nombre]"],
        "default": "✅ <b>Notificación enviada</b>\n\nUn administrador revisará tu donación pronto y actualizará tu nivel.\n¡Muchas gracias por tu apoyo! ❤️",
    },
    "donation_admin_alert": {
        "desc": "Alerta a adminds sobre donación",
        "vars": ["[Nombre]", "[Alias]", "[ID]"],
        "default": "💰 <b>Nueva Donación Reportada</b>\n\n👤 <b>Usuario:</b> [Nombre]\n{{if Alias}}🔗 <b>Alias:</b> @[Alias]\n{{endif}}🆔 <b>ID:</b> <code>[ID]</code>\n\nEl usuario ha indicado que realizó una donación en Ko-fi.\nPor favor verifica y usa <code>/nivel</code> (si existiera) o actualiza manualmente.",
    },
    "search_instructions_legacy": {
        "desc": "Instrucciones de búsqueda (Usuario normal)",
        "vars": [],
        "default": "🔍 Para buscar, usa el comando:\n\n<code>/search término de búsqueda</code>\n\nEjemplo: <code>/search harry potter</code>",
    },
    "help_main_header": {
        "desc": "Encabezado principal de /help",
        "vars": ["[Nombre]"],
        "default": "👋 <b>Centro de Ayuda</b>\nHola [Nombre], aquí tienes los comandos disponibles:",
    },
    "status_message": {
        "desc": "Mensaje de estado (/status)",
        "vars": ["[Nivel]", "[Descargas]", "[ResetTime]", "[Expires]"],
        "default": "🤖 <b>ZeePub Bot</b> [VersionBot]\n\n📊 <b>Tu Estado</b>\n\n👤 <b>Usuario:</b> [Nombre]\n🆔 <b>ID:</b> [ID]\n⭐ <b>Nivel:</b> [Nivel]\n{{if Expires}}📅 <b>Vence:</b> [Expires]\n{{endif}}📉 <b>Descargas:</b> [Descargas]\n{{if ResetTime}}⏳ <b>Reinicio en:</b> [ResetTime]\n{{endif}}",
    },
}

# Global variables available in ALL templates
GLOBAL_VARIABLES = {
    "Nombre": "Nombre del usuario (First Name)",
    "Alias": "Username del usuario (sin @)",
    "ID": "ID numérico del usuario",
    "Fecha": "Fecha actual (YYYY-MM-DD)",
    "Hora": "Hora actual (HH:MM)",
    "VersionBot": "Versión actual del bot (ej: v3.7.2)",
}


class CustomMessagesPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "custom_messages"

    @property
    def version(self) -> str:
        return "1.1.0"

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

            app.add_handler(CommandHandler("templates", self.templates))
            app.add_handler(CommandHandler("template_vars", self.template_vars))

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
                    text_content=description,  # Usamos description para pasar el texto como descripción/contenido
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

    # --- Helper Methods for Template System ---

    def get_text(
        self, slug: str, default_text: str = None, user=None, **replacements
    ) -> str:
        """
        Recupera el texto de un mensaje guardado por su slug.
        Orden de prioridad:
        1. Base de Datos (Personalizado)
        2. default_text (Argumento legado, opcional)
        3. TEMPLATE_REGISTRY explicit default
        4. Cadena vacía

        Realiza el reemplazo de variables en el formato [Variable].
        """
        msg = self._get_message(slug.lower())

        final_text = None
        if msg and msg.text_content:
            final_text = msg.text_content

        # Fallbacks
        if not final_text:
            if default_text:
                final_text = default_text
            else:
                # Look in registry
                entry = TEMPLATE_REGISTRY.get(slug)
                if entry and "default" in entry:
                    final_text = entry["default"]

        if not final_text:
            return ""

        # 1. Inject Global Variables if user is provided
        vars_to_use = replacements.copy()

        # Date/Time are always available
        from datetime import datetime

        now = datetime.now()
        vars_to_use["Fecha"] = now.strftime("%Y-%m-%d")
        vars_to_use["Hora"] = now.strftime("%H:%M")

        from utils.helpers import get_version_string

        vars_to_use["VersionBot"] = get_version_string()

        if user:
            vars_to_use["Nombre"] = user.first_name or "Usuario"
            vars_to_use["Alias"] = user.username  # Can be None, works with {{if Alias}}
            vars_to_use["ID"] = str(user.id)

        # 2. Conditional Logic: {{if Var}}...{{endif}}
        # We process this BEFORE simple replacement so we can hide blocks involving variables that are empty/false.
        def replacer(match):
            key = match.group(1)
            content = match.group(2)
            val = vars_to_use.get(key)
            # Check truthiness:
            # - None -> False
            # - False -> False
            # - "" -> False
            # - 0 -> False
            is_true = bool(val)
            # Special case: allow 0 as True if it's an integer/number, usually we want to display "0 variables"
            if val == 0 or val == "0":
                is_true = True

            # If falsy, strip content. If truthy, keep content (and remove tags)
            return content if is_true else ""

        # Using dotall so {{if}} can span newlines
        final_text = re.sub(
            r"{{if\s+(\w+)}}(.*?){{endif}}", replacer, final_text, flags=re.DOTALL
        )

        # 3. Variable Replacement
        for key, value in vars_to_use.items():
            placeholder = f"[{key}]"
            safe_value = str(value)
            final_text = final_text.replace(placeholder, safe_value)

        return final_text

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

            # Logic to find text to preview:
            # 1. DB Content
            # 2. Registry Default
            text_to_preview = None
            source = "database"

            if msg and msg.text_content:
                text_to_preview = msg.text_content
            else:
                # Check registry
                entry = TEMPLATE_REGISTRY.get(slug)
                if entry and "default" in entry:
                    text_to_preview = entry["default"]
                    source = "default"

            if not text_to_preview:
                await update.message.reply_text(
                    "❌ Mensaje no encontrado (ni en base de datos ni por defecto)."
                )
                return

            # Check for optional target_uid for variable replacement testing
            target_uid = None
            if len(context.args) > 1:
                try:
                    target_uid = int(context.args[1])
                except ValueError:
                    pass

            # If we have text content (either from DB or default) and target for replacement
            if target_uid:
                try:
                    # Get user info to replace [Nombre]
                    try:
                        member = await context.bot.get_chat_member(
                            update.effective_chat.id, target_uid
                        )
                        user = member.user
                    except Exception:
                        chat = await context.bot.get_chat(target_uid)
                        user = chat

                    first_name = user.first_name if user else "Usuario"
                    safe_name = html.escape(first_name)

                    # Use get_text. Note: we don't pass default_text because we already resolved it or it's in registry
                    # But actually get_text will resolve it again if we pass just the slug.
                    # It's better to rely on get_text's internal resolution to be consistent.
                    text_sent = self.get_text(slug, user=user)

                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text_sent,
                        parse_mode=ParseMode.HTML,
                        message_thread_id=get_thread_id(update),
                    )
                    return
                except Exception as e:
                    logger.warning(
                        f"Failed to test vars in list_msge: {e} - Falling back to simple preview"
                    )

            # Simple preview (raw text) or copy if it was a multimedia message in DB
            # If source is default, we just send message.
            # If source is DB and has text_content, we send message.
            # If source is DB and multimedia (no text_content but has IDs), we copy.

            if source == "default" or (msg and msg.text_content):
                # Send text representation
                prefix = (
                    "⚠️ <b>Mensaje por defecto:</b>\n\n"
                    if source == "default"
                    else f"📂 <b>Mensaje Personalizado ({slug}):</b>\n\n"
                )

                # Render keys to show placeholders? Or just raw?
                # Let's show raw but maybe escaped to not break HTML?
                # Actually user wants to see the structure.
                # Use get_text with NO user to see raw placeholders?
                # get_text replaces global vars always if we don't pass them? No, only if user object passed?
                # let's just show text_to_preview raw.

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"{prefix}{html.escape(text_to_preview)}",
                    parse_mode=ParseMode.HTML,
                    message_thread_id=get_thread_id(update),
                )
            elif msg:
                # Multimedia copy fallback
                try:
                    await context.bot.copy_message(
                        chat_id=update.effective_chat.id,
                        from_chat_id=msg.source_chat_id,
                        message_id=msg.source_message_id,
                        message_thread_id=get_thread_id(update),
                    )
                except Exception as e:
                    await update.message.reply_text(
                        f"❌ Error al previsualizar (¿Mensaje original borrado?): {e}"
                    )
            return

        # List mode
        # Show both DB keys and Registry keys
        msgs_db = self._list_messages()
        db_slugs = {m.slug for m in msgs_db}
        registry_slugs = set(TEMPLATE_REGISTRY.keys())

        all_slugs = sorted(db_slugs.union(registry_slugs))

        if not all_slugs:
            await update.message.reply_text("📭 No hay mensajes disponibles.")
            return

        text = "📂 <b>Mensajes Disponibles:</b>\n\n"
        for s in all_slugs:
            icon = "🔹"
            extra = ""
            if s in db_slugs:
                icon = "💾"  # Personalizado
            elif s in registry_slugs:
                icon = "📄"  # Por defecto

            text += f"{icon} <code>{s}</code>{extra}\n"

        text += "\n💾 = Personalizado, 📄 = Por defecto"
        text += "\nUsa <code>/list_msge &lt;id&gt;</code> para ver contenido."
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

    async def send_msge(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        if len(context.args) < 2:
            await update.message.reply_text("❌ Uso: /send_msge <id> <chat_id>")
            return

        slug = context.args[0].lower()
        target_chat_id = context.args[1]

        # Try to resolve via get_text first to see if we have text content
        # But send_msge is often used for multimedia copies...
        # If we have a DB entry with multimedia, copy it.
        # If we have only text (default or DB), send it.

        msg = self._get_message(slug)
        entry = TEMPLATE_REGISTRY.get(slug)

        has_content = (msg and msg.text_content) or (entry and "default" in entry)

        if not msg and not has_content:
            await update.message.reply_text("❌ Mensaje no encontrado.")
            return

        try:
            if msg and not msg.text_content:
                # Pure multimedia copy
                await context.bot.copy_message(
                    chat_id=target_chat_id,
                    from_chat_id=msg.source_chat_id,
                    message_id=msg.source_message_id,
                )
            else:
                # Text based (Default or DB text)
                # We can't really "send" a template without variables replaced...
                # This command is raw. Maybe just send the text?
                # Or try to render with empty vars?
                text_to_send = self.get_text(slug)
                await context.bot.send_message(
                    chat_id=target_chat_id, text=text_to_send, parse_mode=ParseMode.HTML
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

        # Check if content matches a slug
        slug = content.strip().lower()

        # Check if it exists as a template (DB or Default)
        msg_db = self._get_message(slug)
        is_template = (slug in TEMPLATE_REGISTRY) or (msg_db is not None)

        if is_template:
            # It IS a stored message or template
            try:
                if msg_db and not msg_db.text_content:
                    # Multimedia copy
                    await context.bot.copy_message(
                        chat_id=target_chat_id,
                        from_chat_id=msg_db.source_chat_id,
                        message_id=msg_db.source_message_id,
                    )
                else:
                    # Text Message (Template)
                    # Note: We probably want to replace variables?
                    # But /saludo is often used for static things or manual sends.
                    # If it has variables they will remain placeholders unless we inject dummy ones.
                    # Let's send processed text.
                    text_to_send = self.get_text(slug)
                    await context.bot.send_message(
                        chat_id=target_chat_id, text=text_to_send, parse_mode="HTML"
                    )

                await update.message.reply_text(
                    f"✅ Mensaje <code>{slug}</code> enviado a {target_chat_id}",
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
            # Verify if valid slug
            if arg not in TEMPLATE_REGISTRY and not self._get_message(arg):
                await update.message.reply_text(
                    "❌ ID no encontrado. Usa uno de /list_msge"
                )
                return

            self._set_setting("welcome_msg_id", arg)
            await update.message.reply_text(
                f"👋 Bienvenida configurada con mensaje: <code>{arg}</code>",
                parse_mode="HTML",
            )

    async def templates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista todas las plantillas disponibles y sus variables."""
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        text = "📋 <b>Plantillas Disponibles</b>\n\n"
        text += "Usa <code>/add_msge &lt;slug&gt;</code> para personalizar.\n\n"

        for slug, info in TEMPLATE_REGISTRY.items():
            vars_str = ", ".join(info["vars"]) if info["vars"] else "Ninguna"
            text += f"🔹 <b>{slug}</b>\n"
            text += f"   📝 {info['desc']}\n"
            text += f"   💲 Variables: <code>{vars_str}</code>\n\n"

        await update.message.reply_text(text, parse_mode="HTML")

    async def template_vars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista las variables globales disponibles."""
        if update.effective_user.id not in config.ADMIN_USERS:
            return

        text = "💲 <b>Variables Globales</b>\n\n"
        text += "Estas variables se pueden usar en <b>cualquier</b> plantilla:\n\n"

        for key, desc in GLOBAL_VARIABLES.items():
            text += f"🔹 <code>[{key}]</code>: {desc}\n"

        await update.message.reply_text(text, parse_mode="HTML")

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

            # Use get_text to support default templates too, not just DB copy
            # But copy_message is richer for multimedia.
            # Strategy: Try DB message first (for copy). If not, send text.

            msg = self._get_message(current_welcome_id)
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
                    text = self.get_text(current_welcome_id)
                    await context.bot.send_message(
                        chat_id=chat_id, text=text, parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Error enviando bienvenida (text): {e}")
