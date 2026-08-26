"""
Servicio de sincronización automática de publicaciones de Facebook con la base de datos (book_publications).
Descarga periódicamente los posts recientes de la página de Facebook y vincula automáticamente
las nuevas publicaciones manuales del administrador con los libros de la biblioteca.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.communications import BookPublication, PublicationChannel
from models.library import LocalBook
from scripts.execute_fb_replace_batch import (
    DOWNLOAD_DOMAINS,
    URL_REGEX,
    match_single_link,
)

logger = logging.getLogger(__name__)


class FacebookSyncService:
    """
    Gestiona la sincronización periódica y manual del feed de Facebook
    con la tabla relacional `book_publications`.
    """

    @classmethod
    async def sync_recent_publications(
        cls, limit_posts: int = 50, fetch_all: bool = False
    ) -> dict[str, Any]:
        """
        Consulta los posts de Facebook más recientes (o todos si fetch_all=True),
        detecta los enlaces de descarga / códigos de libros y registra los nuevos vínculos
        en la tabla `book_publications`.
        """
        logger.info(f"🔄 Iniciando sincronización de Facebook feed (limit={limit_posts}, fetch_all={fetch_all})...")

        # 1. Obtener credenciales del canal de Facebook y catálogo de libros
        channel_id = None
        page_id = None
        token = None
        all_books: list[dict[str, Any]] = []

        async with pg_manager.get_session() as session:
            # Buscar canal de facebook activo
            stmt_chan = select(PublicationChannel).where(
                PublicationChannel.platform == "facebook",
                PublicationChannel.is_active == True,
            )
            chan_res = await session.execute(stmt_chan)
            chan = chan_res.scalars().first()

            if not chan:
                # Fallback a id=6 o cualquier canal facebook
                stmt_chan_fb = select(PublicationChannel).where(PublicationChannel.platform == "facebook")
                chan = (await session.execute(stmt_chan_fb)).scalars().first()

            if not chan or not chan.config:
                logger.warning("❌ No se encontró un canal de Facebook configurado con token.")
                return {"success": False, "error": "Canal de Facebook no configurado"}

            channel_id = chan.id
            page_id = str(chan.target_id)
            token = chan.config.get("page_access_token") or chan.config.get("access_token")

            if not page_id or not token:
                logger.warning("❌ Falta target_id (Page ID) o page_access_token en el canal de Facebook.")
                return {"success": False, "error": "Credenciales de Facebook incompletas"}

            # Cargar libros con short_link
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

        # 2. Consultar Graph API para obtener publicaciones
        url = f"https://graph.facebook.com/v21.0/{page_id}/published_posts"
        params: dict[str, Any] | None = {
            "access_token": token,
            "fields": "id,message,created_time,permalink_url",
            "limit": str(min(limit_posts, 100)),
        }
        all_posts = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                while url:
                    resp = await client.get(url, params=params if len(all_posts) == 0 else None)
                    if resp.status_code != 200:
                        logger.warning(f"Error consultando Facebook Graph API: {resp.status_code} - {resp.text}")
                        break

                    data = resp.json()
                    posts = data.get("data", [])
                    all_posts.extend(posts)

                    if not fetch_all or len(all_posts) >= limit_posts:
                        break

                    url = data.get("paging", {}).get("next")
                    params = None
        except Exception as e:
            logger.error(f"Excepción al descargar posts de Facebook: {e}")
            return {"success": False, "error": str(e)}

        logger.info(f"📥 Posts recuperados de Facebook: {len(all_posts)}")

        # 3. Emparejar posts con libros
        records_to_insert = []
        for p in all_posts:
            msg = p.get("message") or ""
            urls = URL_REGEX.findall(msg)
            dl_urls = [u for u in urls if any(d in u.lower() for d in DOWNLOAD_DOMAINS) or "dl.zeepubs.com" in u.lower()]
            if not dl_urls:
                continue

            created_str = p.get("created_time")
            pub_date = None
            if created_str:
                try:
                    dt_obj = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                    pub_date = dt_obj.replace(tzinfo=None)
                except Exception:
                    pub_date = datetime.utcnow()

            post_id = p.get("id")
            permalink = p.get("permalink_url") or f"https://www.facebook.com/{post_id}"

            post_books_seen = set()
            for dl in dl_urls:
                matched_book = None
                if "dl.zeepubs.com" in dl:
                    s_code = dl.split("/")[-1].strip()
                    matched_book = next((b for b in all_books if b.get("short_link") == s_code), None)

                if not matched_book:
                    matched_book = match_single_link(msg, dl, all_books)

                if matched_book and matched_book["id"] not in post_books_seen:
                    post_books_seen.add(matched_book["id"])
                    records_to_insert.append({
                        "book_id": matched_book["id"],
                        "platform": "facebook",
                        "channel_id": channel_id,
                        "post_id": post_id,
                        "post_url": permalink,
                        "caption": msg,
                        "published_at": pub_date,
                    })

        # 4. Guardar nuevos registros en base de datos evitando duplicados
        inserted_count = 0
        async with pg_manager.get_session() as session:
            existing_res = await session.execute(select(BookPublication.book_id, BookPublication.post_id))
            existing_pairs = set(existing_res.all())

            for rec in records_to_insert:
                if (rec["book_id"], rec["post_id"]) not in existing_pairs:
                    pub = BookPublication(
                        book_id=rec["book_id"],
                        platform=rec["platform"],
                        channel_id=rec["channel_id"],
                        post_id=rec["post_id"],
                        post_url=rec["post_url"],
                        caption=rec["caption"],
                        published_at=rec["published_at"],
                    )
                    session.add(pub)
                    existing_pairs.add((rec["book_id"], rec["post_id"]))
                    inserted_count += 1

            if inserted_count > 0:
                await session.commit()

        logger.info(f"✅ Sincronización de Facebook finalizada. {inserted_count} nuevas publicaciones vinculadas.")
        return {
            "success": True,
            "posts_checked": len(all_posts),
            "new_publications_synced": inserted_count,
        }


async def facebook_sync_loop():
    """
    Loop en background que ejecuta la sincronización automática cada 6 horas
    y a las 00:00 UTC diariamente.
    """
    logger.info("🕒 Facebook Sync loop scheduler iniciado (intervalo: cada 6 horas).")
    # Primera sincronización a los 30 segundos del arranque
    await asyncio.sleep(30)

    while True:
        try:
            await FacebookSyncService.sync_recent_publications(limit_posts=30, fetch_all=False)
        except asyncio.CancelledError:
            logger.info("Facebook Sync scheduler cancelado.")
            break
        except Exception as e:
            logger.error(f"Error en facebook_sync_loop: {e}", exc_info=True)

        # Esperar 6 horas entre chequeos
        await asyncio.sleep(6 * 3600)


def start_facebook_sync_scheduler():
    """
    Inicia la tarea periódica de sincronización de Facebook en background.
    """
    asyncio.create_task(facebook_sync_loop())
    logger.info("🚀 Facebook Sync Scheduler task registrada.")
