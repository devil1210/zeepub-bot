# core/state_manager.py

from typing import Any


class StateManager:
    """Gestión de estado por usuario en memoria."""

    def __init__(self):
        self.user_state: dict[int, dict[str, Any]] = {}

    def get_user_state(self, uid: int) -> dict[str, Any]:
        if uid not in self.user_state:
            self.user_state[uid] = {
                "historial": [],
                "libros": {},
                "colecciones": {},
                "nav": {"prev": None, "next": None},
                "titulo": "📚 Todas las bibliotecas",
                "destino": None,
                "chat_origen": None,
                "message_thread_id": None,  # Para soporte de topics en grupos
                "esperando_destino_manual": False,
                "esperando_busqueda": False,
                "esperando_password": False,
                "ultima_pagina": None,
                "series_hash": None,
                "volume_id": None,
                "msg_que_hacer": None,
            }
        return self.user_state[uid]


    def register_book_key(self, key: str, book_data: dict[str, Any]) -> None:
        """Registra un libro en el mapa compartido para que cualquier usuario en un grupo pueda descargarlo."""
        if not hasattr(self, "_shared_books"):
            self._shared_books = {}
        self._shared_books[key] = book_data

    def get_book_by_key(self, key: str, uid: int | None = None) -> dict[str, Any] | None:
        """Busca un libro por su key en el estado del usuario, en el mapa compartido o en cualquier estado activo."""
        if uid and uid in self.user_state:
            st = self.user_state[uid]
            if "libros" in st and key in st["libros"]:
                return st["libros"][key]
        if hasattr(self, "_shared_books") and key in self._shared_books:
            return self._shared_books[key]
        for st in self.user_state.values():
            if "libros" in st and key in st["libros"]:
                return st["libros"][key]
        return None

    def register_series_key(self, key: str, series_hash: str) -> None:
        """Registra una serie en el mapa compartido para soporte multiusuario en grupos."""
        if not hasattr(self, "_shared_series"):
            self._shared_series = {}
        self._shared_series[key] = series_hash

    def get_series_by_key(self, key: str, uid: int | None = None) -> str | None:
        """Obtiene el hash de serie por key/índice en estado de usuario o compartido."""
        if uid and uid in self.user_state:
            st = self.user_state[uid]
            if "series_map" in st and key in st["series_map"]:
                return st["series_map"][key]
            if "colecciones" in st and key in st["colecciones"]:
                href = st["colecciones"][key].get("href", "")
                if href.startswith("local_series|"):
                    return href.replace("local_series|", "")
        if hasattr(self, "_shared_series") and key in self._shared_series:
            return self._shared_series[key]
        for st in self.user_state.values():
            if "series_map" in st and key in st["series_map"]:
                return st["series_map"][key]
            if "colecciones" in st and key in st["colecciones"]:
                href = st["colecciones"][key].get("href", "")
                if href.startswith("local_series|"):
                    return href.replace("local_series|", "")
        return None

    def clear_user_state(self, uid: int) -> None:
        if uid in self.user_state:
            del self.user_state[uid]


# Instancia global
state_manager = StateManager()

