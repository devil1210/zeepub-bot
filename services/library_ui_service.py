import io
import logging
import os
import re
import uuid

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config.config_settings import config
from core.state_manager import state_manager
from services.keyboard_factory import BotKeyboards
from services.library_service import LibraryService
from services.rich_message_service import RichMessageService
from utils.helpers import (
    get_thread_id,
    get_translator_acronym,
    normalize_demography,
    resolve_title_cascade,
)

logger = logging.getLogger(__name__)


async def mostrar_menu_principal(
    update: Update, context: ContextTypes.DEFAULT_TYPE, force_new: bool = False
):
    """Muestra el menú principal basado en la BD local."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    st["historial"] = []
    st["current_view"] = "main"
    st["titulo"] = "📚 Biblioteca Local"

    webapp_url = getattr(config, "WEBAPP_URL", None)
    reply_markup = BotKeyboards.main_menu(webapp_url=webapp_url)

    text = (
        "<b>📚 Bienvenido a la Biblioteca Local</b>\n\n"
        "✨ <i>Explora nuestra colección curada de Novelas Ligeras.</i>\n\n"
        "🎯 <b>¿Qué novela te apetece leer hoy?</b>"
    )

    if update.callback_query and not force_new:
        try:
            await update.callback_query.edit_message_text(
                text, reply_markup=reply_markup, parse_mode="HTML"
            )
            return
        except Exception:
            pass

    # Si no hay callback, o force_new=True, o falló la edición (mensaje borrado)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML",
        message_thread_id=get_thread_id(update),
    )


async def mostrar_generos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra lista de géneros."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    genres = await LibraryService.get_genres()

    reply_markup = BotKeyboards.genres_grid(genres)

    st["current_view"] = "genres"
    st["prev_view_local"] = "main"
    st["titulo"] = "🏷️ Géneros"

    text = "<b>🏷️ Selecciona un Género:</b>"
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )


async def mostrar_series(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    origin_type: str,
    filter_val: str = None,
    page: int = 1,
    force_new: bool = False,
):
    """Muestra series filtradas por tag, autor o todas."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    page_size = 10

    st["origin_type"] = origin_type
    st["filter_val"] = filter_val
    st["current_page"] = page

    if origin_type == "genre":
        data = await LibraryService.get_series_by_tag(
            filter_val, page=page, page_size=page_size
        )
        title = f"🏷️ Género: {filter_val}"
        st["prev_view_local"] = "genres"
    elif origin_type == "author":
        data = await LibraryService.get_series_by_author(
            filter_val, page=page, page_size=page_size
        )
        title = f"✍️ Autor: {filter_val}"
        st["prev_view_local"] = "authors"
    else:  # newest or all_series
        sort = "newest" if origin_type == "newest" else "a-z"
        res = await LibraryService.search_series(
            "", page=page, items_per_page=page_size, sort_by=sort
        )
        data = {"items": res["results"], "total": res["totalItems"]}
        title = "⭐ Novedades" if origin_type == "newest" else "📖 Todas las Series"
        st["prev_view_local"] = "main"

    st["colecciones"] = {}
    items = []

    for i, s in enumerate(data["items"]):
        href = f"local_series|{s['series_hash']}"
        series_title = s.get("name") or s.get("series_name") or s.get("title", "Novela")
        st["colecciones"][i] = {"titulo": series_title, "href": href}
        items.append({"title": series_title, "index": i})

    total_pages = (data["total"] + page_size - 1) // page_size if data["total"] > 0 else 1
    reply_markup = BotKeyboards.series_list(
        items=items,
        origin_type=origin_type,
        filter_val=filter_val,
        page=page,
        total_pages=total_pages,
    )

    st["current_view"] = "series_list"
    st["titulo"] = title

    text = f"<b>{title}</b>\nResultados: {data['total']} series."
    if update.callback_query and not force_new:
        try:
            await update.callback_query.edit_message_text(
                text, reply_markup=reply_markup, parse_mode="HTML"
            )
        except Exception:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
                message_thread_id=get_thread_id(update),
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )


