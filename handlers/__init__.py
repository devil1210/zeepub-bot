"""
handlers/__init__.py
---------------------
Lazy exports para V3. Los imports se ejecutan solo cuando se accede al nombre,
evitando que inicializar handlers.v4.* cargue la cadena V3 innecesariamente.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .callback_handlers import buscar_epub, button_handler, set_destino
    from .command_handlers import CommandHandlers
    from .message_handlers import recibir_texto


def __getattr__(name: str):
    """Import bajo demanda para no arrastrar dependencias V3 al cargar subpaquetes V4."""
    if name in ("CommandHandlers",):
        from .command_handlers import CommandHandlers  # noqa: PLC0415

        return CommandHandlers
    if name in ("set_destino", "buscar_epub", "button_handler"):
        return locals()[name]
    if name == "recibir_texto":
        from .message_handlers import recibir_texto  # noqa: PLC0415

        return recibir_texto
    raise AttributeError(f"module 'handlers' has no attribute {name!r}")


__all__ = [
    "CommandHandlers",
    "set_destino",
    "buscar_epub",
    "button_handler",
    "recibir_texto",
]
