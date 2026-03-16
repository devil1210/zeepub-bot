from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utils.logger import log_execution

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    V4 Base Asynchronous Repository using SQLAlchemy 2.0.
    Implements standard CRUD operations with AsyncSession.
    """

    def __init__(self, model: type[T], session: AsyncSession):
        """
        Inyecta el modelo y la sesión asíncrona.
        La sesión debe gestionarse externamente (Unit of Work o Service).
        """
        self.model = model
        self.session = session

    async def get_by_id(self, id_val: Any) -> T | None:
        """Obtiene una entidad por su ID primario."""
        return await self.session.get(self.model, id_val)

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[T]:
        """Obtiene todas las entidades con paginación."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    @log_execution
    async def create(self, entity: T) -> T:
        """Persiste una nueva entidad."""
        self.session.add(entity)
        return entity

    @log_execution
    async def update(self, entity: T) -> T:
        """Fusiona cambios en una entidad existente."""
        return await self.session.merge(entity)

    @log_execution
    async def delete(self, id_val: Any) -> bool:
        """Elimina una entidad por su ID."""
        entity = await self.get_by_id(id_val)
        if entity:
            await self.session.delete(entity)
            return True
        return False

    async def list_by_filters(self, **filters) -> Sequence[T]:
        """Busca entidades basadas en filtros dinámicos."""
        stmt = select(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalars().all()
