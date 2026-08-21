import asyncio
from fb_hourly_replacer import send_telegram_alert

async def notify():
    await send_telegram_alert(
        "📊 <b>Estado de Enlaces en Facebook</b>\n\n"
        "✅ <b>Completados con dl.zeepubs.com:</b> 95 publicaciones\n"
        "⏳ <b>Pendientes por actualizar:</b> 349 publicaciones\n\n"
        "⚠️ <i>Facebook activó un límite temporal de edición anti-spam (Code 368). El bot esperará el enfriamiento de la cuota y continuará procesando lotes de 25 posts por hora automáticamente notificándote aquí.</i>"
    )

asyncio.run(notify())
