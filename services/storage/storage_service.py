import logging
import os
from abc import ABC, abstractmethod
from typing import BinaryIO

logger = logging.getLogger(__name__)


class StorageProvider(ABC):
    @abstractmethod
    async def get_file_content(self, path: str) -> bytes | None:
        pass

    @abstractmethod
    async def get_file_stream(self, path: str) -> BinaryIO | None:
        pass

    @abstractmethod
    async def save_file(self, path: str, content: bytes) -> bool:
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        pass


class LocalStorageProvider(StorageProvider):
    async def get_file_content(self, path: str) -> bytes | None:
        try:
            if not os.path.exists(path):
                return None
            with open(path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"LocalStorage error reading {path}: {e}")
            return None

    async def get_file_stream(self, path: str) -> BinaryIO | None:
        try:
            if not os.path.exists(path):
                return None
            return open(path, "rb")
        except Exception as e:
            logger.error(f"LocalStorage error opening stream {path}: {e}")
            return None

    async def save_file(self, path: str, content: bytes) -> bool:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"LocalStorage error saving {path}: {e}")
            return False

    async def exists(self, path: str) -> bool:
        return os.path.exists(path)


class StorageService:
    def __init__(self, provider: StorageProvider = None):
        self.provider = provider or LocalStorageProvider()

    async def get_content(self, path: str) -> bytes | None:
        return await self.provider.get_file_content(path)

    async def get_stream(self, path: str) -> BinaryIO | None:
        return await self.provider.get_file_stream(path)

    async def save(self, path: str, content: bytes) -> bool:
        return await self.provider.save_file(path, content)

    async def exists(self, path: str) -> bool:
        return await self.provider.exists(path)


storage_service = StorageService()