async def mostrar_libros(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    origin_type: str = "recent",
    filter_val: str = None,
    page: int = 1,
):
    """Muestra libros filtrados o recientes (paginados 10 max)."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    page_size = 10

    st["origin_type_b"] = origin_type
    st["filter_val_b"] = filter_val
    st["current_page_b"] = page
    st["prev_view_local"] = "main"

    if origin_type == "recent":
        data = await LibraryService.get_recent_books(
            page=page, items_per_page=page_size
        )
    else:
        data = {"items": [], "totalItems": 0, "totalPages": 0}

    st["libros"] = {}
    items = []

    for b in data.get("items", []):
        key = uuid.uuid4().hex[:8]
        display = f"📕 {b['title']}"
        st["libros"][key] = {
            "titulo": b["title"],
            "autor": b["author"],
            "descarga": b["filepath"],
            "portada": b.get("coverUrl", b.get("cover_medium") or b.get("cover_low")),
            "hash": b["book_hash"],
        }
        items.append({"key": key, "title": b["title"], "display": display})

    total_pages = data.get("totalPages", 1)
    reply_markup = BotKeyboards.books_list(
        items=items,
        origin_type=origin_type,
        filter_val=filter_val,
        page=page,
        total_pages=total_pages,
    )

    st["current_view"] = "books_list"
    title = "📚 Catálogo de Libros" if origin_type == "recent" else "📖 Libros"
    st["titulo"] = title

    text = f"<b>{title}</b>\n✨ Explorando {data.get('totalItems', 0)} libros disponibles (Pág. {page}/{total_pages})."

    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )


async def mostrar_volumenes_local(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    series_hash: str,
    force_new: bool = False,
):
    """Muestra volúmenes de una serie local."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    volumes = await LibraryService.get_series_volumes(series_hash)
    meta = await LibraryService.get_series_metadata(series_hash)

    series_name = meta.series_name if meta else "Serie"
    st["libros"] = {}
    volumes_items = []

    for v in volumes:
        key = uuid.uuid4().hex[:8]
        # Formato: Vol. X [TR] [Color]
        vol = v.get("volume")
        if vol is None or vol == "":
            vol = 0

        try:
            f_vol = float(vol)
            vol_display = int(f_vol) if f_vol.is_integer() else f_vol
        except (ValueError, TypeError):
            vol_display = vol

        if vol_display == 0:
            vol_str = "📖 Volumen Único"
        else:
            vol_str = f"📖 Vol. {vol_display}"

        translator = v.get("translator")
        tr_acronym = v.get("translator_siglas") or get_translator_acronym(translator)

        is_color = v.get("color_mode") == "color"
        color_tag = " [🎨]" if is_color else ""

        display = f"{vol_str} [{tr_acronym}]{color_tag}"

        st["libros"][key] = {
            "titulo": v.get("title", ""),
            "autor": v.get("author", ""),
            "descarga": v.get("filepath", "N/A"),
            "portada": v.get("coverUrl", ""),
            "hash": v.get("book_hash", ""),
            "display": display,
            "series": series_name,
            "volume": vol,
            "translator": translator,
            "translator_siglas": tr_acronym,
            "color": is_color,
        }

        volumes_items.append({"key": key, "display": display, "volume": vol})

    reply_markup = BotKeyboards.series_volumes(volumes_items)

    st["current_view"] = "volumes_local"
    st["current_series_hash"] = series_hash

    text = (
        f"<b>📖 {series_name}</b>\n\nSelecciona un volumen para obtener más detalles:"
    )

    # Intentar editar, si falla (mensaje borrado), enviar uno nuevo
    if update.callback_query and not force_new:
        try:
            await update.callback_query.edit_message_text(
                text, reply_markup=reply_markup, parse_mode="HTML"
            )
        except Exception:
            # Si el mensaje original fue borrado (común en flujo de detalles), enviamos uno nuevo
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
                message_thread_id=get_thread_id(update),
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )


