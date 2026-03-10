from typing import Any

from repositories.user_repository import UserLevelRepository, UserRepository

from .base_service import BaseService


class UserService(BaseService):
    """
    Business Logic for User identity, roles, and privileges.
    Connects to UserRepository without exposing SQLAlchemy components to Handlers.
    """

    async def get_or_register_user(
        self, telegram_id: int, username: str | None = None, name: str | None = None
    ) -> dict[str, Any]:
        """
        Retrieves user by ID, registering if they don't exist.
        """
        async with self.db.get_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)

            if not user:
                # Need the implicit default level, e.g., level_id=6
                level_repo = UserLevelRepository(session)
                default_lvl = await level_repo.get_by_name("free")

                # We need to construct from models
                from models.user_models import User

                user = User(
                    telegram_id=telegram_id, username=username, name=name, level_id=default_lvl.id if default_lvl else 6
                )
                user = await user_repo.create(user)

            return user.to_dict()

    async def extract_privileges(self, telegram_id: int) -> dict[str, Any]:
        """
        Calculates and returns standard access privileges for the user.
        """
        async with self.db.get_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)

            if not user:
                return {"can_download": False, "is_admin": False}

            lvl = user.level_info

            is_admin = user.role == "admin" or (lvl and lvl.name == "admin")

            return {
                "can_download": lvl.can_download if lvl else False,
                "is_admin": is_admin is True,
                "daily_limit": lvl.daily_downloads if lvl else 5,
            }
