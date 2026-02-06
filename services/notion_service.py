import logging
import httpx
from datetime import datetime
from config.config_settings import config

logger = logging.getLogger(__name__)


class NotionService:
    @staticmethod
    async def log_reading(
        user_name: str,
        book_title: str,
        series_name: str,
        volume: str = "1",
        author: str = "Desconocido",
    ):
        """
        Logs a reading event to a Notion database.
        """
        if not config.NOTION_TOKEN or not config.NOTION_DATABASE_ID:
            logger.debug("Notion integration not configured. Skipping log.")
            return False

        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {config.NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        payload = {
            "parent": {"database_id": config.NOTION_DATABASE_ID},
            "properties": {
                "Título": {"title": [{"text": {"content": book_title}}]},
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

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    logger.info(f"✅ Reading log added to Notion: {book_title} for {user_name}")
                    return True
                else:
                    logger.error(f"❌ Notion API error: {response.status_code} - {response.text}")
                    return False
            except Exception as e:
                logger.error(f"❌ Error connecting to Notion: {e}")
                return False


notion_service = NotionService()
