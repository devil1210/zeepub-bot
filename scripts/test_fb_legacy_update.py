import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel

async def test_update_methods():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        res = await session.execute(select(PublicationChannel).where(PublicationChannel.id == 6))
        chan = res.scalar_one_or_none()
        token = chan.config.get('page_access_token')

    post_id = "109113064138279_309113084138275"
    photo_id = "309112050805045"
    new_message = """Strike the Blood − Volumen 17
EPUB maquetado por #Zeedif #ZeePub

Link de descarga [EPUB3]:
https://dl.zeepubs.com/zSb8UIZX3I

Autor: Gakuto Mikumo
Ilustrador: Manyako
Traducción: KaleidWordTranslations − https://canislykaon.wixsite.com/novelas/strike-the-blood

Sinopsis: ?"""

    async with httpx.AsyncClient(timeout=20.0) as client:
        # Método 1: POST /{post_id} con message
        r1 = await client.post(f"https://graph.facebook.com/v21.0/{post_id}", params={"access_token": token}, data={"message": new_message})
        print(f"Método 1 (POST /{post_id} message): {r1.status_code} -> {r1.text}")

        # Método 2: POST /{photo_id} con message / caption / name
        r2 = await client.post(f"https://graph.facebook.com/v21.0/{photo_id}", params={"access_token": token}, data={"message": new_message})
        print(f"Método 2 (POST /{photo_id} message): {r2.status_code} -> {r2.text}")

        r3 = await client.post(f"https://graph.facebook.com/v21.0/{photo_id}", params={"access_token": token}, data={"caption": new_message})
        print(f"Método 3 (POST /{photo_id} caption): {r3.status_code} -> {r3.text}")

        r4 = await client.post(f"https://graph.facebook.com/v21.0/{photo_id}", params={"access_token": token}, data={"name": new_message})
        print(f"Método 4 (POST /{photo_id} name): {r4.status_code} -> {r4.text}")

        # Método 5: POST /{page_id}_{photo_id}
        full_photo_id = f"109113064138279_{photo_id}"
        r5 = await client.post(f"https://graph.facebook.com/v21.0/{full_photo_id}", params={"access_token": token}, data={"message": new_message})
        print(f"Método 5 (POST /{full_photo_id} message): {r5.status_code} -> {r5.text}")

        # Método 6: Con Graph API v18.0 o v12.0
        r6 = await client.post(f"https://graph.facebook.com/v18.0/{post_id}", params={"access_token": token}, data={"message": new_message})
        print(f"Método 6 (POST v18.0 /{post_id}): {r6.status_code} -> {r6.text}")

        r7 = await client.post(f"https://graph.facebook.com/v18.0/{photo_id}", params={"access_token": token}, data={"message": new_message})
        print(f"Método 7 (POST v18.0 /{photo_id}): {r7.status_code} -> {r7.text}")

if __name__ == "__main__":
    asyncio.run(test_update_methods())
