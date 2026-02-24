import json
import logging
from typing import Any

from fastapi import HTTPException

from api.handlers.helpers import check_staff
from core.supabase_manager import supabase_manager
from repositories.user_repository import user_repo
from services.settings_service import get_setting, set_setting
from services.tier_service import tier_service

logger = logging.getLogger(__name__)

async def handle_admin_get_tiers(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene todos los niveles y su configuración."""
    check_staff(user_data)
    levels = await tier_service.get_all_tiers()
    logger.info(f"ADMIN: handle_admin_get_tiers found {len(levels)} levels")
    return {"success": True, "levels": levels, "tiers": levels}

async def handle_admin_save_tier(data: dict[str, Any], user_data: dict[str, Any]):
    """Guarda cambios en un nivel."""
    check_staff(user_data)
    level_id = data.get("id")
    if not level_id:
        raise HTTPException(status_code=400, detail="Falta level_id")
    await tier_service.update_tier(int(level_id), data)
    return {"success": True}

async def handle_admin_get_tier_config(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene la configuración completa de un nivel/tier."""
    check_staff(user_data)
    tier_name = data.get("name")
    tier_id = data.get("id")

    # Check Global
    is_global = False
    if tier_id and str(tier_id).lower() == "global":
        is_global = True
    elif tier_name and "global" in str(tier_name).lower():
        is_global = True

    if is_global:
        global_raw = get_setting("ui_defaults_global", "{}")
        g = json.loads(global_raw)
        global_config = {
            "id": "global", "name": "Global", "icon": "globe", "color": "#ffffff",
            "dailyDownloads": -1, "maxConcurrent": 10, "priorityRequests": True,
            "earlyAccess": True, "customThemes": True,
            "primaryColor": g.get("primaryColor", "#2b6cee"),
            "glassOpacity": g.get("glassOpacity", 0.6),
            "theme": g.get("theme", "dark"),
            "fontSize": g.get("fontSize", 14),
            "glassBlur": g.get("glassBlur", 12),
            "coverWidth": g.get("coverWidth", 120),
            "navOpacity": g.get("navOpacity", 0.8),
            "accentOpacity": g.get("accentOpacity", 0.2),
            "showRecommendations": g.get("showRecommendations", True),
            "canDownload": g.get("canDownload", True),
            "canRead": g.get("canRead", True),
            "canUploadEpub": g.get("canUploadEpub", False),
            "forceSettings": g.get("forceSettings", False),
            "cardGlowIntensity": g.get("cardGlowIntensity", 0.5),
            "backgroundColor": g.get("backgroundColor", "#0f172a"),
            "cardColor": g.get("cardColor", "#1e293b"),
            "bannerContentOffset": g.get("bannerContentOffset", 0),
            "allowThemeTemplates": g.get("allowThemeTemplates", False),
        }
        return {"success": True, "config": global_config, "tier": global_config}

    tier = None
    if tier_id:
        tier = await user_repo.get_level_by_id(int(tier_id))
    elif tier_name and str(tier_name).isdigit():
        tier = await user_repo.get_level_by_id(int(tier_name))
    elif tier_name:
        all_lvls = await user_repo.get_all_levels()
        tier = next((lvl for lvl in all_lvls if lvl["name"].lower() == tier_name.lower()), None)

    if not tier:
        raise HTTPException(status_code=404, detail="Tier not found")

    return {"success": True, "config": tier, "tier": tier}

async def handle_admin_save_tier_config(data: dict[str, Any], user_data: dict[str, Any]):
    """Guarda la configuración completa de un nivel/tier."""
    check_staff(user_data)
    tier_name = data.get("name")
    level_id = data.get("level_id") or data.get("id")

    is_global = level_id == "global" or tier_name == "Global" or (tier_name and "Global" in str(tier_name))

    if is_global:
        ui_settings = {}
        field_mapping = {
            "primaryColor": "primaryColor", "glassOpacity": "glassOpacity",
            "navOpacity": "navOpacity", "glassBlur": "glassBlur", "coverWidth": "coverWidth",
            "showRecommendations": "showRecommendations", "theme": "theme",
            "fontSize": "fontSize", "accentOpacity": "accentOpacity",
            "canDownload": "canDownload", "canRead": "canRead",
            "hasLibraryAccess": "hasLibraryAccess", "canRequestBooks": "canRequestBooks",
            "bannerContentOffset": "bannerContentOffset", "backgroundColor": "backgroundColor",
            "cardColor": "cardColor", "forceSettings": "forceSettings",
            "cardGlowIntensity": "cardGlowIntensity", "allowThemeTemplates": "allowThemeTemplates",
        }
        for frontend_key, setting_key in field_mapping.items():
            if frontend_key in data:
                val = data[frontend_key]
                if frontend_key in ("glassOpacity", "navOpacity", "accentOpacity"):
                    if isinstance(val, int | float) and val > 1:
                        val = val / 100.0
                ui_settings[setting_key] = val
        if "name" in data:
            ui_settings["name"] = data["name"]

        current_global = json.loads(get_setting("ui_defaults_global", "{}"))
        current_global.update(ui_settings)
        set_setting("ui_defaults_global", json.dumps(current_global))
        return {"success": True, "tierId": "global"}

    # Not global
    client = supabase_manager.get_client()
    tier_id = None
    if level_id and str(level_id).isdigit():
        tier_id = int(level_id)
    else:
        result = client.table("user_levels").select("id").ilike("name", tier_name).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Tier '{tier_name}' no encontrado")
        tier_id = result.data[0]["id"]

    update_data = {}
    field_mapping = {
        "name": "name", "icon": "icon", "color": "color",
        "dailyDownloads": "daily_downloads", "maxConcurrent": "max_concurrent",
        "priorityRequests": "priority_requests", "earlyAccess": "early_access",
        "customThemes": "custom_themes", "primaryColor": "ui_primary_color",
        "glassOpacity": "panel_transparency", "theme": "ui_theme", "fontSize": "ui_font_size",
        "glassBlur": "ui_glass_blur", "coverWidth": "ui_cover_width",
        "navOpacity": "ui_nav_opacity", "accentOpacity": "ui_accent_opacity",
        "showRecommendations": "show_recommendations", "canDownload": "can_download",
        "canRead": "can_read", "canUploadEpub": "can_upload_epub",
        "hasLibraryAccess": "has_library_access", "canRequestBooks": "can_request_books",
        "bannerContentOffset": "banner_content_offset", "backgroundColor": "background_color",
        "cardColor": "card_color", "forceSettings": "force_settings",
        "cardGlowIntensity": "ui_glow_intensity", "ui_exported_settings": "ui_exported_settings",
        "allowThemeTemplates": "allow_theme_templates", "defaultThemeId": "default_theme_id",
    }
    for frontend_key, db_key in field_mapping.items():
        if frontend_key in data and data[frontend_key] is not None:
            val = data[frontend_key]
            if db_key == "panel_transparency":
                try:
                    val = int(float(val) * 100)
                except Exception:
                    val = 70
            update_data[db_key] = val

    try:
        client.table("user_levels").update(update_data).eq("id", tier_id).execute()
    except Exception as e:
        logger.warning(f"Supabase update error: {e}. Attempting local only update.")

    await tier_service.update_tier(tier_id, data)
    from core.optimized_sync_engine import optimized_sync_engine
    await optimized_sync_engine.force_sync_all()

    return {"success": True, "tierId": tier_id}
