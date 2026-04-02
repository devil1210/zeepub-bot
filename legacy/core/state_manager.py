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


# Instancia global
state_manager = StateManager()
