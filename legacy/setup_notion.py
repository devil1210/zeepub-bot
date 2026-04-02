
import asyncio
import logging
import sys
import os
import httpx
from dotenv import load_dotenv

# Cargar env actualizado
load_dotenv(override=True)

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PAGE_ID = os.getenv("NOTION_DATABASE_ID") # El usuario nos dio esto, asumimos que es la página padre

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

async def setup_database():
    print(f"🔍 Analizando ID: {PAGE_ID}...")
    
    async with httpx.AsyncClient() as client:
        # 1. Verificar qué es el objeto (Page o Database)
        try:
            resp = await client.get(f"https://api.notion.com/v1/pages/{PAGE_ID}", headers=headers)
            if resp.status_code == 200:
                print("✅ El ID corresponde a una PÁGINA existente.")
                
                # Crear Database dentro de esta página
                print("🛠️ Creando Base de Datos 'Lecturas ZeePub' dentro de la página...")
                
                db_payload = {
                    "parent": {"type": "page_id", "page_id": PAGE_ID},
                    "title": [
                        {"type": "text", "text": {"content": "Lecturas ZeePub"}}
                    ],
                    "properties": {
                        "Título": {"title": {}},
                        "Tipo": {
                            "select": {
                                "options": [
                                    {"name": "Lectura", "color": "green"},
                                    {"name": "Sugerencia", "color": "blue"},
                                    {"name": "Bug", "color": "red"},
                                    {"name": "Otro", "color": "yellow"},
                                    {"name": "Solicitud", "color": "purple"}
                                ]
                            }
                        },
                        "Serie": {"rich_text": {}},
                        "Volumen": {"number": {"format": "number"}},
                        "Autor": {"rich_text": {}},
                        "Usuario": {"rich_text": {}},
                        "Comentarios": {"rich_text": {}},
                        "Fecha": {"date": {}}
                    }
                }
                
                db_resp = await client.post("https://api.notion.com/v1/databases", json=db_payload, headers=headers)
                
                if db_resp.status_code == 200:
                    new_db_id = db_resp.json()["id"]
                    print(f"\n🎉 BASE DE DATOS CREADA CON ÉXITO!")
                    print(f"🆔 Nuevo DATABASE_ID: {new_db_id}")
                    print(f"\n⚠️ IMPORTANTE: Voy a actualizar tu .env automáticamente con este nuevo ID.")
                    return new_db_id
                else:
                    print(f"❌ Error creando database: {db_resp.text}")
            elif resp.status_code == 404:
                 # Quizás es ya una database?
                 resp_db = await client.get(f"https://api.notion.com/v1/databases/{PAGE_ID}", headers=headers)
                 if resp_db.status_code == 200:
                     print("ℹ️ El ID ya corresponde a una Database. No es necesario crear nada.")
                     return PAGE_ID
                 else:
                     print("❌ El ID no corresponde ni a una Página ni a una Database accesible.")
            else:
                print(f"❌ Error verificando página: {resp.status_code} - {resp.text}")

        except Exception as e:
            print(f"❌ Excepción: {e}")
            
    return None

def update_env(new_id):
    env_path = ".env"
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith("NOTION_DATABASE_ID="):
                f.write(f"NOTION_DATABASE_ID={new_id}\n")
            else:
                f.write(line)
    print("✅ Archivo .env actualizado.")

if __name__ == "__main__":
    if not NOTION_TOKEN or not PAGE_ID:
        print("❌ Faltan credenciales en .env")
    else:
        new_id = asyncio.run(setup_database())
        if new_id and new_id != PAGE_ID:
            update_env(new_id)
