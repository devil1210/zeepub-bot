from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Interfaz base para repositorios asíncronos."""

    def __init__(self, db_manager, table_name: str):
        self.db_manager = db_manager
        self.table_name = table_name
        from core.supabase_manager import supabase_manager
        self.supabase = supabase_manager
    @abstractmethod
    async def get_by_id(self, id: Any) -> T | None:
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        pass

    @abstractmethod
    async def delete(self, id: Any) -> bool:
        pass
