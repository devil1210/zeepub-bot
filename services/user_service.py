import logging
import json
import os
import io
from typing import Optional, Dict, Any
from datetime import datetime
from PIL import Image
from config.config_settings import config
from repositories.user_repository import user_repo
from services.cache_service import AsyncTTLCache
from services.settings_service import get_setting
from utils.library_db import PROFILES_DIR, THUMBNAILS_DIR

logger = logging.getLogger(__name__)

# Cache for user info (5 minutes)
user_cache = AsyncTTLCache(ttl_seconds=300)


async def upsert_user(
    telegram_id: int,
    level: str,
    duration_months: Optional[int] = None,
    role: Optional[str] = None,
    created_by: Optional[int] = None,
    duration_days: Optional[int] = None,
    nickname: Optional[str] = None,
    name: Optional[str] = None,
    username: Optional[str] = None,
    roles: Optional[list] = None,
    level_id: Optional[int] = None,
):
    """
    Agrega o actualiza un usuario.
    Si duration_months/days es None y no existe, es 'infinito'.
    """
    expires_at = None
    from datetime import timedelta

    now = datetime.now()

    if duration_days is not None:
        expires_at = now + timedelta(days=duration_days)
    elif duration_months is not None:
        # Simple approximation: 30 days * months
        days = duration_months * 30
        expires_at = now + timedelta(days=days)

    await user_repo.upsert(
        telegram_id, level, expires_at, role, created_by, nickname, name, username, roles, level_id=level_id
    )
    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def remove_user(telegram_id: int):
    await user_repo.delete(telegram_id)
    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def update_user_status_label(telegram_id: int, new_role: Optional[str]) -> None:
    # Check if user exists first
    info = await get_user_info(telegram_id)
    if not info:
        # User not in DB, retrieve effective level (e.g. from config) and upsert
        eff = await get_effective_user(telegram_id)
        level = eff.get("level", "free")
        # Upsert with new role (functional label)
        await upsert_user(telegram_id, level=str(level), role=new_role)
    else:
        # Just update the role column (the functional role)
        await user_repo.update_status(telegram_id, new_role)

    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def update_user_nickname(telegram_id: int, new_nickname: Optional[str]) -> None:
    # Check if user exists first
    info = await get_user_info(telegram_id)
    if not info:
        # User not in DB, retrieve effective level and upsert
        eff = await get_effective_user(telegram_id)
        level = eff.get("level", "free")
        # Upsert with new nickname
        await upsert_user(telegram_id, level=str(level), nickname=new_nickname)
    else:
        await user_repo.update_nickname(telegram_id, new_nickname)

    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def get_user_info(telegram_id: int) -> Optional[Dict[str, Any]]:
    """
    Retorna info del usuario desde DB.
    """
    return await user_repo.get_by_id(telegram_id)


