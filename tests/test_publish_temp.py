import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import importlib.util
from pathlib import Path

# Fixture to mock dependencies cleanly
@pytest.fixture(autouse=True)
def mock_dependencies():
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
    # Ensure utils acts as a package
    modules_to_patch["utils"].__path__ = []
    # Add explicit submodules referenced
    modules_to_patch["utils.decorators"] = MagicMock()

    with patch.dict(sys.modules, modules_to_patch):
        yield

import importlib.util
from pathlib import Path

# Helper to load the module under test with current sys.modules
def load_callback_handlers():
    cb_path = Path(__file__).resolve().parents[1] / "handlers" / "callback_handlers.py"
    spec = importlib.util.spec_from_file_location("cb_real", str(cb_path))
    cb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cb)
    return cb


@pytest.mark.asyncio
async def test_set_publish_temp_stores_one_time_choice(monkeypatch):
    cb = load_callback_handlers()
    uid = 111

    # prepare a mutable state dict
    st = {}
    mock_state = MagicMock()
    mock_state.get_user_state.return_value = st
    monkeypatch.setattr(cb, "state_manager", mock_state)
    monkeypatch.setattr(sys.modules["services.user_service"], "get_effective_user", AsyncMock(return_value={"role": "free"}))

    # prepare update/context mocks
    update = MagicMock()
    query = MagicMock()
    query.data = "set_publish_temp|telegram"
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()
    update.callback_query = query
    update.effective_user.id = uid

    # ensure mostrar_colecciones is a coroutine so await works
    monkeypatch.setattr(cb, "mostrar_colecciones", AsyncMock())
    context = MagicMock()
    # Mock custom messages plugin
    mock_cms = MagicMock()
    mock_cms.enabled = True
    mock_cms.get_text = AsyncMock(return_value="Preferencia establecida")
    context.application.plugin_manager.get_plugin.return_value = mock_cms

    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()

    await cb.button_handler(update, context)

    assert st.get("publish_target_temp") == "telegram"


@pytest.mark.asyncio
async def test_publish_temp_consumed_on_lib_selection_calls_telegram(monkeypatch):
    cb = load_callback_handlers()
    uid = 222
    libro_key = "k1"
    update = MagicMock()
    update.message = MagicMock()
    update.message.edit_message_text = AsyncMock()
    update.message.edit_message_reply_markup = AsyncMock()
    update.message.delete = AsyncMock()
    query = MagicMock()
    query.data = f"lib|{libro_key}"
    query.message = MagicMock()
    query.message.message_id = 100
    query.message.edit_message_text = AsyncMock()
    query.message.edit_message_reply_markup = AsyncMock()
    query.message.delete = AsyncMock()
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.edit_message_reply_markup = AsyncMock()
    query.delete = AsyncMock()
    update.callback_query = query
    update.effective_user.id = uid
    update.effective_chat.id = uid
    libro = {"titulo": "Mi Libro", "portada": "http://x/cover.jpg", "descarga": "http://x/book.epub"}
    st = {
        "libros": {libro_key: libro},
        "publish_target_temp": "telegram",
        "chat_origen": uid,
        "url": "http://example.com/feed",
        "message_thread_id": None
    }

    mock_state = MagicMock()
    mock_state.get_user_state.return_value = st
    monkeypatch.setattr(cb, "state_manager", mock_state)
    monkeypatch.setattr(cb, "config", MagicMock(FACEBOOK_PUBLISHERS={uid}, ADMIN_USERS=set()))

    # Patch publicar_libro in the actual import path used by the handler
    import sys
    telegram_service_mod = sys.modules.get("services.telegram_service")
    if telegram_service_mod is None:
        from types import ModuleType
        telegram_service_mod = ModuleType("services.telegram_service")
        sys.modules["services.telegram_service"] = telegram_service_mod
    pub = AsyncMock()
    telegram_service_mod.publicar_libro = pub
    monkeypatch.setattr(cb, "publicar_libro", pub)
    monkeypatch.setattr(sys.modules["services.user_service"], "get_effective_user", AsyncMock(return_value={"role": "free"}))

    context = MagicMock()
    # Mock custom messages plugin
    mock_cms = MagicMock()
    mock_cms.enabled = True
    mock_cms.get_text = AsyncMock(return_value="Publicado con éxito")
    context.application.plugin_manager.get_plugin.return_value = mock_cms

    context.bot = MagicMock()
    context.bot.delete_message = AsyncMock()
    send_msg = MagicMock()
    send_msg.message_id = 101
    context.bot.send_message = AsyncMock(return_value=send_msg)

    await cb.button_handler(update, context)

    assert pub.called
    assert "publish_target_temp" not in st


