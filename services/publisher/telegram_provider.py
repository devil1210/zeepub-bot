import logging
import os
import re
from datetime import datetime
from typing import Any

from services.publisher.base import PublisherProvider
from utils.http_client import fetch_bytes
from utils.template_engine import apply_publication_template

logger = logging.getLogger(__name__)


class TelegramPublisherProvider(PublisherProvider):
    # (Mantenemos las plantillas pero las usamos vía el engine)
    COVER_TEMPLATE = (
        "📚 {serie} ║ {romaji_title} ║ {titulo}"
        "[?volumen]\n📖 Volumen {volumen}[/?]"
        "\n#{slug}\n"
        "[?layout_by]\n🎨 <b>Maquetado por:</b> #{layout_by}[/?]"
        "[?tipo]\n🏷️ <b>Categoría:</b> {tipo}[/?]"
        "[?demography]\n👥 <b>Demografía:</b> {demography}[/?]"
        "[?genres]\n🎭 <b>Géneros:</b> {genres}[/?]"
        "[?autor]\n✍️ <b>Autor:</b> {autor}[/?]"
        "[?illustrator]\n🎨 <b>Ilustrador:</b> {illustrator}[/?]"
        "[?published_at]\n📅 <b>Publicado:</b> {published_at}[/?]"
        "[?traductor]\n🌐 <b>Traductor:</b> {traductor}[/?]"
        "[?editorial]\n🏢 <b>Grupo Traductor:</b> {editorial}[/?]"
    )
    SYNOPSIS_TEMPLATE = (
        "📝 <b>Sinopsis:</b>\n\n<blockquote>{sinopsis}</blockquote>\n\n#{slug}"
    )
    INFO_TEMPLATE = "📂 <b>{titulo}</b>\nℹ️ Versión Epub: {version}\n📅 Actualizado: {fecha}\n📦 Tamaño: {tamaño}\n\n#{slug}{archivo}"
    FULL_TEMPLATE = (
        COVER_TEMPLATE + "\n<hr/>\n" + SYNOPSIS_TEMPLATE + "\n<hr/>\n" + INFO_TEMPLATE
    )

    FB_CAPTION_TEMPLATE = (
        "📚 {serie} ║ {romaji_title} ║ {titulo}\n"
        "[?volumen]📖 Volumen {volumen}\n[/?]"
        "[?download_link]⬇️ Descarga: {download_link}\n[/?]"
        "[?fecha]📅 Actualizado: {fecha}\n[/?]"
        "[?tamaño]📦 Tamaño: {tamaño}\n[/?]"
        "[?layout_by]🎨 Maquetado por: {layout_by}\n[/?]"
        "[?tipo]🏷️ Categoría: {tipo}\n[/?]"
        "[?demography]👥 Demografía: {demography}\n[/?]"
        "[?genres]🎭 Géneros: {genres}\n[/?]"
        "[?autor]✍️ Autor: {autor}\n[/?]"
        "[?illustrator]🎨 Ilustrador: {illustrator}\n[/?]"
        "[?traductor]🌐 Traducción: {traductor}\n[/?]"
        "[?editorial]🏢 Grupo: {editorial}\n[/?]"
        "\n[?sinopsis]📝 Sinopsis:\n{sinopsis}\n[/?]"
        "\n[?slug]#{slug}[/?]"
    )

    def __init__(self, bot=None):
        self.bot = bot

    async def announce_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        from services.cover_service import send_doc_bytes, send_photo_bytes

        if not self.bot:
            from api.main import bot as main_bot

            self.bot = main_bot.app.bot

        options = options or {}
        thread_id = options.get("message_thread_id")

        def sanitize_tg_html(t: str) -> str:
            if not t:
                return ""
            t = re.sub(r"<(p|div|h\d)[^>]*>", "", t, flags=re.IGNORECASE)
            t = re.sub(r"</(p|div|h\d)>", "\n", t, flags=re.IGNORECASE)
            t = re.sub(r"<br\s*/?>", "\n", t, flags=re.IGNORECASE)
            t = re.sub(r"<hr\s*/?>", "\n---MSG_SPLIT---\n", t, flags=re.IGNORECASE)
            t = re.sub(r"\n{3,}", "\n\n", t).strip()
            return t

        caption_raw = options.get("caption") or apply_publication_template(
            self.COVER_TEMPLATE, book_data
        )
        msg_parts = re.split(r"<hr\s*/?>|---next---|---", caption_raw)
        msg_parts = [sanitize_tg_html(p) for p in msg_parts if p.strip()]

        # 1. Foto / Portada
        cover_quality = options.get("cover_quality", "high")

        # Determinar orden de fallback según la calidad de portada solicitada
        if cover_quality == "high":
            fallback_order = [
                "cover_high",
                "cover_original",
                "cover_medium",
                "cover_low",
            ]
        elif cover_quality == "medium":
            fallback_order = [
                "cover_medium",
                "cover_low",
                "cover_high",
                "cover_original",
            ]
        elif cover_quality == "low":
            fallback_order = [
                "cover_low",
                "cover_medium",
                "cover_high",
                "cover_original",
            ]
        elif cover_quality == "original":
            fallback_order = [
                "cover_original",
                "cover_high",
                "cover_medium",
                "cover_low",
            ]
        else:
            fallback_order = [
                f"cover_{cover_quality}",
                "cover_high",
                "cover_medium",
                "cover_low",
                "cover_original",
            ]

        cover_source = None
        for key in fallback_order:
            val = book_data.get(key)
            if val:
                cover_source = val
                break

        if not cover_source:
            cover_source = book_data.get("cover") or book_data.get("portada")

        cover_data = book_data.get("cover_bytes")
        if (
            not cover_data
            and isinstance(cover_source, str)
            and cover_source.startswith("http")
        ):
            cover_data = await fetch_bytes(cover_source)
        elif not cover_data:
            cover_data = cover_source

        # Resolver portada (bytes o ruta de archivo local) de forma asíncrona
        from services.cover_service import resolve_cover_data

        resolved_cover = (
            await resolve_cover_data(cover_data)
            if isinstance(cover_data, str)
            else cover_data
        )

        # --- CONSTRUIR RENDER RICH HTML (Telegram Premium) ---
        media = None
        files = None
        if resolved_cover:
            if isinstance(resolved_cover, bytes):
                files = {"tomozaki_cover": ("cover.jpg", resolved_cover, "image/jpeg")}
            elif isinstance(resolved_cover, str) and os.path.exists(resolved_cover):
                try:
                    with open(resolved_cover, "rb") as f:
                        files = {"tomozaki_cover": ("cover.jpg", f.read(), "image/jpeg")}
                except Exception as e:
                    logger.warning(f"Error al leer archivo de portada local para anuncio: {e}")

            if files:
                media = [
                    {
                        "id": "tomozaki_cover",
                        "media": {
                            "type": "photo",
                            "media": "attach://tomozaki_cover"
                        }
                    }
                ]

        # Si se proporcionó una plantilla personalizada (caption), usarla directamente para RichMessage
        if options and options.get("caption"):
            clean_user_caption = (
                caption_raw.replace("__ATTACH_FILE_SIGNAL__", "")
                .replace("{archivo}", "")
                .strip()
            )
            clean_user_caption = re.sub(
                r"<img\s+src=[^>]*>", "", clean_user_caption, flags=re.IGNORECASE
            ).strip()
            if media:
                html_content = (
                    f'<img src="tg://photo?id=tomozaki_cover" />\n{clean_user_caption}'
                )
            else:
                html_content = clean_user_caption
        else:
            html_parts = []
            if media:
                html_parts.append('<img src="tg://photo?id=tomozaki_cover" />\n')

            # Títulos en cascada
            title_en = book_data.get("english_title") or book_data.get("series_english")
            title_jp = book_data.get("romaji_title") or book_data.get("romaji") or book_data.get("title_japanese") or book_data.get("title_jp")
            title_es = book_data.get("spanish_title") or book_data.get("series_spanish") or book_data.get("title_spanish") or book_data.get("title")

            if not title_en and title_es:
                title_en = title_es
                title_es = None

            if title_en:
                html_parts.append(f'<h3>🇬🇧 {title_en}</h3>')
            if title_jp and title_jp != title_en:
                html_parts.append(f'<h4>🇯🇵 {title_jp}</h4>')
            if title_es and title_es != title_en:
                html_parts.append(f'<h5>🇪🇸 {title_es}</h5>')
                
            volume = book_data.get("volume")
            if volume:
                html_parts.append(f'<h6>📚 Volumen {volume}</h6>\n')

            # TABLA 1: Ficha artística y literaria
            tabla_literaria = '<table bordered striped>\n'
            autor = book_data.get("author") or book_data.get("autor") or "Desconocido"
            tabla_literaria += f'  <tr><td><b>👤 Autor</b></td><td>{autor}</td></tr>\n'
            
            ilustrador = book_data.get("illustrator") or book_data.get("ilustrador")
            if ilustrador:
                tabla_literaria += f'  <tr><td><b>🎨 Ilustrador</b></td><td>{ilustrador}</td></tr>\n'
                
            layout_by = book_data.get("layout_by") or book_data.get("maquetador")
            if layout_by:
                layout_val = layout_by if layout_by.startswith("#") else f"#{layout_by}"
                tabla_literaria += f'  <tr><td><b>💻 Maquetador</b></td><td>{layout_val}</td></tr>\n'
                
            categoria = book_data.get("book_type") or book_data.get("tipo") or "Novela"
            tabla_literaria += f'  <tr><td><b>📦 Categoría</b></td><td>{categoria}</td></tr>\n'
            
            demo = book_data.get("demographics_json") or book_data.get("demographics") or book_data.get("demografia")
            if demo:
                demo_val = ", ".join(demo) if isinstance(demo, list) else demo
                tabla_literaria += f'  <tr><td><b>👥 Demografía</b></td><td>{demo_val}</td></tr>\n'
                
            generos = book_data.get("tags_json") or book_data.get("tags") or book_data.get("generos")
            if generos:
                generos_val = ", ".join(generos) if isinstance(generos, list) else generos
                tabla_literaria += f'  <tr><td><b>🎭 Géneros</b></td><td>{generos_val}</td></tr>\n'
                
            traductor = book_data.get("translator") or book_data.get("traductor")
            if traductor:
                tabla_literaria += f'  <tr><td><b>🌐 Traductor</b></td><td>{traductor}</td></tr>\n'
                
            grupo_trad = book_data.get("publisher") or book_data.get("translation_group") or book_data.get("grupo_traductor")
            if grupo_trad:
                grupo_trad_val = grupo_trad
                if book_data.get("translation_group_url"):
                    url_g = book_data.get("translation_group_url")
                    grupo_trad_val = f'<a href="{url_g}">{grupo_trad}</a>'
                tabla_literaria += f'  <tr><td><b>🏢 Grupo Traductor</b></td><td>{grupo_trad_val}</td></tr>\n'
                
            tabla_literaria += '</table>\n'
            html_parts.append(tabla_literaria)

            # SINOPSIS: Acordeón colapsable
            sinopsis_raw = book_data.get("sinopsis") or book_data.get("description") or "Sin sinopsis disponible."
            html_parts.append(
                '<details>\n'
                '  <summary>📖 Ver Sinopsis</summary>\n'
                '  <blockquote>\n'
                f'    {sinopsis_raw}\n'
                '  </blockquote>\n'
                '</details>\n'
            )

            # TABLA 2: Detalles del archivo
            size_val = book_data.get("size")
            if not size_val and book_data.get("file_size"):
                try:
                    size_bytes = int(book_data.get("file_size"))
                    size_val = f"{size_bytes / (1024 * 1024):.2f} MB"
                except Exception:
                    size_val = "Desconocido"
            if not size_val:
                size_val = "Desconocido"

            version_val = book_data.get("epub_version") or book_data.get("version") or "3.0"

            tabla_archivo = (
                '<details>\n'
                '  <summary>📂 Ver Detalles del Archivo</summary>\n'
                '  <table bordered striped>\n'
                f'    <tr><td><b>📂 Nombre</b></td><td>{book_data.get("title") or "Desconocido"}</td></tr>\n'
            )
            if volume:
                tabla_archivo += f'    <tr><td><b>📖 Volumen</b></td><td>Volumen {volume}</td></tr>\n'
            
            tabla_archivo += f'    <tr><td><b>ℹ️ Versión Epub</b></td><td>{version_val}</td></tr>\n'
            
            fecha = book_data.get("updated_at") or book_data.get("actualizado") or book_data.get("indexed_at")
            if fecha:
                if hasattr(fecha, "strftime"):
                    fecha_str = fecha.strftime("%d-%m-%Y")
                elif isinstance(fecha, str):
                    try:
                        dt = datetime.fromisoformat(fecha)
                        fecha_str = dt.strftime("%d-%m-%Y")
                    except Exception:
                        fecha_str = fecha
                else:
                    fecha_str = str(fecha)
                tabla_archivo += f'    <tr><td><b>📅 Actualizado</b></td><td>{fecha_str}</td></tr>\n'
                
            tabla_archivo += f'    <tr><td><b>💾 Tamaño</b></td><td>{size_val}</td></tr>\n'
                
            tabla_archivo += (
                '  </table>\n'
                '</details>\n'
            )
            html_parts.append(tabla_archivo)

            # Línea divisoria y pie
            html_parts.append('<hr/>')
            
            slug = book_data.get("slug")
            if slug:
                hashtag_serie = slug if slug.startswith("#") else f"#{slug}"
                html_parts.append(f'{hashtag_serie}\n\n\n')
            else:
                clean_title = re.sub(r'[^\w\s]', '', title_en).replace(" ", "_")
                html_parts.append(f'#{clean_title}\n\n\n')

            html_content = "\n".join(html_parts)

        # A. Intentar enviar Rich Message unificado a través de Telegram API 10.2
        from services.rich_message_service import RichMessageService
        fname = book_data.get("filename", "libro.epub")
        try:
            res = await RichMessageService.send_rich_message(
                chat_id=target_id,
                html=html_content,
                media=media,
                files=files if files else None,
                message_thread_id=thread_id
            )
            if res and res.get("ok"):
                # B. Si el Rich Message se envió con éxito, enviar el documento ePub abajo con únicamente su hashtag
                epub_data = book_data.get("epub_bytes") or book_data.get("filepath") or book_data.get("file_path")
                if epub_data:
                    slug = book_data.get("slug")
                    if slug:
                        final_caption = slug if slug.startswith("#") else f"#{slug}"
                    else:
                        title_en = book_data.get("english_title") or book_data.get("series_english") or "book"
                        clean_title = re.sub(r'[^\w\s]', '', title_en).replace(" ", "_")
                        final_caption = f"#{clean_title}"

                    await send_doc_bytes(
                        self.bot,
                        target_id,
                        final_caption,
                        epub_data,
                        filename=fname,
                        parse_mode="HTML",
                        message_thread_id=thread_id,
                    )
                return True
        except Exception as e:
            logger.warning(f"Error al enviar Rich Message en announce_book: {e}")

        # Fallback tradicional si falla
        logger.info("Ejecutando fallback tradicional en TelegramPublisherProvider.announce_book")
        photo_sent = False
        for part in msg_parts:
            if not part.strip():
                continue

            if "__ATTACH_FILE_SIGNAL__" in part or "{archivo}" in part:
                part = (
                    part.replace("__ATTACH_FILE_SIGNAL__", "")
                    .replace("{archivo}", "")
                    .strip()
                )
                epub_data = book_data.get("epub_bytes") or book_data.get("filepath") or book_data.get("file_path")
                await send_doc_bytes(
                    self.bot,
                    target_id,
                    part,
                    epub_data,
                    filename=fname,
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
            else:
                sent_photo = None
                if resolved_cover and not photo_sent:
                    try:
                        sent_photo = await send_photo_bytes(
                            self.bot,
                            target_id,
                            part,
                            resolved_cover,
                            parse_mode="HTML",
                            message_thread_id=thread_id,
                        )
                        if sent_photo:
                            photo_sent = True
                    except Exception as e:
                        logger.warning(f"Error al enviar portada como foto: {e}")

                if not sent_photo:
                    await self.bot.send_message(
                        chat_id=target_id,
                        text=part,
                        parse_mode="HTML",
                        message_thread_id=thread_id,
                    )

        return True