async def get_effective_user(
    uid: int, 
    use_cache: bool = True, 
    tg_user: Optional[Any] = None,
    simulated_level_id: Optional[int] = None
) -> Dict[str, Any]:

    """
    Determina el nivel efectivo del usuario y estado, considerando DB y Config (legacy).
    Retorna un dict con keys: level (tier), role (label), status_label, expires_at.
    Tiers (level): 'admin', 'staff', 'premium', 'vip', 'white', 'free'.
    """
    # 0. Check Cache (Bypass if simulating)
    cache_key = f"user_effective:{uid}"
    if use_cache and simulated_level_id is None:
        cached = await user_cache.get(cache_key)
        if cached:
            return cached


    # Extract nickname if tg_user provided
    nickname_from_tg = None
    if tg_user:
        if isinstance(tg_user, dict):
            # From API/WebApp
            first_name = tg_user.get("first_name", "")
            last_name = tg_user.get("last_name", "")
            nickname_from_tg = f"{first_name} {last_name}".strip() or tg_user.get("username")
        else:
            # From Bot (Telegram User object)
            nickname_from_tg = getattr(tg_user, 'full_name', getattr(tg_user, 'first_name', None))
        
        # Propagate name and username from tg_user if present
        name_from_tg = nickname_from_tg
        username_from_tg = getattr(tg_user, 'username', None) if not isinstance(tg_user, dict) else tg_user.get("username")

    # 0. Load Global UI Defaults
    global_raw = get_setting("ui_defaults_global", "{}")
    global_ui = json.loads(global_raw)
    
    # Robust Defaults if DB is empty
    if not global_ui:
        global_ui = {
            "theme": "dark",
            "primaryColor": "#3b82f6",
            "fontSize": 14,
            "navOpacity": 0.8,
            "accentOpacity": 0.2,
            "glassBlur": 12,
            "backgroundColor": "#0f172a",
            "cardColor": "#1e293b",
            "glassOpacity": 0.6,
            "cardGlowIntensity": 0.5
        }

    def normalize_ui(s: Dict[str, Any]):
        """Normaliza valores de opacidad y otros parámetros visuales."""
        opacity_keys = ["navOpacity", "accentOpacity", "glassOpacity"]
        for k in opacity_keys:
            if k in s and isinstance(s[k], (int, float)) and s[k] > 1.1:
                s[k] = s[k] / 100.0
        return s

    result = {
        "level": "free",
        "role": "", # Functional role (e.g. Publicador)
        "status_label": "Lector",
        "expires_at": None,
        "nickname": nickname_from_tg or f"User_{uid}",
        "name": nickname_from_tg or f"User_{uid}",
        "username": username_from_tg or "",
        "settings": normalize_ui(global_ui.copy())
    }

    # 1. Config Admins always have top precedence
    if uid in config.ADMIN_USERS:
        # AUTO-SYNC: Ensure config admins have level_id=1 in DB
        # This runs every time to ensure consistency
        try:
            # AUTO-SYNC: Ensure config admins have level_id=1 in DB
            await user_repo.upsert(uid, level="admin", level_id=1)
            logger.info(f"Auto-synced config admin {uid} to level_id=1 in database")
        except Exception as e:
            logger.warning(f"Could not auto-sync admin {uid} to DB: {e}")
        
        # Load DB info even for config admins to preserve personal settings
        info = await get_user_info(uid)
        
        # Merge personal settings on top of global defaults
        personal_settings = info.get("settings", {}) if info else {}
        base_settings = global_ui.copy()
        base_settings.update(personal_settings)
        
        result.update({
            "level": "admin",
            "role": info.get("role") if info else "",
            "status_label": "Admin",
            "expires_at": None,
            "nickname": info.get("nickname") if (info and info.get("nickname")) else (nickname_from_tg or f"Admin_{uid}"),
            "name": info.get("name") if (info and info.get("name")) else (nickname_from_tg or f"Admin_{uid}"),
            "username": info.get("username") if (info and info.get("username")) else (username_from_tg or ""),
            "roles": info.get("roles") if (info and info.get("roles")) else ["Administrador"],
            "has_mini_app_access": True,
            "can_request_books": info.get("can_request_books", True) if info else True,
            "has_library_access": info.get("has_library_access", True) if info else True,
            "can_upload_epub": info.get("can_upload_epub", False) if info else False,
            "settings": normalize_ui(base_settings),
            "level_info": { # Default level info for config admins if DB is missing it
                "id": "1", "name": "Administrador", "priority": 100, "color": "#FF6B6B", "hasAccess": True,
                "canDownload": True, "canRead": True, "customThemes": True, "forceSettings": False,
                "theme": "dark", "primaryColor": "#3b82f6", "fontSize": 14, "navOpacity": 0.8,
                "accentOpacity": 0.2, "glassOpacity": 0.6, "glassBlur": 12
            }
        })
        # Note: We DON'T return early here anymore to allow enrichment and simulation
    
    # 2. Check DB Info
    info: Optional[Dict[str, Any]] = await get_user_info(uid)
    if info and uid not in config.ADMIN_USERS: # Admins already handled result base above
        # Check expiration
        expires_at: Optional[datetime] = info.get("expires_at")
        if expires_at and expires_at < datetime.now():
            # Expired
            result.update({
                "level": "free",
                "status_label": "Expirado",
                "expires_at": expires_at,
                "has_mini_app_access": False,
            })
        else:
            level_db = info.get("level", "free")
            level_str = level_db.lower() if isinstance(level_db, str) else "free"
            
            # Merge personal settings on top of global defaults
            personal_settings = info.get("settings", {})
            final_settings = global_ui.copy()
            final_settings.update(personal_settings)

            result.update({
                "level": level_str,
                "role": info.get("role"),
                "status_label": info.get("role") or level_str.capitalize(),
                "expires_at": expires_at,
                "nickname": info.get("nickname") or result.get("nickname") or f"User_{uid}",
                "name": info.get("name") or result.get("name") or f"User_{uid}",
                "username": info.get("username") or result.get("username") or "",
                "roles": info.get("roles") or [],
                "can_request_books": info.get("can_request_books", True),
                "has_library_access": info.get("has_library_access", True),
                "can_upload_epub": info.get("can_upload_epub", False),
                "settings": normalize_ui(final_settings),
                "personal_settings_raw": info.get("settings", {}) # Store for simulation comparison
            })

    # 3. PROACTIVE SYNC: Create minimal user record if not exists
    if not info and uid not in config.ADMIN_USERS:
        logger.info(f"Auto-registering user {uid} (Lector level)")
        await user_repo.create_minimal_user(uid, name=name_from_tg, username=username_from_tg)

    # 4. Access Info (Levels & Permissions)
    access_info = await user_repo.get_access_info(uid)
    if access_info:
        result["has_mini_app_access"] = access_info["hasAccess"]
        result["is_admin_db"] = access_info["isAdmin"]
        result["level_info"] = access_info["level"]

        # Check if this is a hard admin FIRST
        is_hard_admin = access_info["isAdmin"] or uid in config.ADMIN_USERS
        result["is_real_admin"] = is_hard_admin
        
        if is_hard_admin:
            # For hard admins: ALWAYS force admin status, regardless of DB level_id
            result["has_mini_app_access"] = True
            result["level"] = "admin"
            result["status_label"] = "Admin"
        else:
            # Map Level ID to standardized role key (more stable than names)
            lvl_id_raw = access_info["level"].get("id")
            try:
                lvl_id = int(lvl_id_raw) if lvl_id_raw is not None else 6
            except (ValueError, TypeError):
                lvl_id = 6

            level_to_role = {
                1: "admin", 2: "staff", 3: "premium", 4: "vip", 5: "white", 6: "free"
            }
            
            if lvl_id in level_to_role:
                result["level"] = level_to_role[lvl_id]
            else:
                result["level"] = access_info["level"]["name"].lower().strip()

            if not info or not info.get("role"):
                result["status_label"] = access_info["level"]["name"]

        # --- Refined Personalized UI Logic ---
        level_settings = access_info["level"]
        
        # 1. Start with Global UI as base
        final_ui = normalize_ui(global_ui.copy())
        
        # 2. Overlay Level Defaults (if defined)
        override_keys = [
            "theme", "fontSize", "glassBlur", "coverWidth", "navOpacity", 
            "accentOpacity", "primaryColor", "showRecommendations",
            "backgroundColor", "cardColor", "cardGlowIntensity",
            "bannerContentOffset", "glassOpacity"
        ]
        for k in override_keys:
            if k in level_settings and level_settings[k] is not None:
                final_ui[k] = level_settings[k]
        
        # Normalize after level overlay
        final_ui = normalize_ui(final_ui)
        # SKIP PERSONAL OVERRIDES IF SIMULATING
        if simulated_level_id is None:
            personal_settings = info.get("settings", {}) if info else {}
            
            # Get exported settings list
            exported_raw = level_settings.get("ui_exported_settings")
            exported_list = []
            if exported_raw:
                try:
                    exported_list = json.loads(exported_raw) if isinstance(exported_raw, str) else exported_raw
                except:
                    exported_list = []
            
            is_forced = level_settings.get("forceSettings", False)
            
            for k, v in personal_settings.items():
                if not is_forced:
                    # Not forced: user settings always win
                    final_ui[k] = v
                else:
                    # Forced: only if specifically exported by admin
                    if k in exported_list:
                        final_ui[k] = v
        else:
            logger.debug(f"Simulation Mode: Skipping personal settings for user {uid}")
        
        # Final normalization
        final_ui = normalize_ui(final_ui)
        result["settings"] = final_ui

        # Overwrite identities if present
        if access_info.get("nickname"): result["nickname"] = access_info["nickname"]
        if access_info.get("name"): result["name"] = access_info["name"]
        if access_info.get("username"): result["username"] = access_info["username"]
        if access_info.get("roles"): result["roles"] = access_info["roles"]
        
        # Add exported UI settings list to result
        exported = level_settings.get("ui_exported_settings")
        if exported:
            try:
                if isinstance(exported, str):
                    result["ui_exported_settings"] = json.loads(exported)
                else:
                    result["ui_exported_settings"] = exported
            except:
                result["ui_exported_settings"] = []
        else:
            # Fallback for old/empty tiers
            result["ui_exported_settings"] = ["theme", "primaryColor", "fontSize"]

    # 5. Legacy Config Fallbacks (only if NOT found in DB/Access Info)
    elif uid in config.FACEBOOK_PUBLISHERS:
        result = {
            "level": "staff",
            "role": "Publicador",
            "status_label": "Publicador",
            "expires_at": None,
            "nickname": None,
            "has_mini_app_access": True,
        }

    elif uid in config.PREMIUM_LIST:
        result = {
            "level": "premium",
            "status_label": "Premium (Legacy)",
            "expires_at": None,
            "nickname": None,
            "has_mini_app_access": True,
        }

    elif uid in config.VIP_LIST:
        result = {
            "level": "vip",
            "status_label": "VIP (Legacy)",
            "expires_at": None,
            "nickname": None,
            "has_mini_app_access": True,
        }

    elif uid in config.WHITELIST:
        result = {
            "level": "white",
            "status_label": "Patrocinador (Legacy)",
            "expires_at": None,
            "nickname": None,
            "has_mini_app_access": True,
        }

    # 5. Admin Level Simulation
    # If the user IS an admin (Config or DB) and a simulated_level_id is provided,
    # we fetch that level's info and override the current result.
    is_real_admin = (uid in config.ADMIN_USERS) or result.get("is_admin_db", False)
    
    if is_real_admin and simulated_level_id is not None:
        logger.info(f"ADMIN SIMULATION: User {uid} simulating level {simulated_level_id}")
        sim_level = await user_repo.get_level_by_id(simulated_level_id)
        if sim_level:
            # Override essential access flags
            result["has_mini_app_access"] = sim_level.get("hasAccess", True)
            result["status_label"] = f"Simulando: {sim_level['name']}"
            result["level_info"] = sim_level
            
            # Fallback for simulated level role
            lvl_id_sim = sim_level.get("id")
            try:
                sid = int(lvl_id_sim) if lvl_id_sim is not None else 6
            except:
                sid = 6
                
            if sid in level_to_role:
                result["level"] = level_to_role[sid]
            else:
                result["level"] = sim_level["name"].lower().strip()
                
            # Simulación: Priorizamos los ajustes del nivel para "ver" la identidad del rango
            # En modo simulación, NO usamos ajustes personales. Solo Global + Level.
            
            # Merge settings from level
            level_settings_overlay = {
                "theme": sim_level.get("theme"),
                "fontSize": sim_level.get("fontSize"),
                "glassBlur": sim_level.get("glassBlur"),
                "coverWidth": sim_level.get("coverWidth"),
                "navOpacity": sim_level.get("navOpacity"),
                "accentOpacity": sim_level.get("accentOpacity"),
                "primaryColor": sim_level.get("primaryColor"),
                "showRecommendations": sim_level.get("showRecommendations"),
                "backgroundColor": sim_level.get("backgroundColor"),
                "cardColor": sim_level.get("cardColor"),
                "cardGlowIntensity": sim_level.get("cardGlowIntensity"),
                "panelTransparency": sim_level.get("glassOpacity") * 100 if sim_level.get("glassOpacity") else 60,
                "bannerContentOffset": sim_level.get("bannerContentOffset", 0),
            }
            # Remove None values
            level_settings_overlay = {k: v for k, v in level_settings_overlay.items() if v is not None}
            
            # Reset settings to Global UI base before applying level overrides
            final_sim_ui = global_ui.copy()
            final_sim_ui.update(level_settings_overlay)
            
            result["settings"] = final_sim_ui
            
            # Special flag to let frontend know it's a simulation
            result["is_simulated"] = True
            result["real_uid"] = uid
    
    result["is_real_admin"] = is_real_admin

    # Save to cache (only if not simulating)

    if simulated_level_id is None:
        await user_cache.set(cache_key, result)
    return result



