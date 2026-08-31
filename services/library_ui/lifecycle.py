# services/library_ui/lifecycle.py
"""
Gestor de ciclo de vida para mensajes interactivos de la biblioteca en Telegram.
Controla la expiración de botones de navegación (10 minutos de inactividad)
y la auto-eliminación de mensajes en grupos (24 horas).
"""

import asyncio
import logging
from typing import Any

from services.rich_message_service import RichMessageService
from .book_builders import build_book_rich_blocks

logger = logging.getLogger(__name__)

# Almacén en memoria de tareas activas de expiración: (chat_id, message_id) -> asyncio.Task
_active_lifecycle_tasks: dict[tuple[int, int], asyncio.Task] = {}

# Set de mensajes con navegación expirada: (chat_id, message_id)
_nav_expired_msgs: set[tuple[int, int]] = set()


def is_nav_expired(chat_id: int, message_id: int | None) -> bool:
    """Verifica si los botones de navegación de un mensaje ya expiraron."""
    if not message_id:
        return False
    return (chat_id, message_id) in _nav_expired_msgs


def cancel_nav_timer(chat_id: int, message_id: int | None):
    """Cancela un timer de ciclo de vida existente si el mensaje se cerró o eliminó."""
    if not message_id:
        return
    key = (chat_id, message_id)
    task = _active_lifecycle_tasks.pop(key, None)
    if task and not task.done():
        task.cancel()
    _nav_expired_msgs.discard(key)


def schedule_message_lifecycle(
    chat_id: int,
    message_id: int | None,
    active_book: dict,
    active_key: str,
    volume_rows: list | None = None,
    files: dict | None = None,
    is_group: bool = False,
    bot_inst: Any = None,
    series_hash_short: str | None = None,
    timeout_seconds: int = 600,
):
    """
    Programa o refresca el temporizador de 10 minutos (600s) para retirar los botones
    de navegación por inactividad. Si el usuario interactúa nuevamente, el timer se reinicia.
    """
    if not message_id:
        return

    key = (chat_id, message_id)

    # Cancelar timer previo si el usuario interactuó (resetea los 10 minutos)
    prev_task = _active_lifecycle_tasks.pop(key, None)
    if prev_task and not prev_task.done():
        prev_task.cancel()

    _nav_expired_msgs.discard(key)

    async def _lifecycle_runner():
        try:
            # Fase 1: A los 10 minutos (timeout_seconds), retirar botones de navegación
            await asyncio.sleep(timeout_seconds)
            _nav_expired_msgs.add(key)

            clean_blocks = build_book_rich_blocks(
                active_book,
                has_cover=bool(files and "tomozaki_cover" in files),
                key=active_key,
                can_download=True,
                is_admin_or_staff=False,
                series_hash_short=series_hash_short,
                volume_buttons=volume_rows if volume_rows else None,
                show_nav_buttons=False,
            )

            try:
                res = await RichMessageService.edit_rich_message(
                    chat_id=chat_id,
                    message_id=message_id,
                    blocks=clean_blocks,
                    files=files if files else None,
                )
                if res and res.get("ok"):
                    logger.info(
                        f"[UI Lifecycle] Botones de navegación retirados por inactividad ({timeout_seconds}s) en chat {chat_id}, msg {message_id}"
                    )
                else:
                    logger.debug(
                        f"[UI Lifecycle] Resultado de edición al expirar msg {message_id}: {res}"
                    )
            except Exception as edit_err:
                logger.debug(
                    f"[UI Lifecycle] No se pudo editar mensaje {message_id} al expirar: {edit_err}"
                )

            # Fase 2: En grupos, auto-eliminar mensaje a las 24 horas (86400s totales)
            if is_group:
                remaining_time = max(1, 86400 - timeout_seconds)
                await asyncio.sleep(remaining_time)
                _nav_expired_msgs.discard(key)

                active_bot = bot_inst
                if not active_bot:
                    from api.main import bot as main_bot

                    active_bot = getattr(main_bot, "app", None) and main_bot.app.bot

                if active_bot:
                    try:
                        await active_bot.delete_message(
                            chat_id=chat_id, message_id=message_id
                        )
                        logger.info(
                            f"[UI Lifecycle] Mensaje {message_id} auto-eliminado tras 24h en chat {chat_id}"
                        )
                    except Exception as del_err:
                        logger.debug(
                            f"[UI Lifecycle] No se pudo auto-eliminar mensaje {message_id} tras 24h: {del_err}"
                        )

        except asyncio.CancelledError:
            # Timer cancelado por nueva interacción del usuario
            pass
        except Exception as err:
            logger.debug(f"[UI Lifecycle] Error en runner para msg {message_id}: {err}")
        finally:
            _active_lifecycle_tasks.pop(key, None)

    task = asyncio.create_task(_lifecycle_runner())
    _active_lifecycle_tasks[key] = task
