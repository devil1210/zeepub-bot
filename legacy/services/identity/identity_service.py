import logging
from typing import Any

from services.rbac_service import Permission, rbac_service
from services.user_service import get_effective_user as get_eff_user

logger = logging.getLogger(__name__)


class IdentityService:
    """
    Centralized service for Identity, Authentication and Authorization.
    Wraps existing User and RBAC services into a unified interface.
    """

    async def get_user_profile(self, user_id: int, **kwargs) -> dict[str, Any]:
        """
        Returns full effective user profile including level, role and settings.
        """
        return await get_eff_user(user_id, **kwargs)

    async def check_admin(self, user_id: int):
        user_data = await self.get_user_profile(user_id)
        if not self.is_admin(user_data):
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Admin permissions required")

    async def check_staff(self, user_id: int):
        user_data = await self.get_user_profile(user_id)
        if not self.is_staff(user_data):
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Staff permissions required")

    async def has_permission(self, user_id_or_data: Any, permission: str) -> bool:
        """
        Checks if a user has a specific permission.
        Accepts either user_id (int) or user_data (dict).
        """
        if isinstance(user_id_or_data, int):
            user_data = await self.get_user_profile(user_id_or_data)
        else:
            user_data = user_id_or_data

        # Convert string to Permission enum if possible
        try:
            p_enum = Permission(permission)
            return await rbac_service.has_permission(user_data, p_enum)
        except ValueError:
            # Fallback for dynamic/custom permissions
            perms = await rbac_service.get_user_permissions(user_data)
            return permission in perms

    def is_admin(self, user_data: dict[str, Any]) -> bool:
        return rbac_service.is_admin(user_data)

    def is_staff(self, user_data: dict[str, Any]) -> bool:
        return rbac_service.is_staff(user_data)

    async def get_permissions(self, user_id: int) -> set[str]:
        user_data = await self.get_user_profile(user_id)
        return await rbac_service.get_user_permissions(user_data)


identity_service = IdentityService()