async def get_users_by_level(level: str) -> list[Dict[str, Any]]:
    """
    Retorna lista de usuarios con un nivel específico desde la DB.
    """
    return await user_repo.get_by_level(level)


async def upgrade_user_level(telegram_id: int, new_level_name: str) -> None:
    """
    Actualiza el nivel de un usuario buscando por nombre de nivel.
    """
    async with user_repo.db.connection() as conn:
        await conn.execute(
            """
            UPDATE users
            SET level_id = (SELECT id FROM user_levels WHERE name = ?)
            WHERE telegram_id = ?
            """,
            (new_level_name, telegram_id),
        )
        await conn.commit()
    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def increment_download_count(telegram_id: int) -> int:
    """Incrementa el contador de descargas y retorna el nuevo total."""
    count = await user_repo.increment_download_count(telegram_id)
    return count


async def check_milestones(uid: int, context) -> Optional[str]:
    """Verifica si el usuario alcanzó un hito y retorna el mensaje de recompensa."""
    # This would ideally use templates from the custom_messages plugin
    user_info = await get_user_info(uid)
    if not user_info:
        return None

    count = user_info.get("total_downloads", 0)

    milestones = {
        10: "milestone_10_downloads",
        50: "milestone_50_downloads",
        100: "milestone_100_downloads",
    }

    if count in milestones:
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        slug = milestones[count]

        # Default messages if plugin not active or template not set
        defaults = {
            10: "🎁 ¡Felicidades! Has descargado tus primeros 10 libros. 🎉",
            50: "🌟 ¡Increíble! Ya llevas 50 libros descargados. Eres un lector apasionado. 📚",
            100: "👑 ¡Master Lector! 100 libros descargados. ¡Tu biblioteca es legendaria! 🏆",
        }

        if cms and cms.enabled:
            return await cms.get_text(
                slug, user=None
            )  # user will be handled by plugin if needed
        return defaults.get(count)

    return None


