from sqlalchemy import select

from models.users import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session):
        super().__init__(User, session)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Busca un usuario por su ID de Telegram con sus relaciones cargadas."""
        from sqlalchemy.orm import joinedload

        query = (
            select(User)
            .where(User.telegram_id == telegram_id)
            .options(joinedload(User.level), joinedload(User.ui_settings))
        )
        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()
