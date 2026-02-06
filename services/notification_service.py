import logging
from typing import Any

import httpx

from config.config_settings import config

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    async def notify_new_books(books_data: list[dict[str, Any]]):
        """
        Sends a notification to Discord/Slack when new books are indexed.
        """
        webhook_url = config.NOTIFICATION_WEBHOOK_URL
        if not webhook_url:
            logger.debug("Notification webhook not configured. Skipping.")
            return False

        if not books_data:
            return False

        # Limit to 10 books in summary to avoid huge messages
        display_books = books_data[:10]
        remaining = len(books_data) - 10

        content = "🆕 **¡Nuevos libros agregados al catálogo!** 📚\n\n"

        for b in display_books:
            title = b.get("title", "Desconocido")
            series = b.get("series", "")
            vol = b.get("volume", "?")
            author = b.get("author", "Desconocido")

            line = f"• **{series or title}** - Vol. {vol} (por {author})\n"
            content += line

        if remaining > 0:
            content += f"\n... y {remaining} libros más."

        # Discord format
        payload = {
            "content": content,
            "username": "ZeePub Notifier",
            "avatar_url": "https://zeepubs.com/logo.png",  # Placeholder
        }

        async with httpx.AsyncClient() as client:
            try:
                # Basic support for both Discord and Slack (Discord uses 'content', Slack uses 'text')
                # We'll try Discord format first as it's the most common for the user
                response = await client.post(webhook_url, json=payload)
                if response.status_code in (200, 204):
                    logger.info(f"✅ Notification sent for {len(books_data)} books.")
                    return True
                else:
                    # Retry with Slack format if needed
                    slack_payload = {"text": content}
                    response = await client.post(webhook_url, json=slack_payload)
                    if response.status_code == 200:
                        return True

                    logger.error(f"❌ Notification error: {response.status_code} - {response.text}")
                    return False
            except Exception as e:
                logger.error(f"❌ Error sending notification: {e}")
                return False


notification_service = NotificationService()