async def invalidate_user_cache(telegram_id: int):
    """Limpia la caché de un usuario específico."""
    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def get_user_settings(telegram_id: int) -> Dict[str, Any]:
    """Obtiene la configuración personal del usuario."""
    info = await get_user_info(telegram_id)
    if info:
        return info.get("settings", {})
    return {}


async def update_user_setting(telegram_id: int, key: str, value: Any) -> Dict[str, Any]:
    """Actualiza una clave específica de la configuración del usuario."""
    current_settings = await get_user_settings(telegram_id)
    current_settings[key] = value

    # Ensure user exists (if not, upsert first)
    info = await get_user_info(telegram_id)
    if not info:
        eff = await get_effective_user(telegram_id)
        await upsert_user(telegram_id, level=str(eff.get("level", "free")))

    await user_repo.update_user_settings(telegram_id, current_settings)
    await user_cache.invalidate(f"user_effective:{telegram_id}")
    return current_settings



# Init DB is handled by DatabaseManager/UserRepository instantiation
# We don't need init_user_db() explicit call here as repo handles connections lazily or via manager


async def sync_user_from_env(telegram_id: int, tg_user=None) -> Optional[Dict]:
    """
    Verifica si el usuario está en alguna lista del .env y
    sincroniza su rol/nivel en Supabase automáticamente.
    
    Prioridad:
    1. ADMIN_USERS -> admin
    2. FACEBOOK_PUBLISHERS -> staff + "Publicador"
    3. PREMIUM_LIST -> premium
    4. VIP_LIST -> vip
    5. WHITELIST -> white (Patrocinador)
    
    Returns:
        Dict con rol asignado o None si no cambió nada
    """
    # Determinar nivel según ENV
    target_level = None
    target_role = None
    
    if telegram_id in config.ADMIN_USERS:
        target_level = "admin"
    elif telegram_id in config.FACEBOOK_PUBLISHERS:
        target_level = "staff"
        target_role = "Publicador"
    elif telegram_id in config.PREMIUM_LIST:
        target_level = "premium"
    elif telegram_id in config.VIP_LIST:
        target_level = "vip"
    elif telegram_id in config.WHITELIST:
        target_level = "white"
    
    if not target_level:
        return None  # No está en ninguna lista del ENV
    
    # Obtener usuario actual
    current_user = await get_effective_user(telegram_id, tg_user=tg_user, use_cache=False)
    current_level = current_user.get("level", "free")
    current_role = current_user.get("role")
    
    # Verificar si necesita actualización
    needs_update = False
    if current_level != target_level:
        needs_update = True
        logger.info(f"Auto-syncing user {telegram_id} from ENV (Level): {current_level} -> {target_level}")
    elif target_role and current_role != target_role:
        needs_update = True
        logger.info(f"Updating functional role for user {telegram_id}: {current_role} -> {target_role}")
    
    if needs_update:
        # Actualizar en DB
        await upsert_user(
            telegram_id=telegram_id,
            level=target_level,
            role=target_role,
            duration_months=None,  # Permanente
        )
        
        # Invalidar cache y retornar usuario actualizado
        await user_cache.invalidate(f"user_effective:{telegram_id}")
        return await get_effective_user(telegram_id, tg_user=tg_user, use_cache=False)
    
    return current_user


