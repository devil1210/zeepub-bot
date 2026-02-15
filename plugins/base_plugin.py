from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class BasePlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def initialize(self, bot_instance) -> bool:
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        pass

    def get_commands(self) -> dict[str, Callable]:
        return {}

    def get_callback_handlers(self) -> dict[str, Callable]:
        return {}

    def get_message_handlers(self) -> list[Callable]:
        return []

    async def on_download_request(
        self, user_id: int, epub_url: str, metadata: dict[str, Any]
    ) -> dict[str, Any] | None:
        return None

    async def on_download_complete(self, user_id: int, epub_url: str, success: bool) -> None:
        """Optional hook called when a download is completed."""
        return None