@pytest.mark.asyncio
async def test_admin_publisher_set_publish_temp_fb_enters_evil(monkeypatch):
    cb = load_callback_handlers()
    uid = 444

    st = {}
    mock_state = MagicMock()
    mock_state.get_user_state.return_value = st
    monkeypatch.setattr(cb, "state_manager", mock_state)

    # user is admin and publisher
    monkeypatch.setattr(cb, "config", MagicMock(FACEBOOK_PUBLISHERS={uid}, ADMIN_USERS={uid}, OPDS_ROOT_EVIL="/opds-evil"))
    monkeypatch.setattr(sys.modules["services.user_service"], "get_effective_user", AsyncMock(return_value={"role": "staff", "custom_status": "Publicador"}))

    # intercept mostrar_colecciones
    mc = AsyncMock()
    monkeypatch.setattr(cb, "mostrar_colecciones", mc)

    update = MagicMock()
    query = MagicMock()
    query.data = "set_publish_temp|facebook"
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()
    update.callback_query = query
    update.effective_user.id = uid
    update.effective_chat.id = uid

    context = MagicMock()
    # Mock custom messages plugin
    mock_cms = MagicMock()
    mock_cms.enabled = True
    mock_cms.get_text = AsyncMock(return_value="Modo Evil")
    context.application.plugin_manager.get_plugin.return_value = mock_cms

    await cb.button_handler(update, context)

    # OPDS root should be switched to evil and mostrar_colecciones called
    assert st.get("opds_root") == "/opds-evil"
    assert st.get("destino") == uid
    assert mc.called


@pytest.mark.asyncio
async def test_start_publisher_does_not_show_collections_immediately(monkeypatch):
    uid = 666

    # Prepare /start handler test: ensure publishers only see the ephemeral
    # publish-choice and do NOT have mostrar_colecciones called immediately.
    import importlib, inspect
    ch_path = Path(__file__).resolve().parents[1] / "handlers" / "command_handlers.py"
    spec = importlib.util.spec_from_file_location("ch_mod", str(ch_path))
    ch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ch)

    # Patch state_manager, downloads_left and mostrar_colecciones
    st = {}
    mock_state = MagicMock()
    mock_state.get_user_state.return_value = st
    monkeypatch.setattr(ch, "state_manager", mock_state)
    # avoid downloads_left using core.state_manager/config inside ch
    mock_dl = AsyncMock(return_value="ilimitadas")
    monkeypatch.setattr(ch, "downloads_left", mock_dl)
    mc = AsyncMock()
    monkeypatch.setattr(ch, "mostrar_colecciones", mc)

    # config: user is publisher
    # Also patch get_effective_user because logic now checks role/custom_status
    monkeypatch.setattr(ch, "config", MagicMock(FACEBOOK_PUBLISHERS={uid}, ADMIN_USERS=set(), OPDS_ROOT_START="/opds-start"))

    import services.user_service
    mock_get_user = AsyncMock(return_value={"role": "staff", "custom_status": "Publicador"})
    # monkeypatch.setattr(services.user_service, "get_effective_user", mock_get_user) <-- This might be failing if services.user_service is not the one in sys.modules
    sys.modules["services.user_service"].get_effective_user = mock_get_user

    # update/context
    update = MagicMock()
    update.effective_user.id = uid
    update.effective_chat.id = uid
    update.effective_chat.type = 'private'
    update.message.reply_text = AsyncMock()  # Needed for donation link validation
    context = MagicMock()
    # Provide an async send_message for the fake bot used in the handler
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()

    # Mock custom messages plugin
    mock_cms = MagicMock()
    mock_cms.enabled = True
    mock_cms.get_text = AsyncMock(return_value="Bienvenido al bot")
    context.application.plugin_manager.get_plugin.return_value = mock_cms

    dummy_app = MagicMock()
    await ch.CommandHandlers(dummy_app).start(update, context)

    # mostrar_colecciones should NOT have been called (we deferred showing)
    assert not mc.called


