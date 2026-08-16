from typing import Any


class PublisherProvider:
    """Clase base para proveedores de publicación (Telegram, Facebook, Twitter, etc)."""

    async def announce_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        raise NotImplementedError
