"""
handlers/v4/base_handler.py
----------------------------
BaseHandlerV4: Contrato base para todos los handlers de la arquitectura V4.
- Inyecta los servicios V4 directamente (no singletons globales)
- Registra al usuario automáticamente en cada interacción
- Proporciona helpers de respuesta comunes
"""

import logging
from abc import ABC, abstractmethod

from telegram import Update
from telegram.ext import ContextTypes

from services.v4.library_service import LibraryService
from services.v4.user_service import UserService

logger = logging.getLogger(__name__)


class BaseHandlerV4(ABC):
    """
    Contrato base para handlers V4.
    Los servicios son inyectados al instanciar el handler,
    siguiendo el patrón Handler -> Service -> Repository.
    """

    def __init__(
        self,
        user_service: UserService | None = None,
        library_service: LibraryService | None = None,
    ):
        self.user_svc = user_service or UserService()
        self.library_svc = library_service or LibraryService()
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Procesa el comando/evento específico."""

    # ------------------------------------------------------------------ #
    #  Helpers de respuesta                                                #
    # ------------------------------------------------------------------ #

    async def reply(
        self,
        update: Update,
        text: str,
        parse_mode: str = "HTML",
        reply_markup=None,
        thread_id: int | None = None,
    ) -> None:
        """Envía respuesta con soporte de topics/threads y markup."""
        await update.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            message_thread_id=thread_id,
        )

    # ------------------------------------------------------------------ #
    #  Auto-registro de usuarios                                           #
    # ------------------------------------------------------------------ #

    async def ensure_user(self, update: Update) -> dict:
        """
        Garantiza que el usuario exista en la BD.
        Retorna el dict de usuario para uso inmediato en el handler.
        """
        tg_user = update.effective_user
        if not tg_user:
            return {}
        try:
            return await self.user_svc.get_or_register_user(
                telegram_id=tg_user.id,
                username=tg_user.username,
                name=tg_user.full_name,
            )
        except Exception as e:
            self.logger.error(f"[ensure_user] Error registrando {tg_user.id}: {e}")
            return {}

    # ------------------------------------------------------------------ #
    #  Helpers de validación de acceso V4                                  #
    # ------------------------------------------------------------------ #

    async def get_privileges(self, telegram_id: int) -> dict:
        """Devuelve los privilegios del usuario del servicio V4."""
        try:
            return await self.user_svc.extract_privileges(telegram_id)
        except Exception as e:
            self.logger.error(f"[get_privileges] Error: {e}")
            return {"is_admin": False, "can_download": False, "daily_limit": 0}
