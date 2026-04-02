import json
from typing import Any

from services.settings_service import get_setting


def load_global_ui_defaults() -> dict[str, Any]:
    global_raw = get_setting("ui_defaults_global", "{}")
    global_ui = json.loads(global_raw)

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
            "cardGlowIntensity": 0.5,
        }
    return global_ui


def normalize_ui(s: dict[str, Any]) -> dict[str, Any]:
    """Normaliza valores de opacidad y asegura que no haya Nones en campos críticos."""
    # 1. Opacity normalization (0-100 to 0.0-1.0)
    opacity_keys = [
        "navOpacity",
        "accentOpacity",
        "glassOpacity",
        "cardGlowIntensity",
    ]
    for k in opacity_keys:
        if k in s and isinstance(s[k], (int, float)):
            if s[k] > 1.1:
                s[k] = s[k] / 100.0
        elif k in s and s[k] is None:
            # Provide defaults if None
            defaults = {
                "navOpacity": 0.8,
                "accentOpacity": 0.2,
                "glassOpacity": 0.6,
                "cardGlowIntensity": 0.5,
            }
            s[k] = defaults.get(k)

        # 2. Key fallbacks for common visual properties
        if not s.get("theme"):
            s["theme"] = "dark"
        if not s.get("primaryColor"):
            s["primaryColor"] = "#3b82f6"
        if s.get("fontSize") is None:
            s["fontSize"] = 14
        if not s.get("backgroundColor"):
            s["backgroundColor"] = "#0f172a"
        if not s.get("cardColor"):
            s["cardColor"] = "#1e293b"

        return s


def merge_user_ui_settings(
    global_ui: dict[str, Any],
    level_settings: dict[str, Any],
    personal_settings: dict[str, Any],
    is_simulated: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """
    Merges global defaults, level/tier overrides, and personal settings to produce the final UI config.
    Returns (final_ui_dict, exported_settings_list).
    """
    final_ui = normalize_ui(global_ui.copy())

    if is_simulated:
        # En modo simulación priorizamos los ajustes del nivel para "ver" la identidad del rango
        level_settings_overlay = {
            "theme": level_settings.get("theme"),
            "fontSize": level_settings.get("fontSize"),
            "glassBlur": level_settings.get("glassBlur"),
            "coverWidth": level_settings.get("coverWidth"),
            "navOpacity": level_settings.get("navOpacity"),
            "accentOpacity": level_settings.get("accentOpacity"),
            "primaryColor": level_settings.get("primaryColor"),
            "showRecommendations": level_settings.get("showRecommendations"),
            "backgroundColor": level_settings.get("backgroundColor"),
            "cardColor": level_settings.get("cardColor"),
            "cardGlowIntensity": level_settings.get("cardGlowIntensity"),
            "panelTransparency": level_settings.get("glassOpacity") * 100 if level_settings.get("glassOpacity") else 60,
            "bannerContentOffset": level_settings.get("bannerContentOffset", 0),
        }
        # Remove None values
        level_settings_overlay = {k: v for k, v in level_settings_overlay.items() if v is not None}
        final_ui.update(level_settings_overlay)
        return normalize_ui(final_ui), []

    # Standard Merging
    override_keys = [
        "theme",
        "fontSize",
        "glassBlur",
        "coverWidth",
        "navOpacity",
        "accentOpacity",
        "primaryColor",
        "showRecommendations",
        "backgroundColor",
        "cardColor",
        "cardGlowIntensity",
        "bannerContentOffset",
        "glassOpacity",
    ]
    for k in override_keys:
        if k in level_settings and level_settings[k] is not None:
            final_ui[k] = level_settings[k]

    final_ui = normalize_ui(final_ui)

    # Exported Settings parsing
    exported_raw = level_settings.get("ui_exported_settings")
    try:
        exported_list = json.loads(exported_raw) if isinstance(exported_raw, str) else (exported_raw or [])
    except Exception:
        exported_list = []

    if not exported_list:
        # Fallback for old/empty tiers
        exported_list = ["theme", "primaryColor", "fontSize"]

    is_forced = level_settings.get("forceSettings", False)

    # Personal Settings Overrides
    for k, v in personal_settings.items():
        if v is None:
            continue
        if not is_forced:
            final_ui[k] = v
        elif k in exported_list:
            final_ui[k] = v

    return normalize_ui(final_ui), exported_list
