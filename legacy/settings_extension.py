
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
        from services.user_service import user_service
        # Use user_service or repo to save
        await user_repo.update_user_settings(user_id, current_settings)
        return {"success": True, "settings": current_settings}
    except Exception as e:
        logger.error(f"Error updating user setting {key}: {e}")
        return {"success": False, "message": str(e)}
