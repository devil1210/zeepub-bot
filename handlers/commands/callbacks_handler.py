# handlers/commands/callbacks_handler.py
"""
Manejador centralizado de Callback Queries para Telegram (ZeePub v3.6+).
Coordina la navegación por el catálogo y delega operaciones a submódulos especializados.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from core.state_manager import state_manager
from handlers.commands.admin_callbacks import handle_admin_callback
from handlers.commands.base_handler import BaseCommandHandler
from handlers.commands.download_callbacks import handle_download_callback
from handlers.commands.publish_callbacks import handle_publish_callback
from services.library_ui_service import (
    build_book_rich_blocks,
    cancel_nav_timer,
    is_nav_expired,
    mostrar_autores_local,
    mostrar_ayuda,
    mostrar_detalles_libro,
    mostrar_donaciones,
    mostrar_generos,
    mostrar_libros,
    mostrar_menu_principal,
    mostrar_reglas,
    mostrar_series,
    mostrar_volumenes_local,
    pedir_termino_busqueda,
)
from services.rich_message_service import RichMessageService
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


class CallbackHandlerV6(BaseCommandHandler):
    """Manejador unificado de navegación por botones y callbacks de Telegram."""

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return

        data = query.data
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)
        msg_id = query.message.message_id if query.message else None
        chat_id = update.effective_chat.id
        is_downloaded_msg = bool(msg_id and msg_id in st.get("downloaded_msgs", set()))

        # Si el usuario interactúa desde un mensaje que contiene un libro descargado,
        # limpiamos sus botones de navegación para preservarlo intacto en el chat.
        if is_downloaded_msg:
            down_data = st.get("libros_downloaded", {}).pop(msg_id, {})
            dl_libro = down_data.get("libro") or {}
            dl_files = down_data.get("files")
            if dl_libro:
                clean_blocks = build_book_rich_blocks(
                    dl_libro,
                    has_cover=bool(dl_files and "tomozaki_cover" in dl_files),
                    include_download=True,
                    volume_buttons=None,
                    show_nav_buttons=False,
                )
                try:
                    await RichMessageService.edit_rich_message(
                        chat_id=chat_id,
                        message_id=msg_id,
                        blocks=clean_blocks,
                        files=dl_files if dl_files else None,
                    )
                except Exception as e:
                    logger.warning(f"Error limpiando botones de mensaje descargado: {e}")
            st["downloaded_msgs"].discard(msg_id)

            if data in ("noop", "salir", "cerrar", "cerrar_mensaje"):
                try:
                    await query.answer("¡Lectura guardada! 📚", show_alert=False)
                except Exception:
                    pass
                return

        # 1. Responder callback
        try:
            await query.answer()
        except Exception:
            pass

        if data == "noop":
            return

        # Expiración por inactividad (10 minutos)
        if is_nav_expired(chat_id, msg_id):
            if data in (
                "main_menu",
                "volver_menu",
                "nav_back",
                "volver",
                "salir",
                "cerrar_mensaje",
            ) or data.startswith("nav_local|"):
                try:
                    await query.answer(
                        "⚠️ Los botones de navegación han expirado por inactividad (10 min). Usa /start o /menu para abrir uno nuevo.",
                        show_alert=True,
                    )
                except Exception:
                    pass
                return

        try:
            # 0. Salir / Cerrar Mensaje
            if data in ("salir", "cerrar_mensaje", "cerrar"):
                cancel_nav_timer(chat_id, msg_id)
                if not is_downloaded_msg and query.message:
                    try:
                        await query.message.delete()
                    except Exception:
                        pass
                try:
                    await query.answer("Navegación cerrada. 👋", show_alert=False)
                except Exception:
                    pass
                return

            # Delegar a submódulos especializados
            if await handle_admin_callback(update, context, data):
                return

            if await handle_download_callback(update, context, data):
                return

            if await handle_publish_callback(update, context, data):
                return

            # 1. Menú Principal
            if data in ("main_menu", "volver_menu"):
                if not is_downloaded_msg and query.message:
                    try:
                        await query.message.delete()
                    except Exception:
                        pass
                await mostrar_menu_principal(update, context, force_new=True)

            # 2. Historial de Navegación Atrás
            elif data in ("nav_back", "volver"):
                if not is_downloaded_msg and query.message:
                    try:
                        await query.message.delete()
                    except Exception:
                        pass

                historial = st.get("historial", [])
                if historial:
                    prev_state = historial.pop()
                    view_type = prev_state[0]
                    if view_type == "series_list":
                        _, orig_t, f_val, pg = prev_state
                        await mostrar_series(
                            update,
                            context,
                            origin_type=orig_t,
                            filter_val=f_val,
                            page=pg or 1,
                            force_new=True,
                        )
                    elif view_type == "genres":
                        await mostrar_generos(update, context, force_new=True)
                    elif view_type == "authors":
                        pg = prev_state[1] if len(prev_state) > 1 else 1
                        await mostrar_autores_local(
                            update, context, page=pg, force_new=True
                        )
                    elif view_type == "main":
                        await mostrar_menu_principal(update, context, force_new=True)
                    else:
                        await mostrar_series(
                            update,
                            context,
                            origin_type="all_series",
                            page=1,
                            force_new=True,
                        )
                else:
                    await mostrar_series(
                        update,
                        context,
                        origin_type="all_series",
                        page=1,
                        force_new=True,
                    )

            # 3. Categorías de Navegación
            elif data.startswith("nav_local|"):
                if not is_downloaded_msg and query.message:
                    try:
                        await query.message.delete()
                    except Exception:
                        pass
                category = data.split("|")[1]
                if category == "all_series":
                    await mostrar_series(
                        update,
                        context,
                        origin_type="all_series",
                        page=1,
                        force_new=True,
                    )
                elif category == "newest":
                    await mostrar_series(
                        update,
                        context,
                        origin_type="newest",
                        page=1,
                        force_new=True,
                    )
                elif category == "genres":
                    await mostrar_generos(update, context, force_new=True)
                elif category == "authors":
                    await mostrar_autores_local(
                        update, context, page=1, force_new=True
                    )
                elif category in ("help", "ayuda"):
                    await mostrar_ayuda(update, context, force_new=True)
                elif category in ("donations", "donar", "vip"):
                    await mostrar_donaciones(update, context, force_new=True)
                elif category in ("rules", "reglas"):
                    await mostrar_reglas(update, context, force_new=True)

            # 4. Filtro por Género
            elif data.startswith("gen|"):
                genre_name = data.split("|")[1]
                await mostrar_series(
                    update, context, origin_type="genre", filter_val=genre_name, page=1
                )

            # 5. Filtro por Autor
            elif data.startswith("aut|"):
                author_name = data.split("|")[1]
                await mostrar_series(
                    update,
                    context,
                    origin_type="author",
                    filter_val=author_name,
                    page=1,
                )

            # 6. Paginador de Series
            elif data.startswith("nav_p|"):
                parts = data.split("|")
                origin_type = parts[1]
                filter_val = parts[2] if parts[2] else None
                page = int(parts[3])
                await mostrar_series(
                    update,
                    context,
                    origin_type=origin_type,
                    filter_val=filter_val,
                    page=page,
                )

            # 7. Selección de Serie / Colección
            elif data.startswith("col|"):
                series_idx = int(data.split("|")[1])
                series_hash = st.get("series_map", {}).get(series_idx)
                if series_hash:
                    await mostrar_volumenes_local(update, context, series_hash)
                else:
                    await query.answer("⚠️ Serie no encontrada.", show_alert=True)

            # 8. Selección de Libro Individual
            elif data.startswith("lib|"):
                key = data.split("|")[1]
                await mostrar_detalles_libro(update, context, key)

            # 9. Cambio de Volumen en Serie
            elif data.startswith("sel_vol|"):
                key = data.split("|")[1]
                await mostrar_detalles_libro(update, context, key, force_edit=True)

            # 10. Toggle de Sinopsis
            elif data.startswith("tog_syn|"):
                key = data.split("|")[1]
                is_expanded = st.get("synopsis_expanded", False)
                st["synopsis_expanded"] = not is_expanded
                await mostrar_detalles_libro(
                    update, context, key, force_edit=True, toggle_synopsis=True
                )

            # 11. Subir Nivel / Volver a Vista Previa
            elif data == "subir_nivel":
                prev_view = st.get("prev_view_local", "main")
                if prev_view == "genres":
                    await mostrar_generos(update, context)
                elif prev_view == "authors":
                    await mostrar_autores_local(
                        update, context, page=st.get("current_page_b", 1)
                    )
                else:
                    await mostrar_menu_principal(update, context)

            elif data == "volver_ultima":
                hist = st.get("historial", [])
                if hist:
                    last_view = hist.pop()
                    st["historial"] = hist
                    view_name = last_view[0]
                    if view_name == "series_list":
                        await mostrar_series(
                            update,
                            context,
                            origin_type=last_view[1],
                            filter_val=last_view[2],
                            page=last_view[3],
                        )
                    elif view_name == "volumes_local":
                        await mostrar_volumenes_local(update, context, last_view[1])
                    else:
                        await mostrar_menu_principal(update, context)
                else:
                    await mostrar_menu_principal(update, context)

            # 12. Búsqueda
            elif data in ("buscar", "search_init"):
                await pedir_termino_busqueda(update, context, force_new=False)

            else:
                logger.info(f"Callback no manejado: {data}")

        except Exception as e:
            logger.error(f"Error procesando callback: {e}", exc_info=True)
            await query.answer("❌ Error en la navegación del catálogo.", show_alert=True)
