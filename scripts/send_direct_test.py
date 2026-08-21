import asyncio
import os
import httpx
from config.config_settings import config

async def test():
    bot_token = getattr(config, "TELEGRAM_TOKEN", None) or os.getenv("TELEGRAM_TOKEN")
    print("Bot token prefix:", bot_token[:10] if bot_token else None)
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": 133994080,
                "text": "🔔 <b>ZeePub-bot:</b> Alerta de prueba enviada con éxito a tu chat de Telegram.",
                "parse_mode": "HTML",
            },
        )
        print("Resultado envío:", r.status_code, r.text)

asyncio.run(test())
