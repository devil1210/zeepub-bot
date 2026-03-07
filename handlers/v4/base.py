import logging
from abc import ABC, abstractmethod
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from core.database import async_session
from core.state_manager import state_manager
from services.library_service import LibraryService
from services.publisher_service import PublisherService
from services.user_service import UserService

logger = logging.getLogger(__name__)


def with_services(func):
    """
    Decorador para inyectar servicios asíncronos y manejar sesiones de base de datos.
    """

    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        async with async_session() as session:
            # Inicializar servicios con la sesión compartida
            services = {
                "user_service": UserService(session),
                "library_service": LibraryService(session),
                "publisher_service": PublisherService(session),
            }
            try:
                # Llamar al handler con los servicios inyectados
                result = await func(self, update, context, **services)
                # Commit automático si no hay excepciones
                await session.commit()
                return result
            except Exception as e:
                # Rollback en caso de error
                await session.rollback()
                logger.error(f"Error en handler {func.__name__}: {e}", exc_info=True)

                # Feedback al usuario
                error_text = "❌ <b>Error Interno:</b> Ha ocurrido un problema al procesar tu solicitud."
                if update.callback_query:
                    await update.callback_query.answer(text="Error interno del servidor.", show_alert=True)
                else:
                    await update.effective_message.reply_html(error_text)
                return None

    return wrapper


class BaseHandlerV4(ABC):
    """
    Clase base para todos los handlers v4.0.
    Proporciona acceso al estado y utilidades comunes.
    """

    def __init__(self, app):
        self.app = app

    @abstractmethod
    @with_services
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **services):
        """Método abstracto que debe ser implementado por cada comando."""
        pass

    def get_user_state(self, uid: int):
        """Obtiene el estado en memoria para un usuario."""
        return state_manager.get_user_state(uid)

    async def send_glass_message(self, update: Update, text: str, reply_markup=None):
        """Envía un mensaje formateado (placeholder para lógica estética futura)."""
        return await update.effective_message.reply_html(text=text, reply_markup=reply_markup)
