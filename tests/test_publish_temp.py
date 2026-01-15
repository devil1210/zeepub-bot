import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture(autouse=True)
def mock_dependencies():
    """Patch dependencies in sys.modules ONLY for the duration of the test."""
    modules_to_patch = {
        "core": MagicMock(__path__=[]),
        "core.bot": MagicMock(),
        "core.state_manager": MagicMock(),
        "core.session_manager": MagicMock(),
        "services": MagicMock(__path__=[]),
        "utils": MagicMock(__path__=[]),
        "utils.http_client": MagicMock(),
        "utils.helpers": MagicMock(),
        "utils.download_limiter": MagicMock(),
        "services.settings_service": MagicMock(),
        "services.user_service": MagicMock(),
        "services.opds_service": MagicMock(),
        "services.telegram_service": MagicMock(),
        "services.topic_service": MagicMock(
            topic_service=MagicMock(ensure_topics=AsyncMock())
        ),
    }
    # Ensure they are AsyncMocks if awaited
    modules_to_patch["utils.download_limiter"].downloads_left = AsyncMock(
        return_value="ilimitadas"
    )
    modules_to_patch["services.user_service"].get_effective_user = AsyncMock(
        return_value={"role": "free"}
    )
    modules_to_patch["services.opds_service"].mostrar_colecciones = AsyncMock()
    modules_to_patch["services.telegram_service"].publicar_libro = AsyncMock()

    modules_to_patch["utils.decorators"] = MagicMock()

    with patch.dict(sys.modules, modules_to_patch):
        yield


import importlib.util
from pathlib import Path


def load_callback_handlers():
    cb_path = Path(__file__).resolve().parents[1] / "handlers" / "callback_handlers.py"
    spec = importlib.util.spec_from_file_location("cb_real", str(cb_path))
    cb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cb)
    return cb


def setup_mocks(update, context):
    context.bot.send_message = AsyncMock()
    context.bot.edit_message_text = AsyncMock()
    context.bot.delete_message = AsyncMock()
    if hasattr(update, "callback_query") and update.callback_query:
        update.callback_query.message.edit_message_text = AsyncMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()


@pytest.mark.asyncio
async def test_set_publish_temp_stores_one_time_choice(monkeypatch):
    cb = load_callback_handlers()
    uid = 111
    st = {}
    mock_state = MagicMock()
    mock_state.get_user_state.return_value = st
    monkeypatch.setattr(cb, "state_manager", mock_state)

    update = MagicMock()
    query = MagicMock()
    query.data = "set_publish_temp|telegram"
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()
    update.callback_query = query
    update.effective_user.id = uid

    context = MagicMock()
    setup_mocks(update, context)

    mock_cms = MagicMock()
    mock_cms.enabled = True
    mock_cms.get_text = AsyncMock(return_value="Preferencia establecida")
    context.application.plugin_manager.get_plugin.return_value = mock_cms

    monkeypatch.setattr(cb, "mostrar_colecciones", AsyncMock())

    with patch(
        "services.user_service.get_effective_user", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = {"role": "free"}
        await cb.button_handler(update, context)
        assert st.get("publish_target_temp") == "telegram"


@pytest.mark.asyncio
async def test_publish_temp_consumed_on_lib_selection_calls_telegram(monkeypatch):
    cb = load_callback_handlers()
    uid = 222
    libro_key = "k1"
    update = MagicMock()
    query = MagicMock()
    query.data = f"lib|{libro_key}"
    query.message = MagicMock()
    query.answer = AsyncMock()
    update.callback_query = query
    update.effective_user.id = uid
    libro = {
        "titulo": "Mi Libro",
        "portada": "http://x/cover.jpg",
        "descarga": "http://x/book.epub",
    }
    st = {
        "libros": {libro_key: libro},
        "publish_target_temp": "telegram",
        "chat_origen": uid,
        "url": "http://example.com/feed",
        "message_thread_id": None,
    }
    mock_state = MagicMock()
    mock_state.get_user_state.return_value = st
    monkeypatch.setattr(cb, "state_manager", mock_state)

    mock_config = MagicMock()
    mock_config.FACEBOOK_PUBLISHERS = {uid}
    mock_config.ADMIN_USERS = set()
    monkeypatch.setattr(cb, "config", mock_config)

    pub = AsyncMock()
    with patch("services.telegram_service.publicar_libro", pub):
        monkeypatch.setattr(cb, "publicar_libro", pub)
        context = MagicMock()
        setup_mocks(update, context)
        mock_cms = MagicMock()
        mock_cms.enabled = True
        mock_cms.get_text = AsyncMock(return_value="Publicado con éxito")
        context.application.plugin_manager.get_plugin.return_value = mock_cms

        with patch(
            "services.user_service.get_effective_user", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = {"role": "free"}
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

    mock_config = MagicMock()
    mock_config.FACEBOOK_PUBLISHERS = {uid}
    mock_config.ADMIN_USERS = {uid}
    mock_config.OPDS_ROOT_EVIL = "/opds-evil"
    monkeypatch.setattr(cb, "config", mock_config)

    mc = AsyncMock()
    monkeypatch.setattr(cb, "mostrar_colecciones", mc)

    update = MagicMock()
    query = MagicMock()
    query.data = "set_publish_temp|facebook"
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()
    update.callback_query = query
    update.effective_user.id = uid

    context = MagicMock()
    setup_mocks(update, context)
    mock_cms = MagicMock()
    mock_cms.enabled = True
    mock_cms.get_text = AsyncMock(return_value="Modo Evil")
    context.application.plugin_manager.get_plugin.return_value = mock_cms

    with patch(
        "services.user_service.get_effective_user", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = {"role": "staff", "custom_status": "Publicador"}
        await cb.button_handler(update, context)
        assert st.get("opds_root") == "/opds-evil"
        assert mc.called


@pytest.mark.asyncio
async def test_start_publisher_does_not_show_collections_immediately(monkeypatch):
    uid = 666
    ch_path = Path(__file__).resolve().parents[1] / "handlers" / "command_handlers.py"
    spec = importlib.util.spec_from_file_location("ch_real", str(ch_path))
    ch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ch)

    st = {}
    mock_state = MagicMock()
    mock_state.get_user_state.return_value = st
    monkeypatch.setattr(ch, "state_manager", mock_state)

    monkeypatch.setattr(ch, "downloads_left", AsyncMock(return_value="ilimitadas"))

    mc = AsyncMock()
    monkeypatch.setattr(ch, "mostrar_colecciones", mc)

    mock_config = MagicMock()
    mock_config.FACEBOOK_PUBLISHERS = {uid}
    mock_config.ADMIN_USERS = set()
    mock_config.OPDS_ROOT_START = "/opds-start"
    monkeypatch.setattr(ch, "config", mock_config)

    update = MagicMock()
    update.effective_user.id = uid
    update.effective_chat.type = "private"
    context = MagicMock()
    setup_mocks(update, context)
    mock_cms = MagicMock()
    mock_cms.enabled = True
    mock_cms.get_text = AsyncMock(return_value="Bienvenido")
    context.application.plugin_manager.get_plugin.return_value = mock_cms

    with patch(
        "services.user_service.get_effective_user", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = {"role": "staff", "custom_status": "Publicador"}
        await ch.CommandHandlers(MagicMock()).start(update, context)
        assert not mc.called
