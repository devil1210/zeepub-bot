from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from models.base import Base

T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    """
    Repositorio base con operaciones CRUD asíncronas estándar.
    """
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: Any) -> Optional[T]:
        """Obtiene un registro por su clave primaria."""
        return await self.session.get(self.model, id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Obtiene una lista de registros con paginación."""
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, **kwargs) -> T:
        """Crea un nuevo registro."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, id: Any, **kwargs) -> Optional[T]:
        """Actualiza un registro existente."""
        query = update(self.model).where(self.model.id == id).values(**kwargs).returning(self.model)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def delete(self, id: Any) -> bool:
        """Elimina un registro."""
        query = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.rowcount > 0

    async def save(self):
        """Confirma los cambios en la base de datos."""
        await self.session.commit()