async def mostrar_detalles_libro(
    update: Update, context: ContextTypes.DEFAULT_TYPE, key: str
):
    """
    Muestra la ficha técnica del libro con el flujo de 3 mensajes: Portada, Sinopsis y Technical Info.
    Sigue el patrón Premium/Glassmorphism y sincroniza la cuota de descargas.
    """
    from services.cover_service import resolve_cover_data, send_photo_bytes
    from services.metadata_orchestrator.metadata_service import metadata_orchestrator
    from services.publisher.publisher_service import TelegramPublisherProvider
    from utils.download_limiter import downloads_left
    from utils.helpers import get_thread_id
    from utils.template_engine import apply_publication_template

    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    # Actualizar vista actual
    st["current_view"] = "detalles_libro"

    libro_st = st.get("libros", {}).get(key)

    if not libro_st:
        logger.warning(f"Libro no encontrado en estado para key: {key}")
        if update.callback_query:
            await update.callback_query.answer(
                "⚠️ Información no disponible.", show_alert=True
            )
        return

    # 1. Obtener Metadata Enriquecida (incluye sinopsis y detalles técnicos)
    book_id = libro_st.get("hash") or libro_st.get("descarga")
    meta = await metadata_orchestrator.get_enriched_metadata(book_id)

    # Actualizar estado local con la data enriquecida
    st["libros"][key].update(meta)
    libro = st["libros"][key]

    # 2. Preparar Capciones usando el Publisher Provider oficial (Garantiza paridad bot/canal)
    # Parte 0: Portada/Principal, Parte 1: Sinopsis, Parte 2: Info técnica
    from repositories.publication_repository import pub_repo

    try:
        db_templates = await pub_repo.get_templates(platform="telegram")
        cover_t = next(
            (t for t in db_templates if (t.extra_config or {}).get("type") == "cover"),
            None,
        )
        synopsis_t = next(
            (
                t
                for t in db_templates
                if (t.extra_config or {}).get("type") == "synopsis"
            ),
            None,
        )
        info_t = next(
            (t for t in db_templates if (t.extra_config or {}).get("type") == "info"),
            None,
        )

        cover_content = (
            cover_t.content if cover_t else TelegramPublisherProvider.COVER_TEMPLATE
        )
        syn_content = (
            synopsis_t.content
            if synopsis_t
            else TelegramPublisherProvider.SYNOPSIS_TEMPLATE
        )
        info_content = (
            info_t.content if info_t else TelegramPublisherProvider.INFO_TEMPLATE
        )
    except Exception as e:
        logger.warning(
            f"Error cargando plantillas de base de datos en mostrar_detalles_libro: {e}"
        )
        cover_content = TelegramPublisherProvider.COVER_TEMPLATE
        syn_content = TelegramPublisherProvider.SYNOPSIS_TEMPLATE
        info_content = TelegramPublisherProvider.INFO_TEMPLATE

    templates = [
        cover_content,
        syn_content,
        info_content,
    ]

    # Fallback si no hay sinopsis
    if not libro.get("sinopsis") and libro.get("description"):
        libro["sinopsis"] = libro.get("description")

    # Si aún no hay sinopsis, la cubrimos
    if not libro.get("sinopsis"):
        libro["sinopsis"] = "Sin sinopsis disponible."

    # Mapeo manual para asegurar que todas las variables del template están presentes
    t_en, t_jp, t_es = resolve_title_cascade(libro)

    libro_map = libro.copy()
    libro_map.update(
        {
            "series_english": t_en,
            "romaji_title": t_jp or "",
            "romaji": t_jp or "",
            "series_spanish": t_es or "",
            "spanish_title": t_es or "",
            "slug": libro.get("slug") or "",
            "layout_by": libro.get("layout_by") or "Desconocido",
            "traductor": libro.get("translator") or "Desconocida",
            # Pasar como listas para que apply_publication_template los procese correctamente
            "tags": libro.get("tags", []),
            "demographics": libro.get("demographics", []),
            "tipo": libro.get("book_type") or "Novela",
        }
    )

    # Limpiamos HTML de las partes antes de enviar (Telegram es delicado)
    def sanitize_tg_html(t: str) -> str:
        if not t:
            return ""

        t = re.sub(r"<(/?p|/?div|/?h\d|/?span|/?a[^>]*)>", "\n", t, flags=re.IGNORECASE)
        t = re.sub(r"<br\s*/?>", "\n", t, flags=re.IGNORECASE)
        t = re.sub(r"<hr\s*/?>", "\n---\n", t, flags=re.IGNORECASE)
        t = re.sub(r"\n{3,}", "\n\n", t).strip()
        return t

    part0 = sanitize_tg_html(apply_publication_template(templates[0], libro_map))
    part1 = sanitize_tg_html(apply_publication_template(templates[1], libro_map))
    part2 = sanitize_tg_html(apply_publication_template(templates[2], libro_map))

    # IMPORTANTE: El template INFO_TEMPLATE incluye {archivo} que se expande a __ATTACH_FILE_SIGNAL__
    # Para la visualización previa en el bot, lo eliminamos para que no ensucie el slug
    part2 = part2.replace("__ATTACH_FILE_SIGNAL__", "").strip()

    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)

    # 3. Limpiar Menú de Volúmenes (Efecto de transición al detalle)
    if update.callback_query:
        try:
            await update.callback_query.message.delete()
        except Exception:
            pass

    # 4. ENVIAR MENSAJES (Flujo solicitado: Portada -> Sinopsis -> Detalles)
    if "last_detalles_msg_ids" not in st:
        st["last_detalles_msg_ids"] = []

    # IMPORTANTE: No limpiamos la lista aquí para que los comandos /cancel o 'cerrar' puedan
    # encontrar el mensaje con botones y quitarlos sin borrar la info.
    if update.callback_query:
        # Notificar que se queda en espera de forma sutil
        await update.callback_query.answer(
            "📌 Ficha técnica fijada en el chat.", show_alert=False
        )

    # A. Resolver Portada y preparar multimedia para Rich HTML
    portada_raw = (
        libro.get("cover_high")
        or libro.get("cover_medium")
        or libro.get("cover_low")
        or libro.get("cover_original")
        or libro.get("portada")
    )
    portada = await resolve_cover_data(portada_raw)

    files = {}
    media = None

    if portada:
        if isinstance(portada, bytes):
            files["tomozaki_cover"] = ("cover.png", io.BytesIO(portada), "image/png")
            media = [
                {
                    "id": "tomozaki_cover",
                    "media": {"type": "photo", "media": "attach://tomozaki_cover"},
                }
            ]
        elif isinstance(portada, str) and os.path.exists(portada):
            try:
                with open(portada, "rb") as f:
                    file_bytes = f.read()
                files["tomozaki_cover"] = (
                    "cover.png",
                    io.BytesIO(file_bytes),
                    "image/png",
                )
                media = [
                    {
                        "id": "tomozaki_cover",
                        "media": {"type": "photo", "media": "attach://tomozaki_cover"},
                    }
                ]
            except Exception as ex:
                logger.error(f"[UI Service] Error leyendo archivo de portada: {ex}")

    # B. Preparar Botones e información técnica del usuario
    left = await downloads_left(uid)
    left_str = (
        f"tienes {left} descargas restantes hoy"
        if isinstance(left, int)
        else "tienes descargas ilimitadas"
    )

    reply_markup = BotKeyboards.book_details(key=key)

    # C. Construir HTML dinámico para el Rich Message unificado
    html_parts = []

    # 1. Imagen al inicio de todo
    if media:
        html_parts.append('<img src="tg://photo?id=tomozaki_cover" />\n')

    # 2. Títulos en cascada
    title_en, title_jp, title_es = resolve_title_cascade(libro)
    html_parts.append(f"<h3>🇬🇧 {title_en}</h3>")
    if title_jp:
        html_parts.append(f"<h4>🇯🇵 {title_jp}</h4>")
    if title_es:
        html_parts.append(f"<h5>🇪🇸 {title_es}</h5>")

    volume = libro.get("volume")
    if volume:
        html_parts.append(f"<h6>📚 Volumen {volume}</h6>\n")

    # 3. TABLA 1: Ficha artística y literaria
    tabla_literaria = "<table bordered striped>\n"

    autor = libro.get("author") or libro.get("autor") or "Desconocido"
    tabla_literaria += f"  <tr><td><b>👤 Autor</b></td><td>{autor}</td></tr>\n"

    ilustrador = libro.get("illustrator") or libro.get("ilustrador")
    if ilustrador:
        tabla_literaria += (
            f"  <tr><td><b>🎨 Ilustrador</b></td><td>{ilustrador}</td></tr>\n"
        )

    layout_by = libro.get("layout_by") or libro.get("maquetador")
    if layout_by:
        maqs = [
            m.strip()
            for m in re.split(r"[,;]+|\s+(?=#)|\s+", str(layout_by))
            if m.strip()
        ]
        layout_val = " ".join(m if m.startswith("#") else f"#{m}" for m in maqs)
        tabla_literaria += (
            f"  <tr><td><b>💻 Maquetador</b></td><td>{layout_val}</td></tr>\n"
        )

    categoria = libro.get("book_type") or libro.get("tipo") or "Novela"
    tabla_literaria += f"  <tr><td><b>📦 Categoría</b></td><td>{categoria}</td></tr>\n"

    demo = (
        libro.get("demographics_json")
        or libro.get("demographics")
        or libro.get("demografia")
    )
    demo_val = normalize_demography(demo)
    if demo_val:
        tabla_literaria += (
            f"  <tr><td><b>👥 Demografía</b></td><td>{demo_val}</td></tr>\n"
        )

    generos = libro.get("tags_json") or libro.get("tags") or libro.get("generos")
    if generos:
        generos_val = ", ".join(generos) if isinstance(generos, list) else generos
        tabla_literaria += (
            f"  <tr><td><b>🎭 Géneros</b></td><td>{generos_val}</td></tr>\n"
        )

    traductor = libro.get("translator") or libro.get("traductor")
    if traductor:
        tabla_literaria += (
            f"  <tr><td><b>🌐 Traductor</b></td><td>{traductor}</td></tr>\n"
        )

    grupo_trad = (
        libro.get("publisher")
        or libro.get("translation_group")
        or libro.get("grupo_traductor")
    )
    if grupo_trad:
        grupo_trad_val = grupo_trad
        if libro.get("translation_group_url"):
            url_g = libro.get("translation_group_url")
            grupo_trad_val = f'<a href="{url_g}">{grupo_trad}</a>'
        tabla_literaria += (
            f"  <tr><td><b>🏢 Grupo Traductor</b></td><td>{grupo_trad_val}</td></tr>\n"
        )

    tabla_literaria += "</table>\n"
    html_parts.append(tabla_literaria)

    # 4. SINOPSIS: Acordeón colapsable
    sinopsis_raw = libro.get("sinopsis") or "Sin sinopsis disponible."
    html_parts.append(
        "<details>\n"
        "  <summary>📖 Ver Sinopsis</summary>\n"
        "  <blockquote>\n"
        f"    {sinopsis_raw}\n"
        "  </blockquote>\n"
        "</details>\n"
    )

    # 5. TABLA 2: Detalles del archivo
    size_val = libro.get("size")
    if not size_val and libro.get("file_size"):
        try:
            size_bytes = int(libro.get("file_size"))
            size_val = f"{size_bytes / (1024 * 1024):.2f} MB"
        except Exception:
            size_val = "Desconocido"
    if not size_val:
        size_val = "Desconocido"

    version_val = libro.get("epub_version") or libro.get("version") or "3.0"

    tabla_archivo = (
        "<details>\n"
        "  <summary>📂 Ver Detalles del Archivo</summary>\n"
        "  <table bordered striped>\n"
        f"    <tr><td><b>📂 Nombre</b></td><td>{libro.get('title') or 'Desconocido'}</td></tr>\n"
    )
    if volume:
        tabla_archivo += (
            f"    <tr><td><b>📖 Volumen</b></td><td>Volumen {volume}</td></tr>\n"
        )

    tabla_archivo += (
        f"    <tr><td><b>ℹ️ Versión Epub</b></td><td>{version_val}</td></tr>\n"
    )

    fecha = (
        libro.get("updated_at") or libro.get("actualizado") or libro.get("indexed_at")
    )
    if fecha:
        if hasattr(fecha, "strftime"):
            fecha_str = fecha.strftime("%d-%m-%Y")
        else:
            fecha_str = str(fecha)
        tabla_archivo += (
            f"    <tr><td><b>📅 Actualizado</b></td><td>{fecha_str}</td></tr>\n"
        )

    tabla_archivo += f"    <tr><td><b>💾 Tamaño</b></td><td>{size_val}</td></tr>\n"

    tabla_archivo += "  </table>\n</details>\n"
    html_parts.append(tabla_archivo)

    # 6. Línea divisoria y pie con espaciado real para teclado
    html_parts.append("<hr/>")

    slug = libro.get("slug")
    if slug:
        hashtag_serie = slug if slug.startswith("#") else f"#{slug}"
        html_parts.append(f"<p>{hashtag_serie}</p>")
    else:
        clean_title = re.sub(r"[^\w\s]", "", title_en).replace(" ", "_")
        html_parts.append(f"<p>#{clean_title}</p>")

    html_parts.append("<br/><br/>")

    html_content = "\n".join(html_parts)

    # D. Intentar enviar Rich Message unificado
    res = await RichMessageService.send_rich_message(
        chat_id=chat_id,
        html=html_content,
        media=media,
        files=files if files else None,
        reply_markup=reply_markup,
        message_thread_id=thread_id,
    )

    # E. Fallback tradicional si la API de Telegram o el transporte fallan
    if not res or not res.get("ok"):
        logger.warning(
            "[UI Service] Fallback a mensajes tradicionales en mostrar_detalles_libro"
        )

        # 1. Enviar portada tradicional
        msg_portada = None
        if portada:
            msg_portada = await send_photo_bytes(
                context.bot,
                chat_id,
                part0,
                portada,
                parse_mode="HTML",
                message_thread_id=thread_id,
            )

        if not msg_portada:
            msg_portada = await context.bot.send_message(
                chat_id=chat_id,
                text=part0,
                parse_mode="HTML",
                message_thread_id=thread_id,
            )

        if msg_portada:
            st["last_detalles_msg_ids"].append(msg_portada.message_id)

        # 2. Mensaje de Sinopsis plano
        msg_sinopsis = await context.bot.send_message(
            chat_id=chat_id, text=part1, parse_mode="HTML", message_thread_id=thread_id
        )
        if msg_sinopsis:
            st["last_detalles_msg_ids"].append(msg_sinopsis.message_id)

        # 3. Mensaje Técnico plano + Botones + Cuota
        text_final = f"{part2}\n\n💡 <i>Recuerda que {left_str}.</i>"
        msg_info = await context.bot.send_message(
            chat_id=chat_id,
            text=text_final,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )
        if msg_info:
            st["last_detalles_msg_ids"].append(msg_info.message_id)
    else:
        # Si fue exitoso el Rich Message, guardamos su ID de mensaje para limpieza
        rich_msg_id = res.get("result", {}).get("message_id")
        if rich_msg_id:
            st["last_detalles_msg_ids"].append(rich_msg_id)


