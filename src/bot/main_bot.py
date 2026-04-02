# src/bot/main_bot.py
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    ContextTypes,
    filters
)
from telegram.request import HTTPXRequest
from telegram.constants import ParseMode
from src.core.config import settings
from src.services.scanner.library_scanner import scanner

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el comando /start."""
    user = update.effective_user
    welcome_text = (
        f"👋 ¡Hola <b>{user.first_name}</b>! Bienvenido al nuevo motor <b>Zeepub Nexus</b>.\n\n"
        "He sido reconstruido para ser más rápido, modular y estable.\n\n"
        "📖 <b>Comandos disponibles:</b>\n"
        "/buscar [título] - Proximamente (Usar Mini App)\n"
        "/scan - Sincronizar biblioteca (Solo Admin)\n"
        "/help - Ver ayuda detallada"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para disparar el escaneo de biblioteca (SÓLO ADMIN)."""
    user_id = update.effective_user.id
    if user_id not in settings.ADMIN_USERS:
        logger.warning(f"🚫 Intento de scan no autorizado por UID: {user_id}")
        return
    
    msg = await update.message.reply_text("🔎 <b>Nexus Scanner:</b> Iniciando escaneo profundo...")
    try:
        await scanner.run_full_scan()
        await msg.edit_text("✅ <b>Nexus Scanner:</b> Sincronización completada con éxito.")
    except Exception as e:
        logger.error(f"❌ Error en comando scan: {e}")
        await msg.edit_text(f"❌ <b>Nexus Scanner:</b> Error durante el proceso:\n<code>{e}</code>", parse_mode=ParseMode.HTML)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para ayuda."""
    help_text = (
        "🛠 <b>Nexus Skeleton Help</b>\n\n"
        "Este bot es el esqueleto de la nueva arquitectura <b>Nexus</b>.\n"
        "Actualmente gestiona la biblioteca local y la integración con IA.\n\n"
        "Si tienes problemas con las descargas, contacta a un administrador."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

def create_bot_app():
    """
    Fábrica de la aplicación del Bot Zeepub-Nexus.
    Configura red optimizada para evitar Timeouts en el VPS.
    """
    if not settings.TELEGRAM_TOKEN:
        logger.error("❌ No se encontró TELEGRAM_TOKEN. El bot no iniciará.")
        return None

    # Configuración de red robusta (Basada en métricas de v4 original)
    trequest = HTTPXRequest(
        connection_pool_size=100,
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )
    
    app = ApplicationBuilder() \
        .token(settings.TELEGRAM_TOKEN) \
        .request(trequest) \
        .build()
    
    # Registro de Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CommandHandler("help", help_command))
    
    logger.info("🤖 Zeepub-Nexus Bot: Handlers registrados.")
    return app
