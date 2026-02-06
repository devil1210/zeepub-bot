import logging
from datetime import datetime

import httpx

from config.config_settings import config

logger = logging.getLogger(__name__)


class NotionService:
    async def _send_to_notion(self, payload: dict) -> bool:
        if not config.NOTION_TOKEN or not config.NOTION_DATABASE_ID:
            logger.debug("Notion integration not configured. Skipping log.")
            return False

        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {config.NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    return True
                else:
                    logger.error(f"❌ Notion API error: {response.status_code} - {response.text}")
                    return False
            except Exception as e:
                logger.error(f"❌ Error connecting to Notion: {e}")
                return False

    async def log_download(
        self,
        user_name: str,
        book_title: str,
        series_name: str,
        volume: str = "1",
        author: str = "Desconocido",
    ):
        """Logs a download event."""
        payload = {
            "parent": {"database_id": config.NOTION_DATABASE_ID},
            "icon": {"emoji": "📥"},
            "properties": {
                "Título": {"title": [{"text": {"content": book_title}}]},
                "Tipo": {"select": {"name": "Descarga"}},
                "Serie": {"rich_text": [{"text": {"content": series_name}}]},
                "Volumen": {
                    "number": float(volume)
                    if volume and volume.replace(".", "", 1).isdigit()
                    else 1
                },
                "Autor": {"rich_text": [{"text": {"content": author}}]},
                "Usuario": {"rich_text": [{"text": {"content": user_name}}]},
                "Fecha": {"date": {"start": datetime.utcnow().isoformat()}},
            },
        }
        success = await self._send_to_notion(payload)
        if success:
            logger.info(f"✅ Download log added to Notion: {book_title}")
        return success

    async def log_social_publish(
        self, platform: str, title: str, series: str = "", user: str = "System", details: str = ""
    ):
        """Logs a publication to social media (Facebook/Telegram)."""
        emoji = "🔵" if platform.lower() == "facebook" else "🔹"
        payload = {
            "parent": {"database_id": config.NOTION_DATABASE_ID},
            "icon": {"emoji": emoji},
            "properties": {
                "Título": {"title": [{"text": {"content": title}}]},
                "Tipo": {"select": {"name": platform.capitalize()}},
                "Serie": {"rich_text": [{"text": {"content": series}}]},
                "Comentarios": {"rich_text": [{"text": {"content": details}}]},
                "Usuario": {"rich_text": [{"text": {"content": user}}]},
                "Fecha": {"date": {"start": datetime.utcnow().isoformat()}},
            },
        }
        success = await self._send_to_notion(payload)
        if success:
            logger.info(f"✅ Social publish logged to Notion: {platform} - {title}")
        return success

    async def log_feedback(self, user_name: str, message: str, category: str = "Sugerencia"):
        """Logs user feedback, bugs, or general comments."""
        payload = {
            "parent": {"database_id": config.NOTION_DATABASE_ID},
            "icon": {"emoji": "💡" if category == "Sugerencia" else "🐞"},
            "properties": {
                "Título": {"title": [{"text": {"content": f"{category} de {user_name}"}}]},
                "Tipo": {"select": {"name": category}},
                "Comentarios": {"rich_text": [{"text": {"content": message}}]},
                "Usuario": {"rich_text": [{"text": {"content": user_name}}]},
                "Fecha": {"date": {"start": datetime.utcnow().isoformat()}},
            },
        }
        success = await self._send_to_notion(payload)
        if success:
            logger.info(f"✅ Feedback logged to Notion: {category} from {user_name}")
        return success

    async def log_book_request(
        self, user_name: str, book_name: str, author: str = "", notes: str = ""
    ):
        """Logs a specific book request."""
        details = f"Autor: {author}\nNotas: {notes}" if notes else f"Autor: {author}"
        payload = {
            "parent": {"database_id": config.NOTION_DATABASE_ID},
            "icon": {"emoji": "🙏"},
            "properties": {
                "Título": {"title": [{"text": {"content": f"Solicitud: {book_name}"}}]},
                "Tipo": {"select": {"name": "Solicitud"}},
                "Serie": {
                    "rich_text": [{"text": {"content": book_name}}]
                },  # Use Serie col for requested book name too
                "Comentarios": {"rich_text": [{"text": {"content": details}}]},
                "Usuario": {"rich_text": [{"text": {"content": user_name}}]},
                "Fecha": {"date": {"start": datetime.utcnow().isoformat()}},
            },
        }
        success = await self._send_to_notion(payload)
        if success:
            logger.info(f"✅ Book request logged to Notion: {book_name}")
        return success


notion_service = NotionService()
