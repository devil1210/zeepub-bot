from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_models import User, UserLevel

from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    CRUD for Users.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Returns a user by their Telegram ID."""
        return await self.get_by_id(telegram_id)


class UserLevelRepository(BaseRepository[UserLevel]):
    """
    CRUD for User Levels.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(UserLevel, session)

    async def get_by_name(self, name: str) -> UserLevel | None:
        """Returns a level by its name (e.g., 'free', 'premium')."""
        stmt = select(UserLevel).where(UserLevel.name == name.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
