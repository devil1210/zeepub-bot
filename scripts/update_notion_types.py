import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv(override=True)

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


async def update_notion_types():
    if not NOTION_TOKEN or not DATABASE_ID:
        print("❌ Faltan credenciales en .env")
        return

    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"

    payload = {
        "properties": {
            "Tipo": {
                "select": {
                    "options": [
                        {"name": "Descarga", "color": "green"},
                        {"name": "Lectura", "color": "green"},
                        {"name": "Sugerencia", "color": "blue"},
                        {"name": "Bug", "color": "red"},
                        {"name": "Otro", "color": "yellow"},
                        {"name": "Solicitud", "color": "purple"},
                        {"name": "Facebook", "color": "blue"},
                        {"name": "Telegram", "color": "blue"},
                    ]
                }
            }
        }
    }

    print("🛠️ Actualizando opciones de 'Tipo' en Notion...")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.patch(url, json=payload, headers=headers)
            if resp.status_code == 200:
                print("✅ Opciones actualizadas con éxito en Notion.")
                print("Tipos 'Descarga', 'Facebook' y 'Telegram' agregados.")
            else:
                print(f"❌ Error actualizando opciones: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"❌ Excepción: {e}")


if __name__ == "__main__":
    asyncio.run(update_notion_types())
