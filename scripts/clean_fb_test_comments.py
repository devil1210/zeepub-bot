import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel

async def clean_test_comments():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        res = await session.execute(select(PublicationChannel).where(PublicationChannel.id == 6))
        chan = res.scalar_one_or_none()
        token = chan.config.get('page_access_token')

    json_path = "/app/scripts/facebook_posts_pendientes_manual.json"
    with open(json_path, encoding="utf-8") as f:
        posts = json.load(f)

    print("🧹 Buscando y eliminando comentarios automáticos de prueba...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        for p in posts:
            fb_url = p.get("Enlace_Post_Facebook", "")
            post_id = fb_url.split("/")[-1]

            # Listar comentarios del post
            c_res = await client.get(
                f"https://graph.facebook.com/v21.0/109113064138279_{post_id}/comments",
                params={"access_token": token, "fields": "id,message"}
            )
            if c_res.status_code == 200:
                comments = c_res.json().get("data", [])
                for c in comments:
                    if "Enlace de descarga oficial actualizado" in c.get("message", ""):
                        cid = c["id"]
                        del_res = await client.delete(
                            f"https://graph.facebook.com/v21.0/{cid}",
                            params={"access_token": token}
                        )
                        if del_res.status_code == 200:
                            print(f"🗑️ Comentario eliminado en post {post_id} (ID: {cid})")

    print("✅ Limpieza de comentarios completada.")

if __name__ == "__main__":
    asyncio.run(clean_test_comments())
