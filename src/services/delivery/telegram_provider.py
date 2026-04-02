# src/services/delivery/telegram_provider.py
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional
from telegram import Bot, InputMediaPhoto
from telegram.constants import ParseMode
from src.utils.templates import render_template
from src.core.config import settings

logger = logging.getLogger(__name__)

class TelegramDeliveryProvider:
    """
    Proveedor de entrega de Telegram para Zeepub-Nexus.
    Restaura las plantillas estables del sistema original.
    """
    
    # Plantillas estables (ADN de Zeepub original)
    COVER_TEMPLATE = (
        "📚 {serie} ║ {romaji_title} ║ {titulo}"
        "[?volumen]\n📖 Volumen {volumen}[/?]"
        "\n#{slug}\n"
        "[?layout_by]\n🎨 <b>Maquetado por:</b> #{layout_by}[/?]"
        "[?tipo]\n🏷️ <b>Categoría:</b> {tipo}[/?]"
        "[?genres]\n🎭 <b>Géneros:</b> {genres}[/?]"
        "[?autor]\n✍️ <b>Autor:</b> {autor}[/?]"
        "[?editorial]\n🏢 <b>Grupo Traductor:</b> {editorial}[/?]"
    )
    SYNOPSIS_TEMPLATE = "📝 <b>Sinopsis:</b>\n\n<blockquote>{sinopsis}</blockquote>\n\n#{slug}"
    INFO_TEMPLATE = "📂 <b>{titulo}</b>\nℹ️ Versión Epub: {version}\n📅 Actualizado: {fecha}\n📦 Tamaño: {size}\n\n#{slug}"

    def __init__(self, bot: Bot):
        self.bot = bot

    async def deliver_book(self, chat_id: int, book_data: Dict[str, Any]):
        """
        Envía un libro con el formato premium completo: Portada -> Sinopsis -> Archivo.
        """
        logger.info(f"🚚 Entregando libro a {chat_id}: {book_data.get('titulo')}")
        
        # 1. Preparar Datos (Normalización para templates)
        data = self._prepare_template_data(book_data)
        
        # 2. Renderizar Mensajes
        cover_text = render_template(self.COVER_TEMPLATE, data)
        synopsis_text = render_template(self.SYNOPSIS_TEMPLATE, data)
        info_text = render_template(self.INFO_TEMPLATE, data)

        try:
            # 2a. Foto / Portada
            cover_url = data.get("cover_url")
            if cover_url:
                await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=cover_url,
                    caption=cover_text,
                    parse_mode=ParseMode.HTML
                )
            else:
                await self.bot.send_message(chat_id=chat_id, text=cover_text, parse_mode=ParseMode.HTML)

            # 2b. Sinopsis
            if data.get("sinopsis"):
                await self.bot.send_message(chat_id=chat_id, text=synopsis_text, parse_mode=ParseMode.HTML)

            # 2c. Archivo con Info final
            file_path = data.get("file_path")
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    await self.bot.send_document(
                        chat_id=chat_id,
                        document=f,
                        caption=info_text,
                        parse_mode=ParseMode.HTML,
                        filename=os.path.basename(file_path)
                    )
            else:
                logger.warning(f"⚠️ Archivo no encontrado para entrega: {file_path}")
                await self.bot.send_message(chat_id=chat_id, text=info_text, parse_mode=ParseMode.HTML)

            return True
        except Exception as e:
            logger.error(f"❌ Error en entrega Telegram: {e}")
            return False

    def _prepare_template_data(self, book_data: Dict[str, Any]) -> Dict[str, Any]:
        """Asegura que las llaves coincidan con las plantillas."""
        return {
            "serie": book_data.get("serie", "Standalone"),
            "romaji_title": book_data.get("romaji", ""),
            "titulo": book_data.get("titulo", "Libro"),
            "volumen": book_data.get("volume", "0.0"),
            "slug": book_data.get("slug", "epub"),
            "sinopsis": book_data.get("description", "Sin sinopsis."),
            "version": "1.0-Nexus",
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "size": f"{book_data.get('file_size', 0) // 1024} KB",
            "cover_url": book_data.get("cover_url"),
            "file_path": book_data.get("file_path"),
            "autor": book_data.get("author", "N/A"),
            "tipo": book_data.get("book_type", "Novel"),
            "editorial": book_data.get("group", "Zeepubs"),
            "genres": ", ".join(book_data.get("genres", [])) if isinstance(book_data.get("genres"), list) else ""
        }
