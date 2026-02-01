# core/session_manager.py

import asyncio
import logging

import aiohttp


class SessionManager:
    """Gestión única de la sesión HTTP y locks por usuario."""

    def __init__(self):
        self._session = None
        self._locks = {}  # Inicializar diccionario de locks
        self.logger = logging.getLogger(__name__)

    def get_session(self) -> aiohttp.ClientSession:
        """Devuelve un único ClientSession, creándolo si es necesario."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=None)
            )
            self.logger.debug("Sesión HTTP creada.")
        return self._session

    def get_publish_lock(self, uid: int) -> asyncio.Lock:
        """
        Obtiene un lock asyncio por usuario (idempotente).
        Permite serializar descargas/publicaciones por usuario.
        """
        if uid not in self._locks:
            self._locks[uid] = asyncio.Lock()
        return self._locks[uid]

    async def close(self):
        """Cierra la sesión HTTP si existe."""
        if self._session:
            self.logger.debug("Cerrando sesión HTTP.")
            await self._session.close()
            self._session = None


# Instancia global
session_manager = SessionManager()
