import logging
import re
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.communications import (
    PublicationQueue,
)
from repositories.book_repository import BookRepository
from repositories.publication_repository import PublicationRepository
from utils.http_client import fetch_bytes
from utils.template_engine import apply_publication_template

logger = logging.getLogger(__name__)


class PublisherProvider:
    """Clase base para proveedores de publicación (Telegram, Facebook, etc)."""

    async def announce_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        raise NotImplementedError


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
        "📚 {serie} ║ {romaji_title} ║ {titulo}"
        "[?volumen]\n📖 Volumen {volumen}[/?]"
        "\n[?download_link]\n⬇️ Descarga: {download_link}[/?]\n"
        "\n[?layout_by]🎨 Maquetado por: {layout_by}[/?]"
        "[?tipo]\n🏷️ Categoría: {tipo}[/?]"
        "[?demography]\n👥 Demografía: {demography}[/?]"
        "[?genres]\n🎭 Géneros: {genres}[/?]"
        "[?autor]\n✍️ Autor: {autor}[/?]"
        "[?illustrator]\n🎨 Ilustrador: {illustrator}[/?]"
        "[?published_at]\n📅 Publicado: {published_at}[/?]"
        "[?traductor]\n🌐 Traductor: {traductor}[/?]"
        "[?editorial]\n🏢 Grupo Traductor: {editorial}[/?]"
        "\n📝 Sinopsis: {sinopsis}"
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

        html_parts = []
        if media:
            html_parts.append('<img src="tg://photo?id=tomozaki_cover" />\n')

        # Títulos en cascada
        from utils.metadata_utils import is_romaji_string

        title_en = book_data.get("english_title") or book_data.get("title") or book_data.get("titulo") or "Sin título"
        title_jp = book_data.get("romaji_title") or book_data.get("title_japanese") or book_data.get("title_jp")
        title_es = book_data.get("spanish_title") or book_data.get("title_spanish") or book_data.get("title_es")

        # Autocorrección de campos permutados
        if title_es and is_romaji_string(title_es):
            if not title_jp or title_jp == title_en:
                title_jp = title_es
            title_es = None

        if title_jp and (title_jp == title_en or not is_romaji_string(title_jp)):
            title_jp = None

        if title_es and (title_es == title_en or is_romaji_string(title_es)):
            title_es = None

        html_parts.append(f'<h3>🇬🇧 {title_en}</h3>')
        if title_jp:
            html_parts.append(f'<h4>🇯🇵 {title_jp}</h4>')
        if title_es:
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
            except:
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
                except:
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
        rich_sent = False
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
                rich_sent = True
                
                # B. Si el Rich Message se envió con éxito, enviar el documento ePub abajo con únicamente su hashtag
                epub_data = book_data.get("epub_bytes") or book_data.get("filepath")
                if epub_data:
                    if slug:
                        final_caption = slug if slug.startswith("#") else f"#{slug}"
                    else:
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
                epub_data = book_data.get("epub_bytes") or book_data.get("filepath")
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


class FacebookPublisherProvider(PublisherProvider):
    async def announce_book(self, target_id, book_data, options=None) -> bool:
        # Implementación simplificada para v4, delegando a httpx
        logger.info(f"Facebook announcement logic placeholder for target {target_id}")
        return True


