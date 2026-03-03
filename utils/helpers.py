"""
ZeePub Bot: Helpers Utility Module
This module acts as a facade for various specialized utilities.
Centralizes re-exports for backward-compatible imports across the project.
"""

# Re-exports for backward compatibility
from urllib.parse import urljoin

# --- identity_utils ---
from utils.identity_utils import generate_short_link  # noqa: F401

# --- metadata_utils ---
from utils.metadata_utils import (
    generar_slug_from_meta,  # noqa: F401
    parse_metadata_from_title,  # noqa: F401
    process_book_identity_comprehensive,  # noqa: F401
)

# --- string_utils ---
from utils.string_utils import (
    escapar_html,  # noqa: F401
    get_translator_acronym,  # noqa: F401
    limpiar_html_basico,  # noqa: F401
)

# --- system_utils ---
from utils.system_utils import (
    get_last_commit_message,  # noqa: F401
    get_version_string,  # noqa: F401
)

# --- telegram_utils ---
from utils.telegram_utils import (  # noqa: F401
    get_thread_id,
    is_command_for_bot,
)


# Legacy / Unused Proxies
def extract_creators_by_role(entry, role_code: str):
    return None


def extract_author(entry, is_folder=False):
    return "Desconocido"


def abs_url(base: str, href: str) -> str:
    return href if href.startswith("http") else urljoin(base, href)


def build_search_url(query: str, uid: int = None, role: str = None) -> str:
    return ""


def find_zeepubs_destino(feed, prefer_libraries: bool = False):
    return None


# Type aliases / compatibility
def parse_title_string(title_str: str):
    res = parse_metadata_from_title(title_str)
    return res["series"], res["volume"]


# Proxy to Hash Service
def generate_book_hash(**kwargs):
    from services.hash_service import hash_service

    return hash_service.generate_book_hash(**kwargs)


def generate_series_hash(**kwargs):
    from services.hash_service import hash_service

    return hash_service.generate_series_hash(**kwargs)


def validate_facebook_credentials(config_obj):
    missing = []
    token = config_obj.FACEBOOK_PAGE_ACCESS_TOKEN
    if not token or "your_token" in token or "token_falso" in token:
        missing.append("FACEBOOK_PAGE_ACCESS_TOKEN")
    group_id = config_obj.FACEBOOK_GROUP_ID
    if not group_id or "id_del_grupo" in group_id or "your_group_id" in group_id:
        missing.append("FACEBOOK_GROUP_ID")
    if missing:
        msg = (
            "⚠️ <b>Configuración inválida</b>\n\n"
            "No se puede publicar en Facebook porque las siguientes credenciales faltan o tienen valores por defecto (placeholders):\n"
            f"<code>{', '.join(missing)}</code>\n\n"
            "Por favor, ponte en contacto con un admin para que active el envío a Facebook."
        )
        return False, msg
    return True, ""
