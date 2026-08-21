import asyncio
from fb_hourly_replacer import send_telegram_alert

async def main():
    await send_telegram_alert("🤖 <b>ZeePub-bot:</b> Servicio de notificaciones de actualización de enlaces en Facebook activado correctamente.")

asyncio.run(main())