async def mostrar_autores_local(
    update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1
):
    """Muestra lista de autores locales paginada."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    page_size = 10

    data = await LibraryService.get_authors(page=page, page_size=page_size)
    authors = data["items"]
    total = data["total"]

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    reply_markup = BotKeyboards.authors_list(
        authors=authors, page=page, total_pages=total_pages
    )

    st["current_view"] = "authors"
    st["prev_view_local"] = "main"
    st["titulo"] = "✍️ Autores"

    text = f"<b>✍️ Selecciona un Autor:</b>\nMostrando {len(authors)} autores (Pág. {page}/{total_pages})."
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )


async def mostrar_resultados_locales(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: str,
    series: list,
    books_standalone: list = None,
):
    """Muestra los resultados de una búsqueda local agrupada por series."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    st["libros"] = {}
    st["colecciones"] = {}
    series_items = []

    # 1. Agregar Series (Resultados agrupados)
    if series:
        for i, s in enumerate(series):
            if i >= 15:
                break
            href = f"local_series|{s['series_hash']}"
            series_title = (
                s.get("series_english")
                or s.get("name_english")
                or s.get("name")
                or s.get("series_name")
                or s.get("title", "Novela")
            )
            st["colecciones"][i] = {"titulo": series_title, "href": href}
            series_items.append({"title": series_title, "index": i})

    # 2. Agregar Libros "Sueltos" (que no pertenecen a las series encontradas o no tienen serie)
    books_items = []
    if books_standalone:
        for b in books_standalone:
            if len(books_items) >= 15:
                break
            key = uuid.uuid4().hex[:8]

            eng_t = b.get("english_title") or b.get("series_english")
            if eng_t:
                vol_num = b.get("volume")
                if vol_num and vol_num > 0:
                    vol_str = f" {int(vol_num)}" if vol_num % 1 == 0 else f" {vol_num}"
                    display_title = f"{eng_t} - Volumen {vol_str}"
                else:
                    display_title = eng_t
            else:
                display_title = b["title"]

            display = f"📕 {display_title}"
            st["libros"][key] = {
                "titulo": display_title,
                "autor": b["author"],
                "descarga": b["filepath"],
                "portada": b.get("cover_medium") or b.get("cover_low"),
                "hash": b["book_hash"],
            }
            books_items.append({"key": key, "title": display_title, "display": display})

    reply_markup = BotKeyboards.search_results(
        series_items=series_items, books_items=books_items
    )

    st["current_view"] = "search_results"
    st["titulo"] = f"🔍 Resultado: {query}"

    total_s = len(series) if series else 0
    total_b = len(books_standalone) if books_standalone else 0

    if total_s > 0 or total_b > 0:
        text = f"<b>🔍 Resultados para:</b> {query}\n"
        if total_s > 0:
            text += f"📂 Encontradas <b>{total_s}</b> series.\n"
        if total_b > 0:
            text += f"📕 Encontrados <b>{total_b}</b> libros individuales.\n"
    else:
        text = f"❌ No se han encontrado resultados para: <b>{query}</b>"

    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )
