import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.v4.base import BaseHandlerV4, with_services
from repositories.download_repository import DownloadRepository
from services.cover_service import send_doc_bytes
from services.rich_message_service import RichMessageService
from services.v4.ui_service import UIServiceV4

logger = logging.getLogger(__name__)


class CallbackHandlerV4(BaseHandlerV4):
    """
    Manejador centralizado de callbacks para la arquitectura v4.0.
    Coordina la navegación entre menús, catálogo y descargas.
    """

    @with_services
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **services):
        query = update.callback_query
        data = query.data

        library_service = services["library_service"]
        services["user_service"]

        # 1. Asegurar que el query sea respondido
        try:
            await query.answer()
        except Exception:
            pass

        # 2. Dispatcher de navegación
        try:
            if data == "main_menu":
                text, markup = await UIServiceV4.render_main_menu()
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data.startswith("catalog|"):
                page = int(data.split("|")[1])
                series_list = await library_service.get_all_series(skip=page * 10, limit=10)
                text, markup = await UIServiceV4.render_series_list(series_list, page=page)
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data.startswith("sv|"):
                series_id = data.split("|")[1]
                series = await library_service.get_series_details(series_id)
                if not series:
                    await query.answer("⚠️ Serie no encontrada.", show_alert=True)
                    return
                # El series_id real puede ser más largo si se buscó por prefijo
                real_series_id = series.id
                books = await library_service.get_books_by_series(real_series_id)
                text, markup = await UIServiceV4.render_series_details(series, books)
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data.startswith("bv|"):
                book_id = data.split("|")[1]
                # Usar repositorio vía library_service si es posible, o búsqueda por prefijo
                book = (
                    await library_service.book_repo.get_by_id_prefix(book_id)
                    if len(book_id) < 64
                    else await library_service.book_repo.get_by_id(book_id)
                )

                if not book:
                    await query.answer("⚠️ Libro no encontrado.", show_alert=True)
                    return

                # Obtener detalles de la serie para la sinopsis
                series = await library_service.get_series_details(book.series_id) if book.series_id else None
                sinopsis = series.description if series and series.description else "No hay descripción disponible para esta obra."

                # Intentar enviar Rich Message (API 10.2)
                _, markup = await UIServiceV4.render_book_details(book)
                blocks = [
                    RichMessageService.create_section_heading(f"📕 {book.title}", level=2),
                    RichMessageService.create_table(
                        headers=["Atributo", "Detalle"],
                        rows=[
                            ["🏷️ Identificador", book.id[:8]],
                            ["👤 Autor", book.author or "Desconocido"],
                            ["🎨 Maquetador", book.layout_by or "No especificado"],
                            ["🌐 Traductor", book.translator or "No especificado"],
                        ]
                    ),
                    RichMessageService.create_details(
                        title="📖 Ver Sinopsis Completa",
                        blocks=[RichMessageService.create_paragraph(sinopsis)]
                    )
                ]

                res = await RichMessageService.edit_rich_message(
                    chat_id=update.effective_chat.id,
                    message_id=query.message.message_id,
                    blocks=blocks,
                    reply_markup=markup
                )

                # Fallback tradicional si la API de Telegram o el transporte fallan
                if not res or not res.get("ok"):
                    logger.warning("[Callbacks] Fallback a mensaje tradicional en bv|")
                    text, markup = await UIServiceV4.render_book_details(book)
                    await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data.startswith("bd|"):
                book_id = data.split("|")[1]
                user_id = update.effective_user.id

                # Obtener libro
                book = await library_service.book_repo.get_by_id_prefix(book_id)
                if not book:
                    await query.answer("⚠️ Libro no encontrado.", show_alert=True)
                    return

                await query.answer("⚡️ Iniciando descarga...", show_alert=False)

                # Obtener preferencia del usuario
                user_service = services["user_service"]
                user = await user_service.get_or_create_user(
                    telegram_id=user_id, username=update.effective_user.username, name=update.effective_user.full_name
                )
                preferencia_destino = user.extra_data.get("download_destination", "chat") if user.extra_data else "chat"

                # Registrar descarga
                download_repo = DownloadRepository(session=services["library_service"].session)
                await download_repo.add_download(
                    user_id=user_id, title=book.title, book_hash=book.id, series_hash=book.series_id
                )

                # Enviar archivo (flujo v3)
                caption = f"📕 <b>{book.title}</b>\n🏷️ Hash: <code>{book.id[:8]}</code>"
                
                dest_chat_id = update.effective_chat.id
                api_kwargs = None

                if preferencia_destino == "private":
                    dest_chat_id = user_id
                else:
                    if update.effective_chat and update.effective_chat.type in ("group", "supergroup"):
                        api_kwargs = {"receiver_user_id": user_id}

                try:
                    await send_doc_bytes(
                        context.bot,
                        dest_chat_id,
                        caption,
                        book.filepath,
                        filename=book.filename or f"{book.title}.epub",
                        parse_mode="HTML",
                        api_kwargs=api_kwargs,
                    )
                    # Notificar éxito
                    await query.answer("🚀 ¡Archivo enviado con éxito!", show_alert=False)

                    # Auditoría para Staff en el grupo si fue efímero (obtenido de PostgreSQL)
                    if api_kwargs:
                        from models.users import User
                        from sqlalchemy import select
                        
                        stmt = select(User.telegram_id).where(User.role.in_(["admin", "staff"]))
                        staff_ids = (await user_service.session.execute(stmt)).scalars().all()
                        
                        # Combinar con los admins configurados en .env como fallback
                        from config.config_settings import config
                        all_staff_ids = set(staff_ids)
                        if config.ADMIN_USERS:
                            all_staff_ids.update(config.ADMIN_USERS)
                        
                        for staff_id in all_staff_ids:
                            # Omitir notificar al propio usuario
                            if staff_id == user_id:
                                continue
                            try:
                                admin_kwargs = {"receiver_user_id": staff_id}
                                admin_text = f"👁‍🗨 [Auditoría] El usuario <b>{update.effective_user.full_name}</b> (<code>{user_id}</code>) descargó <b>{book.title}</b>."
                                await context.bot.send_message(
                                    chat_id=update.effective_chat.id,
                                    text=admin_text,
                                    parse_mode="HTML",
                                    api_kwargs=admin_kwargs
                                )
                            except Exception:
                                pass
                except Exception as e:
                    logger.warning(f"Error enviando descarga al destino {dest_chat_id}: {e}")
                    if preferencia_destino == "private":
                        await query.answer(
                            "⚠️ No pude enviarte el libro al privado. Inicia el bot en privado (/start) e inténtalo de nuevo.",
                            show_alert=True
                        )
                    else:
                        await query.answer("❌ Error al enviar el libro.", show_alert=True)

                # Notificar éxito
                await query.answer("🚀 ¡Archivo enviado con éxito!", show_alert=False)

            elif data == "user_status":
                user_service = services["user_service"]
                user_data = await user_service.get_effective_user(update.effective_user.id)
                text, markup = await UIServiceV4.render_user_status(user_data)
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data == "settings_menu":
                text, markup = await UIServiceV4.render_settings_menu()
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data == "web_access":
                from config.config_settings import config

                text, markup = await UIServiceV4.render_web_access(config.WEBAPP_URL)
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data == "search_init":
                text, markup = await UIServiceV4.render_search_init()
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data == "buscar":
                # Delegar al search_handler pidiendo el término (activará el estado)
                from handlers.v4.search import SearchHandlerV4

                search_h = SearchHandlerV4(self.app)
                await search_h.handle(update, context)

            elif data.startswith("destino|"):
                _, destino = data.split("|", 1)
                uid = update.effective_user.id
                st = self.get_user_state(uid)

                # Manejar destino
                if destino == "aqui":
                    st["destino"] = update.effective_chat.id
                elif destino == "otro":
                    st["esperando_destino_manual"] = True
                    await query.edit_message_text(
                        "✏️ <b>Escribe el @usuario o ID del chat destino:</b>", parse_mode="HTML"
                    )
                    return
                else:
                    st["destino"] = destino  # @canal_id

                await query.answer(f"✅ Destino establecido: {destino}")
                # Volver al menú principal tras configurar
                text, markup = await UIServiceV4.render_main_menu()
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data.startswith("set_dest|"):
                _, nuevo_destino = data.split("|")
                user_service = services["user_service"]
                uid = update.effective_user.id

                user = await user_service.get_or_create_user(
                    telegram_id=uid, username=update.effective_user.username, name=update.effective_user.full_name
                )

                if not isinstance(user.extra_data, dict):
                    user.extra_data = {}
                user.extra_data["download_destination"] = nuevo_destino

                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(user, "extra_data")
                await user_service.session.commit()

                dest_names = {
                    "chat": "Chat actual (Efímero en grupos)",
                    "private": "Mensaje Privado (DM)"
                }
                await query.answer(f"✅ Destino cambiado a: {dest_names.get(nuevo_destino)}", show_alert=True)

                # Actualizar el mensaje
                text = (
                    f"⚙️ <b>Destino de Descarga</b>\n\n"
                    f"Configura dónde deseas recibir tus novelas descargadas.\n\n"
                    f"📍 <b>Configuración actual:</b> <code>{dest_names.get(nuevo_destino)}</code>\n\n"
                    f"<i>Selecciona una opción a continuación para cambiarlo:</i>"
                )

                keyboard = [
                    [InlineKeyboardButton("📥 Chat actual", callback_data="set_dest|chat")],
                    [InlineKeyboardButton("💬 Mensaje Privado", callback_data="set_dest|private")],
                ]

                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

            elif data == "close_menu":
                await query.message.delete()

            else:
                logger.info(f"Callback no manejado en v4.0: {data}")
                # Podríamos delegar a handlers legacy aquí si es necesario

        except Exception as e:
            logger.error(f"Error procesando callback v4.0 {data}: {e}", exc_info=True)
            await query.answer("❌ Error en la navegación.", show_alert=True)
