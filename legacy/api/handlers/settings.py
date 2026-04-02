import json
import logging
import time
from typing import Any

from fastapi import HTTPException

from repositories.user_repository import user_repo
from services.settings_service import get_setting, set_setting

logger = logging.getLogger(__name__)


async def handle_ui_settings(data: dict[str, Any], user_data: dict[str, Any]):
    """Gestiona configuraciones de UI (globales, por nivel o personales)."""
    user_id = user_data.get("user_id")
    user_level = user_data.get("level", "free")
    sub_action = data.get("subAction", "get")

    if sub_action == "get":
        # We can mostly rely on user_data["settings"] which is pre-calculated by get_effective_user
        # but we also add the badge settings which are not in the main settings blob yet.

        final_settings = user_data.get("settings", {}).copy()

        # Add badge config (stored as separate settings)
        try:
            final_settings.update(
                {
                    "badgePosTop": int(get_setting("badge_pos_top", "8")),
                    "badgePosRight": int(get_setting("badge_pos_right", "8")),
                    "showPosTool": get_setting("show_pos_tool", "false").lower() == "true",
                    "badgePosMode": get_setting("badge_pos_mode", "relative"),
                    "uiScale": 1.0,
                    "avatarScale": 1.0,
                    "isDarkMode": True,
                    "showSearchCard": True,
                    "showSearchBar": False,
                    "showDonateCard": True,
                    "showHelpCard": True,
                    "dataSaver": False,
                }
            )
        except Exception as e:
            logger.error(f"Error loading UI base defaults: {e}")

        return final_settings

    elif sub_action == "set":
        target_role = data.get("role", "global")
        settings_obj = data.get("settings", {})

        if target_role == "personal":
            try:
                role_raw = get_setting(f"ui_defaults_{user_level}", "{}")
                role_data = json.loads(role_raw)
                settings_obj["last_seen_version"] = role_data.get("ui_version", 0)
            except Exception:
                settings_obj["last_seen_version"] = 0

            await user_repo.update_user_settings(user_id, settings_obj)

            # Bidirectional Sync Trigger (Local -> Cloud -> Local)
            from core.optimized_sync_engine import optimized_sync_engine

            await optimized_sync_engine.force_sync_all()

            return {
                "success": True,
                "message": "Configuración personal guardada y sincronizada con la nube",
            }
        else:
            if user_level not in ["admin", "staff"]:
                raise HTTPException(
                    status_code=403,
                    detail="Solo administradores pueden cambiar la configuración global",
                )

            settings_obj["ui_version"] = int(time.time())
            set_setting(f"ui_defaults_{target_role}", json.dumps(settings_obj))

            if data.get("forceOverwrite"):
                role_to_level = {
                    "admin": 1,
                    "staff": 2,
                    "premium": 3,
                    "vip": 4,
                    "white": 5,
                    "free": 6,
                }
                l_id = role_to_level.get(target_role)
                if l_id:
                    await user_repo.reset_level_users_settings(l_id)

            return {
                "success": True,
                "message": f"Configuración para {target_role} guardada (v{settings_obj['ui_version']})",
            }


async def handle_save_badge_config(data: dict[str, Any], user_data: dict[str, Any]):
    """Guarda la configuración global de los badges (solo Admin)."""
    user_level = user_data.get("level", "free")
    if user_level not in ["admin", "staff"]:
        raise HTTPException(
            status_code=403,
            detail="Solo administradores pueden guardar configuración global",
        )

    set_setting("badge_pos_top", str(data.get("badgeTop", 8)))
    set_setting("badge_pos_right", str(data.get("badgeRight", 8)))
    set_setting("show_pos_tool", str(data.get("showPosTool", False)))
    set_setting("badge_pos_mode", data.get("badgePosMode", "relative"))

    return {"success": True, "message": "Configuración de badge guardada correctamente"}


async def handle_update_user_setting(data: dict[str, Any], user_data: dict[str, Any]):
    """Actualiza una configuración específica del usuario."""
    key = data.get("key")
    value = data.get("value")

    if not key:
        return {"success": False, "message": "Key is required"}

    user_id = user_data.get("user_id")

    # Get current settings
    current_settings = user_data.get("settings") or {}
    if isinstance(current_settings, str):
        try:
            current_settings = json.loads(current_settings)
        except Exception:
            current_settings = {}

    current_settings[key] = value

    try:
        # Use user_service or repo to save
        await user_repo.update_user_settings(user_id, current_settings)
        return {"success": True, "settings": current_settings}
    except Exception as e:
        logger.error(f"Error updating user setting {key}: {e}")
        return {"success": False, "message": str(e)}
