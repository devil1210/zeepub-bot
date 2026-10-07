#!/usr/bin/env python3
# scripts/fix_published_synopsis.py
"""
Script de mantenimiento para corregir in-place las sinopsis en publicaciones de Telegram
que recibieron la sinopsis general de la serie en vez de la del volumen individual
a contar del 28 de agosto de 2026.

Uso:
    # Modo simulación (por defecto, no envía nada a Telegram):
    python scripts/fix_published_synopsis.py --dry-run

    # Modo simulación limitando a 5 novelas:
    python scripts/fix_published_synopsis.py --dry-run --limit 5

    # Modo aplicación real:
    python scripts/fix_published_synopsis.py --apply --delay 2.0
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any

# Añadir raíz al PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fix_synopsis")


def clean_text_snippet(text: str | None, max_len: int = 90) -> str:
    """Limpia etiquetas y recorta un extracto de texto para visualización."""
    if not text:
        return "(vacío)"
    import re

    cleaned = re.sub(r"<[^>]+>", "", text).replace("\n", " ").strip()
    if len(cleaned) > max_len:
        return cleaned[:max_len] + "..."
    return cleaned


async def find_affected_publications(
    session, since_date: datetime, default_channel: str = "@ZeePubs"
) -> list[dict[str, Any]]:
    """
    Busca todas las publicaciones de Telegram realizadas a contar de `since_date`
    que cuenten con un `tg_message_id` y donde el volumen posea una sinopsis individual
    distinta a la de la serie.
    """
    from sqlalchemy import and_, select
    from sqlalchemy.orm import selectinload

    from models.communications import PublicationChannel, PublicationQueue
    from models.library import Book

    # 1. Canales de Telegram
    stmt_chans = select(PublicationChannel).where(PublicationChannel.platform == "telegram")
    channels = (await session.execute(stmt_chans)).scalars().all()
    channel_map = {c.id: c.target_id for c in channels if c.target_id}

    # 2. Consultar cola de publicaciones enviadas a Telegram desde la fecha
    stmt_q = (
        select(PublicationQueue)
        .where(
            and_(
                PublicationQueue.status == "sent",
                PublicationQueue.published_at >= since_date,
            )
        )
        .order_by(PublicationQueue.published_at.asc())
    )
    q_items = (await session.execute(stmt_q)).scalars().all()

    # Filtrar solo canales de Telegram
    tg_q_items = [
        q for q in q_items
        if q.book_hash and (q.channel_id in channel_map or default_channel)
    ]

    book_hashes = list({q.book_hash for q in tg_q_items})
    if not book_hashes:
        return []

    # 3. Cargar libros y sus series en una sola consulta batch
    stmt_books = (
        select(Book)
        .options(selectinload(Book.series_info))
        .where(Book.id.in_(book_hashes))
    )
    books_map = {b.id: b for b in (await session.execute(stmt_books)).scalars().all()}

    affected: list[dict[str, Any]] = []
    seen_posts: set[str] = set()

    for q in tg_q_items:
        book = books_map.get(q.book_hash)
        if not book or not book.tg_message_id:
            continue

        msg_id_str = str(book.tg_message_id).strip()
        if msg_id_str in seen_posts:
            continue
        seen_posts.add(msg_id_str)

        chat_id = getattr(book, "tg_chat_id", None) or channel_map.get(q.channel_id, default_channel)
        book_desc = (book.description or "").strip()
        series_info = book.series_info
        series_desc = (series_info.description or "").strip() if series_info else ""

        if book_desc and book_desc != series_desc:
            vol_disp = book.volume if book.volume is not None else "Único"
            affected.append(
                {
                    "book": book,
                    "title": book.title,
                    "volume": vol_disp,
                    "chat_id": chat_id,
                    "tg_message_id": msg_id_str,
                    "published_at": q.published_at,
                    "series_name": series_info.series_name if series_info else "Desconocida",
                    "volume_synopsis": book_desc,
                    "series_synopsis": series_desc,
                }
            )

    return affected


async def run_fix(
    apply_changes: bool = False,
    limit: int | None = None,
    delay: float = 2.0,
    since_str: str = "2026-08-17",
    channel_override: str = "@ZeePubs",
    bot_token: str | None = None,
):
    """Ejecuta el escaneo y la corrección de sinopsis."""
    from config.config_settings import config

    if bot_token:
        config.TELEGRAM_TOKEN = bot_token

    try:
        since_date = datetime.strptime(since_str, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Formato de fecha inválido: {since_str}. Use YYYY-MM-DD.")
        return

    mode_label = (
        "🔴 LIVE (APLICANDO CAMBIOS)" if apply_changes else "🟡 DRY-RUN (SIMULACIÓN)"
    )
    logger.info(f"=== INICIANDO SCRIPT DE CORRECCIÓN DE SINOPSIS [{mode_label}] ===")
    logger.info(f"📅 Filtro desde: {since_date.strftime('%Y-%m-%d')}")
    logger.info(f"⏱️ Retardo entre llamadas: {delay}s | Límite: {limit or 'Ilimitado'}")

    from core.db_manager_pg import pg_manager
    from services.library_ui.book_builders import build_book_rich_blocks
    from services.publisher.publisher_service import publisher_service
    from services.rich_message_service import RichMessageService
    from services.workgroup_service import workgroup_service

    await pg_manager.initialize()

    async with pg_manager.get_session() as session:
        affected = await find_affected_publications(
            session=session, since_date=since_date, default_channel=channel_override
        )

        total_found = len(affected)
        logger.info(
            f"📊 Publicaciones encontradas que requieren corrección: {total_found}"
        )

        if not affected:
            logger.info("✅ No se detectaron publicaciones pendientes de corrección.")
            return

        if limit:
            affected = affected[:limit]
            logger.info(f"ℹ️ Procesando lote limitado a {len(affected)} publicaciones.")

        # Tabla de visualización
        print("\n" + "=" * 115)
        print(
            f"{'#':<3} | {'MENSAJE TG':<12} | {'NOVELA / VOLUMEN':<35} | {'SINOPSIS ACTUAL (SERIE) vs NUEVA (VOL)':<55}"
        )
        print("=" * 115)

        for idx, item in enumerate(affected, 1):
            title_vol = f"{item['title'][:25]} (Vol. {item['volume']})"
            s_snip = clean_text_snippet(item["series_synopsis"], 40)
            v_snip = clean_text_snippet(item["volume_synopsis"], 40)
            comp_str = f"ACTUAL: {s_snip} -> NUEVA: {v_snip}"
            print(
                f"{idx:<3} | {item['tg_message_id']:<12} | {title_vol:<35} | {comp_str:<55}"
            )

        print("=" * 115 + "\n")

        if not apply_changes:
            logger.info(
                "💡 Modo Dry-Run finalizado. No se enviaron peticiones a Telegram.\n"
                "   Para aplicar estos cambios en vivo, ejecuta:\n"
                f"   python scripts/fix_published_synopsis.py --apply --delay {delay}"
            )
            return

        # Modo Live
        logger.info(
            f"🚀 Iniciando edición in-place en Telegram para {len(affected)} mensajes..."
        )
        success_count = 0
        failed_count = 0

        for idx, item in enumerate(affected, 1):
            book = item["book"]
            chat_id = item["chat_id"]
            msg_id = item["tg_message_id"]

            logger.info(
                f"[{idx}/{len(affected)}] Editando msg {msg_id} ({item['title']} Vol. {item['volume']})..."
            )

            try:
                # 1. Generar diccionario de datos de publicación (con prioridad de volumen activa)
                book_data = publisher_service._build_book_data_dict(book)

                # 2. Enriquecer créditos de grupos traductores/maquetadores
                try:
                    credits_meta = (
                        await workgroup_service.resolve_book_workgroup_credits(
                            book_id=book.id,
                            book_obj=book,
                            raw_meta=book_data,
                            public_link=book_data.get("download_link"),
                        )
                    )
                    book_data.update(credits_meta)
                except Exception as e:
                    logger.debug(
                        f"Aviso enriqueciendo créditos para libro {book.id}: {e}"
                    )

                # 3. Preparar archivos (Portada y EPUB para preservar attachments)
                import io

                from services.cover_service import resolve_cover_data

                cover_raw = (
                    book_data.get("cover_high")
                    or book_data.get("coverUrl")
                    or book_data.get("cover_original")
                )
                cover_data = await resolve_cover_data(cover_raw)

                files = {}
                if cover_data:
                    if isinstance(cover_data, (bytes, bytearray)):
                        files["tomozaki_cover"] = ("cover.jpg", cover_data, "image/jpeg")
                    elif isinstance(cover_data, str) and os.path.exists(cover_data):
                        with open(cover_data, "rb") as f:
                            files["tomozaki_cover"] = ("cover.jpg", f.read(), "image/jpeg")

                epub_path = (
                    book_data.get("filepath")
                    or book_data.get("file_path")
                    or book_data.get("descarga")
                )
                fname = book_data.get("filename") or (
                    os.path.basename(epub_path) if epub_path else "libro.epub"
                )
                if epub_path and os.path.exists(epub_path):
                    with open(epub_path, "rb") as f:
                        files["epub_file"] = (
                            fname,
                            io.BytesIO(f.read()),
                            "application/epub+zip",
                        )

                # 4. Construir Bloques Nativos (Rich Blocks)
                rich_blocks = build_book_rich_blocks(
                    book_data,
                    has_cover=bool("tomozaki_cover" in files),
                    include_download=bool("epub_file" in files),
                    show_nav_buttons=False,
                    volume_buttons=None,
                )

                # 5. Enviar edición in-place a Telegram
                res_edit = await RichMessageService.edit_rich_message(
                    chat_id=chat_id,
                    message_id=int(msg_id),
                    blocks=rich_blocks,
                    files=files if files else None,
                )

                if res_edit and res_edit.get("ok"):
                    logger.info(
                        f"✅ Mensaje {msg_id} actualizado exitosamente en Telegram."
                    )
                    success_count += 1
                else:
                    err_desc = (
                        res_edit.get("description", str(res_edit))
                        if res_edit
                        else "Sin respuesta de Telegram"
                    )
                    logger.warning(f"⚠️ Falló edición de msg {msg_id}: {err_desc}")
                    failed_count += 1

            except Exception as e:
                logger.error(f"❌ Error procesando msg {msg_id}: {e}")
                failed_count += 1

            # Pausa de seguridad anti-flood
            if idx < len(affected):
                await asyncio.sleep(delay)

        logger.info(
            f"\n🏁 PROCESO FINALIZADO:\n"
            f"   - Exitosos: {success_count}\n"
            f"   - Fallidos: {failed_count}\n"
            f"   - Total procesados: {len(affected)}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Corrige in-place la sinopsis de las publicaciones de Telegram posteriores al 17 de agosto."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Aplica los cambios reales en Telegram (por defecto es Dry-Run).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Solo simula y muestra qué publicaciones se actualizarían.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limita el número de publicaciones a procesar (ej. --limit 5).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Tiempo de espera en segundos entre peticiones a Telegram (default: 2.0s).",
    )
    parser.add_argument(
        "--since",
        type=str,
        default="2026-08-17",
        help="Fecha inicial en formato YYYY-MM-DD (default: 2026-08-17).",
    )
    parser.add_argument(
        "--channel",
        type=str,
        default="@ZeePubs",
        help="Handle o target_id del canal oficial (default: @ZeePubs).",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Token opcional del bot con permisos para editar mensajes en el canal.",
    )

    args = parser.parse_args()

    # Si se pasa explícitamente --apply, desactiva dry-run
    is_apply = args.apply

    asyncio.run(
        run_fix(
            apply_changes=is_apply,
            limit=args.limit,
            delay=args.delay,
            since_str=args.since,
            channel_override=args.channel,
            bot_token=args.token,
        )
    )


if __name__ == "__main__":
    main()