@pytest.mark.asyncio
async def test_publish_temp_consumed_on_lib_selection_calls_facebook(monkeypatch):
    cb = load_callback_handlers()
    uid = 333
    libro_key = "k2"
    update = MagicMock()
    update.message = MagicMock()
    update.message.edit_message_text = AsyncMock()
    update.message.edit_message_reply_markup = AsyncMock()
    update.message.delete = AsyncMock()
    query = MagicMock()
    query.data = f"lib|{libro_key}"
    query.message = MagicMock()
    query.message.message_id = 100
    query.message.edit_message_text = AsyncMock()
    query.message.edit_message_reply_markup = AsyncMock()
    query.message.delete = AsyncMock()
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.edit_message_reply_markup = AsyncMock()
    query.delete = AsyncMock()
    update.callback_query = query
    update.effective_user.id = uid
    update.effective_chat.id = uid
    libro = {"titulo": "Libro 2", "portada": "http://x/cover2.jpg", "descarga": "http://x/book2.epub"}
    st = {
        "libros": {libro_key: libro},
        "publish_target_temp": "facebook",
        "chat_origen": uid,
        "url": "http://example.com/feed",
        "message_thread_id": None
    }

    mock_state = MagicMock()
    mock_state.get_user_state.return_value = st
    monkeypatch.setattr(cb, "state_manager", mock_state)
    monkeypatch.setattr(cb, "config", MagicMock(FACEBOOK_PUBLISHERS={uid}, ADMIN_USERS=set()))

    # Patch _publish_choice_facebook in the actual import path used by the handler
    import sys
    telegram_service_mod = sys.modules.get("services.telegram_service")
    if telegram_service_mod is None:
        from types import ModuleType
        telegram_service_mod = ModuleType("services.telegram_service")
        sys.modules["services.telegram_service"] = telegram_service_mod
    facebook = AsyncMock()
    telegram_service_mod._publish_choice_facebook = facebook
    monkeypatch.setattr(sys.modules["services.user_service"], "get_effective_user", AsyncMock(return_value={"role": "free"}))

    context = MagicMock()
    # Mock custom messages plugin
    mock_cms = MagicMock()
    mock_cms.enabled = True
    mock_cms.get_text = AsyncMock(return_value="Publicado con éxito")
    context.application.plugin_manager.get_plugin.return_value = mock_cms

    context.bot = MagicMock()
    context.bot.delete_message = AsyncMock()
    send_msg = MagicMock()
    send_msg.message_id = 101
    context.bot.send_message = AsyncMock(return_value=send_msg)

    await cb.button_handler(update, context)

    assert facebook.called
    assert "publish_target_temp" not in st


@pytest.mark.asyncio
async def test_descartar_fb_removes_buttons_not_message(monkeypatch):
    cb = load_callback_handlers()
    uid = 555
    st = {}
    mock_state = MagicMock()
    mock_state.get_user_state.return_value = st
    monkeypatch.setattr(cb, "state_manager", mock_state)

    update = MagicMock()
    query = MagicMock()
    query.data = "descartar_fb"
    # message.delete should NOT be called
    query.message.delete = AsyncMock()
    # instead we expect edit_message_reply_markup to be called
    query.edit_message_reply_markup = AsyncMock()
    query.answer = AsyncMock()
    query.message.text = "preview"
    update.callback_query = query
    update.effective_user.id = uid

    context = MagicMock()

    await cb.button_handler(update, context)

    assert query.edit_message_reply_markup.called
    assert not query.message.delete.called