class PublisherService:
    """
    Servicio Central de Publicación v4.0.
    Maneja la lógica de negocio, colas y proveedores.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PublicationRepository(session)
        self.book_repo = BookRepository(session)  # Inyectar sesión a BookRepository
        self.providers = {
            "telegram": TelegramPublisherProvider(),
            "facebook": FacebookPublisherProvider(),
        }

    async def schedule_publication(
        self,
        book_hash: str,
        channel_id: int,
        scheduled_for: datetime,
        template_id: int | None = None,
        payload: dict | None = None,
    ) -> PublicationQueue:
        """Programa una nueva publicación."""
        new_item = PublicationQueue(
            book_hash=book_hash,
            channel_id=channel_id,
            template_id=template_id,
            scheduled_for=scheduled_for,
            status="pending",
            payload=payload or {},
        )
        self.session.add(new_item)
        await self.session.flush()
        return new_item

    async def process_queue(self):
        """Procesa items pendientes en la cola."""
        pending = await self.repo.get_pending_queue(limit=10)
        for item in pending:
            try:
                item.status = "publishing"
                await self.session.flush()

                # Datos del libro: cargar siempre desde la base de datos si existe book_hash,
                # y luego permitir que el payload (opcional) sobrescriba cualquier campo.
                book_data = {}
                if item.book_hash:
                    book = await self.book_repo.get_by_hash(item.book_hash)
                    if book:
                        # Extraer metadatos para el template engine
                        book_data = {
                            "title": book.title,
                            "author": book.author
                            or (book.series.author if book.series else ""),
                            "volume": book.volume,
                            "cover_original": book.cover_original,
                            "cover_high": book.cover_high,
                            "cover_medium": book.cover_medium,
                            "cover_low": book.cover_low,
                            "portada": book.series.cover_url
                            if book.series
                            else (book.cover_medium or book.cover_low or ""),
                            "serie": (
                                book.series.series_english if book.series else None
                            )
                            or book.series_english
                            or "",
                            "series_english": (
                                book.series.series_english if book.series else None
                            )
                            or book.series_english
                            or "",
                            "series": (book.series.name if book.series else None)
                            or book.series_english
                            or "",
                            "romaji_title": (book.series.name if book.series else None)
                            or book.romaji_title
                            or "",
                            "romaji": (book.series.name if book.series else None)
                            or book.romaji_title
                            or "",
                            "series_spanish": (
                                book.series.series_spanish if book.series else None
                            )
                            or book.series_spanish
                            or book.title,
                            "sinopsis": (
                                book.series.description if book.series else None
                            )
                            or book.description
                            or "",
                            "generos": book.series.tags_json
                            if book.series
                            else (book.tags_json or []),
                            "tags": book.series.tags_json
                            if book.series
                            else (book.tags_json or []),
                            "demographics": book.series.demographics_json
                            if book.series
                            else (book.demographics_json or []),
                            "demography": book.series.demographics_json
                            if book.series
                            else (book.demographics_json or []),
                            "illustrator": (
                                book.series.illustrator if book.series else None
                            )
                            or book.illustrator
                            or "",
                            "author_jap": (
                                book.series.author_jap if book.series else None
                            )
                            or book.author_jap
                            or "",
                            "illustrator_jap": (
                                book.series.illustrator_jap if book.series else None
                            )
                            or book.illustrator_jap
                            or "",
                            "series_name": (book.series.name if book.series else None)
                            or book.series_english
                            or "",
                            "layout_by": book.layout_by if book.layout_by else "",
                            "book_type": book.series.book_type
                            if book.series
                            else "Light Novel",
                            "publisher": book.series.publisher if book.series else "",
                            "book_hash": book.book_hash,
                            "traductor": book.translator if book.translator else "",
                            "editorial": book.publisher
                            or (book.series.publisher if book.series else ""),
                            "epub_version": book.epub_version or "",
                            "version": book.epub_version or "",
                            "modified_at_opf": book.modified_at_opf.isoformat()
                            if book.modified_at_opf
                            else "",
                            "updated_at": book.file_modified_at.isoformat()
                            if book.file_modified_at
                            else "",
                            "filename": book.filename or "",
                            "filepath": book.filepath or "",
                            "file_size": book.file_size or 0,
                            "short_link": book.short_link or "",
                        }
                if item.payload:
                    book_data.update(item.payload)

                # Obtener proveedor
                platform = item.channel.platform if item.channel else "telegram"
                provider = self.providers.get(platform)

                # Cargar plantilla personalizada si existe
                caption = None
                cover_quality = "high"
                if item.template_id:
                    template = await self.repo.get_template_by_id(item.template_id)
                    if template:
                        # Compilar plantilla con los datos del libro
                        caption = apply_publication_template(
                            template.content, book_data
                        )
                        if (
                            template.extra_config
                            and "cover_quality" in template.extra_config
                        ):
                            saved_q = template.extra_config["cover_quality"]
                            # Convertir de español (del frontend) a la clave esperada en el backend
                            cover_quality = (
                                "high"
                                if saved_q == "grande"
                                else "medium"
                                if saved_q == "mediana"
                                else "low"
                                if saved_q == "pequeña"
                                else saved_q
                            )

                if provider:
                    # Extraer message_thread_id del config del canal
                    thread_id = None
                    if item.channel and item.channel.config:
                        thread_id = item.channel.config.get("message_thread_id")

                    success = await provider.announce_book(
                        item.channel.target_id,
                        book_data,
                        options={
                            "template_id": item.template_id,
                            "caption": caption,
                            "cover_quality": cover_quality,
                            "message_thread_id": thread_id,
                        },
                    )
                    item.status = "sent" if success else "failed"
                else:
                    item.status = "failed"
                    item.error_message = f"Provider {platform} not found"

                item.published_at = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error processing queue item {item.id}: {e}")
                item.status = "failed"
                item.error_message = str(e)

        await self.session.commit()

    async def get_channels(self, active_only: bool = True):
        return await self.repo.get_channels(active_only)

    async def get_channels_with_discovery(self, active_only: bool = True) -> dict:
        """Obtiene canales oficiales y chats descubiertos (v3.x compat)."""
        channels = await self.repo.get_channels(active_only)
        discovered = await self.repo.get_discovered_chats(limit=50)
        return {
            "channels": [
                {
                    "id": c.id,
                    "name": c.name,
                    "platform": c.platform,
                    "target_id": c.target_id,
                    "is_active": c.is_active,
                    "is_favorite": c.is_favorite,
                    "config": c.config or {},
                }
                for c in channels
            ],
            "discovered": [
                {
                    "chat_id": d.chat_id,
                    "title": d.title,
                    "type": d.type,
                    "username": d.username,
                    "member_count": d.member_count,
                    "last_seen": d.last_seen_at.isoformat() if d.last_seen_at else None,
                }
                for d in discovered
            ],
        }

    async def toggle_favorite(self, channel_id: int) -> bool:
        """Alterna el estado favorito de un canal."""
        channel = await self.repo.get_channel_by_id(channel_id)
        if channel:
            channel.is_favorite = not channel.is_favorite
            await self.session.flush()
            return True
        return False

    async def promote_discovered_to_channel(self, chat_id: str, name: str) -> bool:
        """Convierte un chat descubierto en un canal oficial."""
        from models.communications import PublicationChannel

        # Verificar si ya existe el canal
        channels = await self.repo.get_channels(active_only=False)
        if any(c.target_id == str(chat_id) for c in channels):
            return False

        # Crear nuevo canal
        new_channel = PublicationChannel(
            name=name, target_id=str(chat_id), platform="telegram", is_active=True
        )
        self.session.add(new_channel)
        await self.session.flush()
        return True

    async def upsert_chat(self, chat_id: str, title: str, chat_type: str, **kwargs):
        """Descubrimiento de chats."""
        return await self.repo.save_discovered_chat(chat_id, title, chat_type, **kwargs)


# --- Wrappers para compatibilidad global ---


class PublisherServiceWrapper:
    """Wrapper estático para PublisherService que gestiona sus propias sesiones."""

    @classmethod
    async def get_channels_with_discovery(cls, active_only: bool = True) -> dict:
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = PublisherService(session)
            return await service.get_channels_with_discovery(active_only)

    @classmethod
    async def toggle_favorite(cls, channel_id: int) -> bool:
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = PublisherService(session)
            res = await service.toggle_favorite(channel_id)
            await session.commit()
            return res

    @classmethod
    async def promote_discovered_to_channel(cls, chat_id: str, name: str) -> bool:
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = PublisherService(session)
            res = await service.promote_discovered_to_channel(chat_id, name)
            await session.commit()
            return res

    @classmethod
    async def schedule_publication(cls, **kwargs) -> Any:
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = PublisherService(session)
            res = await service.schedule_publication(**kwargs)
            await session.commit()
            return res

    @classmethod
    async def process_queue(cls):
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = PublisherService(session)
            await service.process_queue()


# Instancia exportada para compatibilidad con handlers v3.x
publisher_service = PublisherServiceWrapper
