"""
Script para obtener tu ID de Telegram y verificar configuración de admin
"""

import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Configuración temporal para obtener tu ID
TOKEN = "TU_TOKEN_AQUI"  # Reemplaza con tu token real


async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obtiene tu ID de usuario de Telegram."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    await update.message.reply_text(
        f"🔍 **Tu información de Telegram:**\n\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"👤 **Username:** @{username if username else 'N/A'}\n"
        f"📝 **Nombre:** {first_name}\n\n"
        f"📋 **Para añadirte como admin:**\n"
        f"Añade este número a la variable `ADMIN_USERS` en tu archivo `.env`:\n"
        f"```\n"
        f"ADMIN_USERS={user_id}\n"
        f"```\n\n"
        f"O si ya hay otros admins:\n"
        f"```\n"
        f"ADMIN_USERS=123456789,{user_id},987654321\n"
        f"```"
    )


async def main():
    """Función principal para ejecutar el bot temporal."""
    logging.basicConfig(level=logging.INFO)

    application = Application.builder().token(TOKEN).build()

    # Handler para obtener ID
    application.add_handler(CommandHandler("myid", get_my_id))

    print("🤖 Bot iniciado. Envía /myid para obtener tu ID de Telegram")
    print("📝 Luego añade ese ID a ADMIN_USERS en tu .env")

    await application.run_polling()


if __name__ == "__main__":
    if TOKEN == "TU_TOKEN_AQUI":
        print(
            "❌ ERROR: Debes reemplazar 'TU_TOKEN_AQUI' con tu token real de Telegram"
        )
        print("📝 Ve a https://t.me/BotFather para obtener tu token")
    else:
        asyncio.run(main())
