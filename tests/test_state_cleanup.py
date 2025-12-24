import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.fixture(autouse=True)
def mock_dependencies():
    """Patch dependencies in sys.modules ONLY for the duration of the test."""
    modules_to_patch = {
        "core": MagicMock(),
        "core.bot": MagicMock(),
        "core.state_manager": MagicMock(),
        "core.session_manager": MagicMock(),
        "services.opds_service": MagicMock(),
        "services.telegram_service": MagicMock(),
        "services": MagicMock(),
        "utils": MagicMock(),
        "utils.http_client": MagicMock(),
        "utils.helpers": MagicMock(),
        "utils.download_limiter": MagicMock(),
        "services.settings_service": MagicMock(),
        "config.config_settings": MagicMock(),
        "services.user_service": MagicMock(),
    }
    modules_to_patch["services.user_service"].get_effective_user = AsyncMock(return_value={"role": "free"})
    modules_to_patch["utils"].__path__ = []
    modules_to_patch["utils.decorators"] = MagicMock()

    with patch.dict(sys.modules, modules_to_patch):
        yield

import importlib.util
from pathlib import Path

def load_callback_handlers():
    cb_path = Path(__file__).resolve().parents[1] / "handlers" / "callback_handlers.py"
    spec = importlib.util.spec_from_file_location("cb_real_cleanup", str(cb_path))
    cb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cb)
    return cb

@pytest.mark.asyncio
async def test_state_cleanup_on_new_book(monkeypatch):
    cb = load_callback_handlers()
    uid = 123
    update = MagicMock()
    query = MagicMock()
    query.data = "lib|k1"
    query.message = MagicMock()
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    update.callback_query = query
    update.effective_user.id = uid
    update.effective_chat.id = uid
    st = {
        "epub_buffer": b"old",
        "meta_pendiente": {"foo": "bar"},
        "portada_pendiente": "old_url",
        "titulo_pendiente": "old_title",
        "fb_caption": "old_caption",
        "libros": {"k1": {"titulo": "Nuevo", "portada": "url", "descarga": "epub"}},
        "chat_origen": uid,
        "url": "http://example.com/feed",
        "message_thread_id": None
    }
    mock_state = MagicMock()
    mock_state.get_user_state.return_value = st
    monkeypatch.setattr(cb, "state_manager", mock_state)
    
    # Mock config
    mock_config = MagicMock()
    mock_config.FACEBOOK_PUBLISHERS = {uid}
    mock_config.ADMIN_USERS = set()
    monkeypatch.setattr(cb, "config", mock_config)
    
    pub = AsyncMock()
    # Mock telegram_service.publicar_libro
    with patch("services.telegram_service.publicar_libro", pub):
        monkeypatch.setattr(cb, "publicar_libro", pub)

        context = MagicMock()
        context.bot = MagicMock()
        context.bot.delete_message = AsyncMock()
        send_msg = MagicMock()
        send_msg.message_id = 101
        context.bot.send_message = AsyncMock(return_value=send_msg)

        await cb.button_handler(update, context)
        
        # All temp keys should be gone
        for k in ("epub_buffer", "meta_pendiente", "portada_pendiente", "titulo_pendiente", "fb_caption"):
            assert k not in st, f"Key '{k}' should have been cleaned up"
