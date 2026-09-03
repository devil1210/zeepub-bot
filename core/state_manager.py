# core/state_manager.py

from typing import Any


class StateManager:
    """Gestión de estado por usuario en memoria con soporte multiusuario y pila de navegación."""

    def __init__(self):
        self.user_state: dict[int, dict[str, Any]] = {}
        self._shared_books: dict[str, dict[str, Any]] = {}
        self._shared_series: dict[str, str] = {}

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
                "current_series_hash": None,
                "volume_id": None,
                "vol_page": 1,
                "last_search_query": "",
                "msg_que_hacer": None,
            }
        return self.user_state[uid]

    def push_history(self, uid: int, entry: tuple) -> None:
        """Agrega un estado a la pila de navegación del usuario evitando duplicados inmediatos."""
        st = self.get_user_state(uid)
        hist = st.setdefault("historial", [])
        if not hist or hist[-1] != entry:
            hist.append(entry)

    def pop_history(self, uid: int) -> tuple | None:
        """Extrae el último estado de la pila de navegación."""
        st = self.get_user_state(uid)
        hist = st.get("historial", [])
        if hist and isinstance(hist, list):
            return hist.pop()
        return None

    def register_book_key(self, key: str, book_data: dict[str, Any]) -> None:
        """Registra un libro en el mapa compartido para que cualquier usuario en un grupo pueda descargarlo."""
        self._shared_books[key] = book_data

    def get_book_by_key(
        self, key: str, uid: int | None = None
    ) -> dict[str, Any] | None:
        """Busca un libro por su key en el estado del usuario, en el mapa compartido o en cualquier estado activo."""
        if uid and uid in self.user_state:
            st = self.user_state[uid]
            if "libros" in st and key in st["libros"]:
                return st["libros"][key]
        if key in self._shared_books:
            return self._shared_books[key]
        for st in self.user_state.values():
            if "libros" in st and key in st["libros"]:
                return st["libros"][key]
        return None

    def register_series_key(self, key: str, series_hash: str) -> None:
        """Registra una serie en el mapa compartido para soporte multiusuario en grupos."""
        self._shared_series[key] = series_hash

    def get_series_by_key(self, key: str, uid: int | None = None) -> str | None:
        """Obtiene el hash de serie por key/índice en estado de usuario o compartido."""
        str_key = str(key)
        int_key = int(str_key) if str_key.isdigit() else None

        if uid and uid in self.user_state:
            st = self.user_state[uid]
            if "series_map" in st:
                if str_key in st["series_map"]:
                    return st["series_map"][str_key]
                if int_key is not None and int_key in st["series_map"]:
                    return st["series_map"][int_key]
            if "colecciones" in st:
                col = st["colecciones"].get(str_key) or (
                    st["colecciones"].get(int_key) if int_key is not None else None
                )
                if col and isinstance(col, dict):
                    href = col.get("href", "")
                    if href.startswith("local_series|"):
                        return href.replace("local_series|", "")

        if str_key in self._shared_series:
            return self._shared_series[str_key]

        for st in self.user_state.values():
            if "series_map" in st:
                if str_key in st["series_map"]:
                    return st["series_map"][str_key]
                if int_key is not None and int_key in st["series_map"]:
                    return st["series_map"][int_key]
            if "colecciones" in st:
                col = st["colecciones"].get(str_key) or (
                    st["colecciones"].get(int_key) if int_key is not None else None
                )
                if col and isinstance(col, dict):
                    href = col.get("href", "")
                    if href.startswith("local_series|"):
                        return href.replace("local_series|", "")
        return None

    def clear_user_state(self, uid: int) -> None:
        if uid in self.user_state:
            del self.user_state[uid]


# Instancia global
state_manager = StateManager()
