import asyncio
import json
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel

async def comment_pending_posts():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        res = await session.execute(select(PublicationChannel).where(PublicationChannel.id == 6))
        chan = res.scalar_one_or_none()
        token = chan.config.get('page_access_token')

    json_path = "/app/scripts/facebook_posts_pendientes_manual.json"
    with open(json_path, encoding="utf-8") as f:
        posts = json.load(f)

    log_file = open("/app/fb_comment_live.log", "w", encoding="utf-8", buffering=1)
    log_file.write(f"🚀 Iniciando proceso de comentario oficial para {len(posts)} posts antiguos...\n")

    success_count = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx, p in enumerate(posts, 1):
            fb_url = p.get("Enlace_Post_Facebook", "")
            post_id = fb_url.split("/")[-1]
            new_link = p.get("Link_Oficial_Nuevo", "")
            book_name = p.get("Libro_Detectado", "")

            if not new_link or new_link == "N/A":
                continue

            comment_text = f"📌 Enlace de descarga oficial actualizado (EPUB3):\n{new_link}"

            try:
                c_res = await client.post(
                    f"https://graph.facebook.com/v21.0/109113064138279_{post_id}/comments",
                    params={"access_token": token},
                    data={"message": comment_text}
                )

                if c_res.status_code == 200:
                    msg = f"[{idx}/{len(posts)}] ✅ Comentario publicado en post {post_id} ({book_name}): {new_link}\n"
                    log_file.write(msg)
                    success_count += 1
                elif c_res.status_code == 400 and "OAuthException" in c_res.text:
                    msg = f"[{idx}/{len(posts)}] ⚠️ Rate limit detectado en post {post_id}. Esperando 60s...\n"
                    log_file.write(msg)
                    await asyncio.sleep(60)
                else:
                    msg = f"[{idx}/{len(posts)}] ❌ Error en post {post_id}: {c_res.status_code} -> {c_res.text}\n"
                    log_file.write(msg)
            except Exception as e:
                msg = f"[{idx}/{len(posts)}] ❌ Excepción en post {post_id}: {e}\n"
                log_file.write(msg)

            await asyncio.sleep(random.uniform(4.0, 7.0))

    log_file.write(f"\n🎉 PROCESO COMPLETADO: {success_count}/{len(posts)} posts comentados exitosamente con su link oficial.\n")
    log_file.close()

if __name__ == "__main__":
    asyncio.run(comment_pending_posts())
