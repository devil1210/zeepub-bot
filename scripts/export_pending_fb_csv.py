import asyncio
import sys
import csv
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel
from models.library import LocalBook
from scripts.execute_fb_replace_batch import DOWNLOAD_DOMAINS, URL_REGEX, match_single_link

async def generate_pending_csv():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        res_chan = await session.execute(select(PublicationChannel).where(PublicationChannel.id == 6))
        chan = res_chan.scalar_one_or_none()
        page_id = str(chan.target_id)
        token = chan.config.get('page_access_token')

        res_books = await session.execute(select(LocalBook))
        raw_books = res_books.scalars().all()
        all_books = [
            {
                "id": str(b.id),
                "title": b.title,
                "volume": b.volume,
                "short_link": b.short_link,
                "series_spanish": b.series_spanish,
                "series_english": b.series_english,
                "color_mode": b.color_mode,
                "layout_by": b.layout_by,
                "translator": b.translator,
                "filename": b.filename,
            }
            for b in raw_books
            if b.short_link
        ]

    url = f"https://graph.facebook.com/v21.0/{page_id}/published_posts"
    params = {'access_token': token, 'fields': 'id,message,created_time,permalink_url', 'limit': '100'}
    all_posts = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while url:
            resp = await client.get(url, params=params if len(all_posts) == 0 else None)
            if resp.status_code != 200: break
            data = resp.json()
            posts = data.get('data', [])
            all_posts.extend(posts)
            url = data.get('paging', {}).get('next')
            params = None

    print(f"Total posts descargados: {len(all_posts)}")
    rows = []

    for p in all_posts:
        msg = p.get('message') or ''
        # Solo procesar posts que contengan links antiguos de descarga y no hayan sido actualizados
        urls = URL_REGEX.findall(msg)
        dl_urls = [u for u in urls if any(d in u.lower() for d in DOWNLOAD_DOMAINS)]
        if not dl_urls:
            continue

        first_line = msg.strip().split('\n')[0] if msg else ''
        post_url = p.get('permalink_url') or f"https://www.facebook.com/{p.get('id')}"
        created_time = (p.get('created_time') or '')[:10]

        # Generar texto completo reemplazado
        replaced_msg = msg
        items_detail = []

        for dl in dl_urls:
            matched = match_single_link(msg, dl, all_books)
            if matched:
                new_url = f"https://dl.zeepubs.com/{matched['short_link']}"
                book_name = matched['title']
                replaced_msg = replaced_msg.replace(dl, new_url)
                items_detail.append({
                    "old_url": dl,
                    "new_url": new_url,
                    "book_name": book_name
                })
            else:
                items_detail.append({
                    "old_url": dl,
                    "new_url": "N/A",
                    "book_name": "Desconocido"
                })

        old_links_str = " \n".join([item["old_url"] for item in items_detail])
        new_links_str = " \n".join([item["new_url"] for item in items_detail])
        books_str = " \n".join([item["book_name"] for item in items_detail])

        rows.append({
            "Fecha": created_time,
            "Titulo_Publicacion": first_line,
            "Enlace_Post_Facebook": post_url,
            "Libro_Detectado": books_str,
            "Link_Antiguo": old_links_str,
            "Link_Oficial_Nuevo": new_links_str,
            "Texto_Completo_Actualizado": replaced_msg
        })

    # Guardar en CSV con encoding utf-8-sig (para que Excel abra perfecto los acentos y emojis)
    csv_path = "/app/scripts/facebook_posts_pendientes_manual.csv"
    json_path = "/app/scripts/facebook_posts_pendientes_manual.json"
    
    with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Fecha",
            "Titulo_Publicacion",
            "Enlace_Post_Facebook",
            "Libro_Detectado",
            "Link_Antiguo",
            "Link_Oficial_Nuevo",
            "Texto_Completo_Actualizado"
        ])
        writer.writeheader()
        writer.writerows(rows)

    with open(json_path, mode="w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"✅ Archivos generados con éxito: {len(rows)} filas guardadas en {csv_path}")

if __name__ == "__main__":
    asyncio.run(generate_pending_csv())
