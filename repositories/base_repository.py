import contextlib
import logging
from collections.abc import AsyncIterator, Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utils.logger import log_execution

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    V4 Base Asynchronous Repository using SQLAlchemy 2.0.
    Implements standard CRUD operations with AsyncSession.
    """

    def __init__(self, model: type[T], session: AsyncSession | None = None, db_manager: Any | None = None):
        """
        Inyecta el modelo y la sesión asíncrona o el gestor de DB.
        """
        self.model = model
        self.injected_session = session
        self.db_manager = db_manager

    @contextlib.asynccontextmanager
    async def _get_session(self) -> AsyncIterator[AsyncSession]:
        """
        Helper para obtener una sesión. Si hay una sesión inyectada, se usa.
        Si hay un db_manager, se crea una nueva sesión y se cierra al finalizar.
        """
        if self.injected_session:
            yield self.injected_session
        elif self.db_manager:
            async with self.db_manager.get_session() as session:
                yield session
        else:
            raise RuntimeError(f"Repositorio {self.__class__.__name__} sin sesión ni db_manager.")

    async def get_by_id(self, id_val: Any) -> T | None:
        """Obtiene una entidad por su ID primario."""
        async with self._get_session() as session:
            return await session.get(self.model, id_val)

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[T]:
        """Obtiene todas las entidades con paginación."""
        async with self._get_session() as session:
            stmt = select(self.model).offset(skip).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()

    @log_execution
    async def create(self, entity: T) -> T:
        """Persiste una nueva entidad."""
        async with self._get_session() as session:
            session.add(entity)
            if not self.injected_session:
                await session.commit()
                await session.refresh(entity)
            return entity

    @log_execution
    async def update(self, entity: T) -> T:
        """Fusiona cambios en una entidad existente."""
        async with self._get_session() as session:
            merged = await session.merge(entity)
            if not self.injected_session:
                await session.commit()
            return merged

    @log_execution
    async def delete(self, id_val: Any) -> bool:
        """Elimina una entidad por su ID."""
        async with self._get_session() as session:
            entity = await session.get(self.model, id_val)
            if entity:
                await session.delete(entity)
                if not self.injected_session:
                    await session.commit()
                return True
        return False

    async def list_by_filters(self, **filters) -> Sequence[T]:
        """Busca entidades basadas en filtros dinámicos."""
        async with self._get_session() as session:
            stmt = select(self.model).filter_by(**filters)
            result = await session.execute(stmt)
            return result.scalars().all()