async def sync_user_profile_photo(telegram_id: int, bot) -> Optional[str]:
    """
    Obtiene la foto de perfil del usuario desde Telegram y la guarda localmente.
    Retorna la URL relativa para acceder a la imagen.
    """
    try:
        # 1. Obtener fotos de perfil del usuario
        photos = await bot.get_user_profile_photos(telegram_id, limit=1)
        if not photos or not photos.photos:
            logger.info(f"Usuario {telegram_id} no tiene fotos de perfil públicas.")
            return None
        
        # 2. Obtener la versión más pequeña/mediana (index 0 de la primera foto)
        # photos.photos[0] es la lista de tamaños de la foto más reciente
        # Tomamos index 0 o 1 para que no sea gigante
        photo_size = photos.photos[0][-1] # La última suele ser la mejor calidad
        file = await bot.get_file(photo_size.file_id)
        
        # 3. Preparar ruta local
        filename = f"user_{telegram_id}.jpg"
        thumb_filename = f"user_{telegram_id}_thumb.jpg"
        local_path = os.path.join(PROFILES_DIR, filename)
        thumb_path = os.path.join(PROFILES_DIR, thumb_filename)
        
        # 4. Descargar a memoria primero para procesar
        photo_bytes = await file.download_as_bytearray()
        
        # 5. Guardar original y crear thumbnail
        with Image.open(io.BytesIO(photo_bytes)) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Guardar "grande" (pero optimizado)
            img.save(local_path, "JPEG", quality=85, optimize=True)
            
            # Crear thumbnail (120px)
            thumb_img = img.copy()
            thumb_img.thumbnail((120, 120), Image.LANCZOS)
            thumb_img.save(thumb_path, "JPEG", quality=75, optimize=True)
            
        logger.info(f"Foto de perfil para {telegram_id} guardada (Original + Thumb)")
        
        # 6. Actualizar en DB
        # Obtenemos info actual para no perder el nivel
        info = await get_user_info(telegram_id)
        level_id = info.get("level_id", 6) if info else 6
        level_name = info.get("level", "free") if info else "free"
        
        # Relative URL path (usamos el thumb por defecto en la lista para velocidad)
        relative_url = f"/api/profiles/{thumb_filename}"
        
        await user_repo.upsert(
            telegram_id=telegram_id,
            level=level_name,
            level_id=level_id,
            photo_url=relative_url
        )
        
        await user_cache.invalidate(f"user_effective:{telegram_id}")
        return relative_url
        
    except Exception as e:
        logger.error(f"Error sincronizando foto de perfil de {telegram_id}: {e}")
        return None
