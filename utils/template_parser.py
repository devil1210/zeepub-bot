import re
from datetime import datetime
from typing import Any

from utils.template_registry_data import TEMPLATE_REGISTRY


async def get_extended_user_context(user) -> dict[str, Any]:
    """
    Calcula variables dinámicas del usuario (Nivel, Descargas, etc.)
    Solo se llama si el template las requiere.
    """
    from datetime import timedelta

    from config.config_settings import config
    from core.state_manager import state_manager
    from services.user_service import get_effective_user

    if not user:
        return {}

    uid = user.id
    user_data = await get_effective_user(uid)
    st = state_manager.get_user_state(uid)

    roles_display_map = {
        "admin": "Administrador",
        "staff": "STAFF",
        "premium": "Premium",
        "vip": "VIP",
        "white": "Patrocinador",
        "free": "Lector",
        "banned": "Baneado",
    }

    role_key = user_data.get("role", "free")
    expires_at = user_data.get("expires_at")

    if isinstance(role_key, str):
        role_key = role_key.strip().lower()

    nivel_display = roles_display_map.get(role_key, "Lector")

    if role_key in ("admin", "staff", "premium", "banned"):
        max_dl = None
    elif role_key == "vip":
        max_dl = config.VIP_DOWNLOADS_PER_DAY
    elif role_key == "white":
        max_dl = config.WHITELIST_DOWNLOADS_PER_DAY
    else:
        max_dl = config.MAX_DOWNLOADS_PER_DAY

    used = st.get("downloads_used", 0)

    if max_dl is None:
        if role_key == "banned":
            descargas_text = "⛔ Acceso denegado"
        else:
            descargas_text = "✅ Descargas ilimitadas"
    else:
        remaining = max_dl - used
        descargas_text = f"⚡️ Te quedan {remaining if remaining > 0 else 0} descargas por día"

    reset_time_str = None
    if max_dl is not None:
        now = datetime.now()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time_left = next_midnight - now
        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        reset_time_str = f"{hours}h {minutes}m"

    expire_str = None
    if expires_at:
        fmt = "%d/%m/%Y %H:%M" if role_key == "banned" else "%d/%m/%Y"
        expire_str = expires_at.strftime(fmt)

    rol_funcional = user_data.get("custom_status")
    apodo = user_data.get("nickname")

    return {
        "Nivel": nivel_display,
        "Rol": rol_funcional,
        "Apodo": apodo,
        "Descargas": descargas_text,
        "ResetTime": reset_time_str,
        "Expires": expire_str,
    }


async def render_template(
    slug: str,
    db_text: str = None,
    default_text: str = None,
    user=None,
    global_vars_cache: dict[str, str] = None,
    bot_info: dict = None,
    **replacements,
) -> str:
    """
    Parsea y renderiza la plantilla solicitada reemplazando variables.
    """
    final_text = db_text

    if not final_text:
        if default_text:
            final_text = default_text
        else:
            entry = TEMPLATE_REGISTRY.get(slug)
            if entry and "default" in entry:
                final_text = entry["default"]

    if not final_text:
        return ""

    vars_to_use = (global_vars_cache or {}).copy()

    now = datetime.now()
    vars_to_use["Fecha"] = now.strftime("%Y-%m-%d")
    vars_to_use["Hora"] = now.strftime("%H:%M")

    from utils.helpers import get_version_string

    vars_to_use["VersionBot"] = get_version_string()

    if bot_info:
        vars_to_use["BotNombre"] = bot_info.get("first_name", "Bot")
        vars_to_use["BotAlias"] = bot_info.get("username", "Bot")

    if user:
        vars_to_use["Nombre"] = user.mention_html() if hasattr(user, "mention_html") else (user.first_name or "Usuario")
        vars_to_use["Alias"] = getattr(user, "username", None) or ""
        vars_to_use["ID"] = str(getattr(user, "id", ""))

        needed_keys = {
            "[Nivel]",
            "[Descargas]",
            "[ResetTime]",
            "[Expires]",
            "[Rol]",
            "[Apodo]",
        }
        if any(k in final_text for k in needed_keys):
            extended_context = await get_extended_user_context(user)
            vars_to_use.update(extended_context)

    upd = replacements.get("update")
    if upd and hasattr(upd, "effective_chat") and upd.effective_chat:
        vars_to_use["ChatID"] = str(upd.effective_chat.id)
        vars_to_use["ChatTitulo"] = upd.effective_chat.title or "Chat Privado"

    vars_to_use.update(replacements)

    def replacer(match):
        key = match.group(1)
        content = match.group(2)
        val = vars_to_use.get(key)
        is_true = bool(val)
        if val == 0 or val == "0":
            is_true = True
        return content if is_true else ""

    final_text = re.sub(r"{{if\s+(\w+)}}(.*?){{endif}}", replacer, final_text, flags=re.DOTALL)

    for key, value in vars_to_use.items():
        placeholder = f"[{key}]"
        safe_value = str(value)
        final_text = final_text.replace(placeholder, safe_value)

    return final_text
