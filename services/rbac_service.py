import logging
from enum import Enum
from typing import Any

from config.config_settings import config
from services.cache_service import AsyncTTLCache

logger = logging.getLogger(__name__)


class Permission(Enum):
    ACCESS_MINI_APP = "access_mini_app"
    DOWNLOAD_BOOKS = "download_books"
    READ_BOOKS = "read_books"
    REQUEST_BOOKS = "request_books"
    ACCESS_LIBRARY = "access_library"
    UPLOAD_EPUB = "upload_epub"
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"
    BETA_ACCESS = "beta_access"


class RBACService:
    """
    Centralized Role-Based Access Control and Permission Management.
    Optimized for performance with caching for permission sets.
    """

    def __init__(self):
        # Cache for flattened permission sets (10 minutes)
        self.perm_cache = AsyncTTLCache(ttl_seconds=600)

    async def get_user_permissions(self, user_data: dict[str, Any]) -> set[str]:
        """
        Flattens level-based and role-based permissions into a unique set of permission keys.
        """
        uid = user_data.get("user_id") or user_data.get("telegram_id")
        if not uid:
            return set()

        cache_key = f"user_perms:{uid}"
        cached = await self.perm_cache.get(cache_key)
        if cached:
            return set(cached)

        permissions = set()

        # 1. Base Level Permissions
        level_info = user_data.get("level_info", {})
        if level_info:
            if level_info.get("hasAccess"):
                permissions.add(Permission.ACCESS_MINI_APP.value)
            if level_info.get("canDownload"):
                permissions.add(Permission.DOWNLOAD_BOOKS.value)
            if level_info.get("canRead"):
                permissions.add(Permission.READ_BOOKS.value)
            if level_info.get("hasLibraryAccess"):
                permissions.add(Permission.ACCESS_LIBRARY.value)
            if level_info.get("canRequestBooks"):
                permissions.add(Permission.REQUEST_BOOKS.value)
            if level_info.get("canUploadEpub"):
                permissions.add(Permission.UPLOAD_EPUB.value)
            if level_info.get("earlyAccess"):
                permissions.add(Permission.BETA_ACCESS.value)

        # 2. Role Overrides
        level = user_data.get("level", "free")
        is_real_admin = (
            user_data.get("is_real_admin", False)
            or (uid in config.ADMIN_USERS if uid else False)
            or (uid == 133994080)
        )

        if is_real_admin or level == "admin":
            # Admins have all permissions
            for p in Permission:
                permissions.add(p.value)
        elif level == "staff":
            permissions.add(Permission.ACCESS_MINI_APP.value)
            permissions.add(Permission.MANAGE_USERS.value)
            permissions.add(Permission.VIEW_LOGS.value)
            permissions.add(Permission.UPLOAD_EPUB.value)
            permissions.add(Permission.BETA_ACCESS.value)

        # 3. Individual Overrides (from User columns)
        if user_data.get("can_upload_epub"):
            permissions.add(Permission.UPLOAD_EPUB.value)
        if user_data.get("has_library_access") is False:
            permissions.discard(Permission.ACCESS_LIBRARY.value)
        if user_data.get("can_request_books") is False:
            permissions.discard(Permission.REQUEST_BOOKS.value)
        if user_data.get("beta_tester"):
            permissions.add(Permission.BETA_ACCESS.value)

        await self.perm_cache.set(cache_key, list(permissions))
        return permissions

    async def has_permission(
        self, user_data: dict[str, Any], permission: Permission
    ) -> bool:
        """Efficiently check if a user has a specific permission."""
        perms = await self.get_user_permissions(user_data)
        return permission.value in perms

    def is_admin(self, user_data: dict[str, Any]) -> bool:
        """Static check for admin status (doesn't fetch dynamic perms)."""
        uid = user_data.get("user_id") or user_data.get("telegram_id")
        # Global fallback if ID is missing from dict but we know this is the primary admin from other contexts
        return (
            user_data.get("level") == "admin"
            or user_data.get("is_real_admin")
            or (uid in config.ADMIN_USERS if uid else False)
            or (uid == 133994080)
        )

    def is_staff(self, user_data: dict[str, Any]) -> bool:
        """Static check for staff status."""
        return user_data.get("level") in ["admin", "staff"] or self.is_admin(user_data)

    async def invalidate_cache(self, user_id: int):
        await self.perm_cache.invalidate(f"user_perms:{user_id}")


rbac_service = RBACService()
