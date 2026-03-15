from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import select

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    V4 Base Asynchronous Repository using SQLAlchemy 2.0.
    Implements standard CRUD operations.
    The `session` is injected from the outside (Service or Unit of Work level).
    """

    def __init__(self, model_cls: type[T], session=None, db_manager=None):
        self.model_cls = model_cls
        self.injected_session = session
        from core.db_manager_pg import pg_manager

        self.db_manager = db_manager or pg_manager

    def _get_session(self):
        """Internal helper to provide a session context."""

        if self.injected_session:
            # If a session was injected, we wrap it in a mock context manager
            # so the 'async with' syntax still works without opening a new session.
            class WrappedSession:
                def __init__(self, session):
                    self.session = session

                async def __aenter__(self):
                    return self.session

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

            return WrappedSession(self.injected_session)

        return self.db_manager.get_session()

    async def get_by_id(self, id: Any) -> T | None:
        async with self._get_session() as session:
            return await session.get(self.model_cls, id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[T]:
        async with self._get_session() as session:
            stmt = select(self.model_cls).offset(skip).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def create(self, entity: T) -> T:
        async with self._get_session() as session:
            session.add(entity)
            if not self.injected_session:
                await session.commit()
                await session.refresh(entity)
            return entity

    async def update(self, entity: T) -> T:
        async with self._get_session() as session:
            entity = await session.merge(entity)
            if not self.injected_session:
                await session.commit()
                await session.refresh(entity)
            return entity

    async def delete(self, id: Any) -> bool:
        async with self._get_session() as session:
            entity = await session.get(self.model_cls, id)
            if entity:
                await session.delete(entity)
                if not self.injected_session:
                    await session.commit()
                return True
            return False
