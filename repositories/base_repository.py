from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Any

T = TypeVar("T")

class BaseRepository(ABC, Generic[T]):
    """Interfaz base para repositorios asíncronos."""
    
    @abstractmethod
    async def get_by_id(self, id: Any) -> Optional[T]:
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
